from sqlalchemy.orm import Session
from sqlalchemy import func
from core import models
import pandas as pd
import random
from typing import List, Dict
from services.analytics_service import AnalyticsService
from services.ml_service_risk import MLRiskService

class RiskMonitorService:
    @staticmethod
    def get_risk_heatmap_data(db: Session) -> List[Dict]:
        """
        Aggregates site risk scores for heatmap visualization using fast aggregation.
        """
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
        
        return [{"site": r.site_id, "risk_score": int(r.risk_score or 0)} for r in results_raw]

    @staticmethod
    def get_detailed_risk_data(db: Session) -> List[Dict]:
        """Aggregates multi-source risk metrics for all sites using Optimized Batch Queries."""
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

        # Uncoded Coding (Join)
        # MedDRA
        med_q = db.query(models.EDCMetrics.site_id, func.count(models.MedDRACoding.id))\
                  .join(models.MedDRACoding, models.EDCMetrics.subject_id == models.MedDRACoding.subject)\
                  .filter(models.MedDRACoding.coding_status.ilike('%uncoded%'))\
                  .group_by(models.EDCMetrics.site_id).all()
        uncoded_map = {r[0]: r[1] for r in med_q}
        
        # WHODrug
        who_q = db.query(models.EDCMetrics.site_id, func.count(models.WHODrugCoding.id))\
                  .join(models.WHODrugCoding, models.EDCMetrics.subject_id == models.WHODrugCoding.subject)\
                  .filter(models.WHODrugCoding.coding_status.ilike('%uncoded%'))\
                  .group_by(models.EDCMetrics.site_id).all()
        for r in who_q:
            uncoded_map[r[0]] = uncoded_map.get(r[0], 0) + r[1]
            
        # 5. Fetch Site Action Status (Latest Comment Tag)
        # Fetch all comments ordered by date asc, so last one overwrites
        comments = db.query(models.SiteComment.site_number, models.SiteComment.tag)\
                     .order_by(models.SiteComment.created_at.asc()).all()
        action_map = {}
        for c in comments:
            action_map[c.site_number] = c.tag

        results = []
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

            results.append({
                "site": site_id,
                "country": s.country,
                "study_id": s.study_id,
                "sae_count": sae_count,
                "missing_pages": missing_pages,
                "subject_count": subject_count,
                "query_latency": int((s.sum_latency or 0) / subject_count),
                "query_resolution_rate": 0,
                "protocol_deviations": s.sum_deviations or 0,
                "clean_patient_rate": clean_patient_rate,
                "risk_level": risk_level,
                "predicted_risk": MLRiskService.predict_site_risk(missing_pages, sae_count, subject_count),
                "dqi": dqi,
                "milestone_readiness": clean_patient_rate,
                "action_status": action_status,
                "recommendation": RiskMonitorService.generate_recommendation(risk_level, missing_pages, sae_count, s.sum_deviations or 0)
            })
            
        results.sort(key=lambda x: x['dqi'])
        return results

    @staticmethod
    def generate_recommendation(risk: str, missing: int, sae: int, deviations: int) -> str:
        """Generates AI-driven monitoring recommendations based on specific URD triggers."""
        if risk == "High":
            if deviations > 5: return "Investigative Audit: High Protocol Deviations detected."
            if missing > 50: return "Data Clean-up Drive: Significant backlog of missing pages."
            if sae > 10: return "Medical Monitoring: Urgent SAE review required."
            return "Enhanced Surveillance: Multiple high-risk indicators identified."
        elif risk == "Medium":
            if missing > 20: return "Targeted SDV: Focus on missing core CRF pages."
            return "Remote Monitoring: Review unreviewed SAEs and queries."
        else:
            return "Routine Surveillance: Site performance within nominal range."
