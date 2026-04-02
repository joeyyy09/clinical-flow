from sqlalchemy.orm import Session
from sqlalchemy import func
from core import models
import pandas as pd
import random
import time
from typing import List, Dict
from services.analytics_service import AnalyticsService
from services.ml_service_risk import MLRiskService

# --- Simple in-memory TTL cache ---
_cache: dict = {}
_CACHE_TTL = 120  # 2-minute cache (was 5 min — risk data should refresh more often)

def _get_cache(key: str):
    entry = _cache.get(key)
    if entry and (time.time() - entry['ts']) < _CACHE_TTL:
        return entry['data']
    return None

def _set_cache(key: str, data):
    _cache[key] = {'ts': time.time(), 'data': data}

def invalidate_cache():
    """Call this after ingestion to force a fresh risk calculation."""
    _cache.clear()

class RiskMonitorService:
    @staticmethod
    def get_risk_heatmap_data(db: Session) -> List[Dict]:
        """
        Aggregates site risk scores for heatmap visualization using fast aggregation.
        """
        cached = _get_cache('risk_heatmap')
        if cached is not None:
            return cached
            
        # Fast aggregation using SQL instead of per-site DQI calculation
        from sqlalchemy import func
        
        results_raw = db.query(
            models.EDCMetrics.site_id,
            func.sum(models.EDCMetrics.missing_pages + models.EDCMetrics.missing_visits + 
                    models.EDCMetrics.total_queries + models.EDCMetrics.protocol_deviations).label('risk_score')
        ).group_by(models.EDCMetrics.site_id)\
         .order_by(func.sum(models.EDCMetrics.missing_pages + models.EDCMetrics.missing_visits + 
                           models.EDCMetrics.total_queries + models.EDCMetrics.protocol_deviations).desc())\
         .limit(10)\
         .all()
        
        result = [{"site": r.site_id, "risk_score": int(r.risk_score or 0)} for r in results_raw]
        _set_cache('risk_heatmap', result)
        return result

    @staticmethod
    def get_detailed_risk_data(db: Session) -> List[Dict]:
        """Aggregates multi-source risk metrics for all sites using Optimized Batch Queries."""
        cached = _get_cache('risk_monitor')
        if cached is not None:
            return cached
            
        # Fast aggregation using Group By to avoid N+1 query problem
        from services.ml_service_risk import MLRiskService
        
        # 1. Fetch Aggregated EDCMetrics (Base)
        edc_stats = db.query(
            models.EDCMetrics.site_id,
            models.EDCMetrics.study_id,
            models.EDCMetrics.country,
            func.count(models.EDCMetrics.id).label('subject_count'),
            func.sum(models.EDCMetrics.missing_pages).label('sum_missing_pages'),
            func.sum(models.EDCMetrics.missing_visits).label('sum_missing_visits'),
            func.sum(models.EDCMetrics.total_queries).label('sum_queries'),
            func.sum(models.EDCMetrics.protocol_deviations).label('sum_deviations'),
            func.sum(models.EDCMetrics.esae_review_dm + models.EDCMetrics.esae_review_safety).label('sum_edc_sae'),
            func.sum(models.EDCMetrics.query_latency).label('sum_latency')
        ).group_by(models.EDCMetrics.site_id, models.EDCMetrics.study_id, models.EDCMetrics.country).all()
        
        if not edc_stats:
            return []

        # 2. Fetch Global Maps (Single Query per table)
        # Missing Pages
        g_miss_q = db.query(models.MissingPages.site_number, func.count(models.MissingPages.id)).group_by(models.MissingPages.site_number).all()
        g_miss_map = {r[0]: r[1] for r in g_miss_q}

        # SAEs (Total & Pending)
        g_sae_q = db.query(models.SAEMetrics.site, func.count(models.SAEMetrics.id)).group_by(models.SAEMetrics.site).all()
        g_sae_map = {r[0]: r[1] for r in g_sae_q}
        
        p_sae_q = db.query(models.SAEMetrics.site, func.count(models.SAEMetrics.id)).filter(models.SAEMetrics.review_status != 'Completed').group_by(models.SAEMetrics.site).all()
        p_sae_map = {r[0]: r[1] for r in p_sae_q}

        # Uncoded Coding — query coding tables directly (no cross-join, no leading-% LIKE)
        # Build subject→site_id map from edc_metrics first (one fast query)
        subj_site_q = db.query(models.EDCMetrics.subject_id, models.EDCMetrics.site_id).all()
        subj_to_site = {r[0]: r[1] for r in subj_site_q}

        # MedDRA uncoded subjects (suffix-anchored — index-friendly)
        med_q = db.query(models.MedDRACoding.subject, func.count(models.MedDRACoding.id))\
                  .filter(models.MedDRACoding.coding_status.ilike('uncoded%'))\
                  .group_by(models.MedDRACoding.subject).all()
        uncoded_map: dict = {}
        for subj, cnt in med_q:
            site = subj_to_site.get(subj)
            if site:
                uncoded_map[site] = uncoded_map.get(site, 0) + cnt

        # WHODrug uncoded subjects
        who_q = db.query(models.WHODrugCoding.subject, func.count(models.WHODrugCoding.id))\
                  .filter(models.WHODrugCoding.coding_status.ilike('uncoded%'))\
                  .group_by(models.WHODrugCoding.subject).all()
        for subj, cnt in who_q:
            site = subj_to_site.get(subj)
            if site:
                uncoded_map[site] = uncoded_map.get(site, 0) + cnt
            
        # 5. Fetch Site Action Status (Latest Comment Tag)
        # Fetch all comments ordered by date asc, so last one overwrites
        comments = db.query(models.SiteComment.site_number, models.SiteComment.tag)\
                     .order_by(models.SiteComment.created_at.asc()).all()
        action_map = {}
        for c in comments:
            action_map[c.site_number] = c.tag

        results = []
        batch_input = []
        
        for s in edc_stats:
            site_id = s.site_id
            
            # Lookup Logic
            keys = [site_id, f"Site {site_id}", str(site_id).lstrip('0')]
            if str(site_id).isdigit(): keys.append(str(int(site_id)))
            
            g_miss_val = 0
            g_sae_val = 0
            p_sae_val = 0
            for k in keys:
                g_miss_val += g_miss_map.get(k, 0)
                g_sae_val += g_sae_map.get(k, 0)
                p_sae_val += p_sae_map.get(k, 0)
            
            subject_count = s.subject_count or 1
            missing_pages = max(s.sum_missing_pages or 0, g_miss_val)
            sae_count = max(s.sum_edc_sae or 0, g_sae_val)
            
            # DQI Calc (Fast)
            sae_rate = p_sae_val / subject_count
            s_safety = max(0, 100 - (sae_rate * 100))
            
            missing_rate = ((missing_pages + (s.sum_missing_visits or 0)) / subject_count)
            s_missing = max(0, 100 - (missing_rate * 20))
            
            query_rate = (s.sum_queries or 0) / subject_count
            s_queries = max(0, 100 - (query_rate * 10))
            
            coding_rate = uncoded_map.get(site_id, 0) / subject_count
            s_coding = max(0, 100 - (coding_rate * 20))
            
            dqi = int((s_safety * 0.40) + (s_missing * 0.25) + (s_queries * 0.25) + (s_coding * 0.10))
            
            # Risk Level
            if dqi < 50: risk_level = "High"
            elif dqi < 80: risk_level = "Medium"
            else: risk_level = "Low"
            if sae_count > 0 and dqi < 70: risk_level = "High"
            
            # Heuristic Clean Patient Rate (to skip subject iteration)
            clean_patient_rate = int(max(0, 100 - ((missing_pages + (s.sum_queries or 0) * 0.5) / subject_count * 10)))

            # Resolve Action Status
            action_status = "No Action"
            for k in keys:
                if k in action_map: 
                    action_status = action_map[k]
                    break 
            
            # Prepare Batch Input
            batch_input.append({
                'missing_pages': missing_pages,
                'sae_count': sae_count,
                'subject_count': subject_count
            })

            res_obj = {
                "site": site_id,
                "study_id": s.study_id,
                "country": s.country or "Unknown",
                "sae_count": sae_count,
                "missing_pages": missing_pages,
                "subject_count": subject_count,
                "query_latency": int((s.sum_latency or 0) / subject_count),
                "protocol_deviations": s.sum_deviations or 0,
                "clean_patient_rate": clean_patient_rate,
                "risk_level": risk_level,
                "dqi": dqi,
                "milestone_readiness": clean_patient_rate
            }
            if action_status != "No Action":
                res_obj["action_status"] = action_status
                
            results.append(res_obj)
            
        # Execute Batch Prediction
        if batch_input:
            predictions = MLRiskService.predict_batch(batch_input)
            for i, result in enumerate(results):
                result['predicted_risk'] = predictions[i]
            
        results.sort(key=lambda x: x['dqi'])
        _set_cache('risk_monitor', results)
        return results


