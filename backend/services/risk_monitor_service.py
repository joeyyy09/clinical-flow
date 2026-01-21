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
        """Aggregates multi-source risk metrics for all sites based on URD requirements using Real Data."""
        # 1. Get all unique sites from EDCMetrics (Single Source of Truth)
        sites = db.query(models.EDCMetrics.site_id, models.EDCMetrics.study_id, models.EDCMetrics.country).distinct().all()
        
        results = []
        for site_row in sites:
            site_id = site_row.site_id
            study_id = site_row.study_id
            country = site_row.country or "Unknown"

            # Get all subjects for this site
            site_subjects = db.query(models.EDCMetrics).filter(models.EDCMetrics.site_id == site_id).all()
            subject_count = len(site_subjects)
            
            if subject_count == 0:
                continue

            # 2. Aggregate Metrics
            # Base metrics from EDCMetrics
            edc_missing = sum(s.missing_pages for s in site_subjects)
            edc_sae = sum(s.esae_review_dm + s.esae_review_safety for s in site_subjects)
            
            # Cross-reference with global tables (Legacy/Detail tables)
            # Normalize Site ID: "Site 14" -> "14", "014" -> "14"
            def normalize_site(s_id):
                return str(s_id).lower().replace('site', '').strip().lstrip('0')
                
            norm_id = normalize_site(site_id)
            
            # Fallback 1: Missing Pages Table
            # Query all sites and filter in python if needed, or query specifically
            # Note: MissingPages table has 'site_number' like "Site 14"
            # We assume site_number in MissingPages needs normalization to match EDCMetrics site_id
            # Optimization: could cache this mapping, but for now we query.
            # SQLite doesn't have great regex, so we fetch all missing pages sites and match in Py
            # BUT for performance, let's just try simple matches
            
            # Direct match or "Site {id}"
            missing_count_global = db.query(models.MissingPages).filter(
                (models.MissingPages.site_number == site_id) | 
                (models.MissingPages.site_number == f"Site {site_id}")
            ).count()
            
            # Fallback 2: SAE Metrics Table
            sae_count_global = db.query(models.SAEMetrics).filter(
                (models.SAEMetrics.site == site_id) | 
                (models.SAEMetrics.site == f"Site {site_id}")
            ).count()
            
            # Consolidate (Use Max to avoid under-reporting if one source is empty)
            missing_pages = max(edc_missing, missing_count_global)
            sae_count = max(edc_sae, sae_count_global)
            
            missing_visits = sum(s.missing_visits for s in site_subjects)
            total_queries = sum(s.total_queries for s in site_subjects)
            protocol_deviations = sum(s.protocol_deviations for s in site_subjects) 
            
            # 3. Derived Metrics (URD requirements)
            # DQI (Data Quality Index) - using the strict logic in AnalyticsService
            dqi = AnalyticsService.calculate_data_quality_index(db, site_id)
            
            # Clean Patient Rate
            clean_count = 0
            for s in site_subjects:
                if AnalyticsService.check_clean_patient_status(db, s.subject_id):
                    clean_count += 1
            
            clean_patient_rate = int((clean_count / subject_count) * 100)
            
            # Query Latency & Resolution
            # We don't have "latency days" in EDC metrics, but we have "Overdue" vs "Closed" in theory?
            # The current schema doesn't have "latency". We will use "Overdue Signatures" as a proxy for "slowness"
            # or just map "total_queries" for now.
            query_resolution_rate = 0 # Placeholder if we don't have 'closed_queries'
            # If we had 'answered_queries' vs 'total', we could calc rate.
            # Using 'crfs_locked' as a proxy for 'done'? No.
            # Let's mock resolution rate STRICTLY as 100 - (Open/Total * 100).
            # We have 'total_queries'. We assume open if not specified? 
            # In new schema we have breakdown but not explicit "Closed queries" count.
            # Let's use 0 as conservative if no data.
            
            # 4. Determine Risk level
            # Using DQI as primary driver per URD
            if dqi < 50:
                risk_level = "High"
            elif dqi < 80:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            # Override for critical safety
            if sae_count > 0 and dqi < 70:
                risk_level = "High"

            # 5. Milestone Readiness (% readiness for Lock/Submission)
            # Driven by Clean Patient Rate
            milestone_readiness = clean_patient_rate

            results.append({
                "site": site_id,
                "country": country,
                "study_id": study_id,
                "sae_count": sae_count,
                "missing_pages": missing_pages,
                "subject_count": subject_count,
                "query_latency": 0, # Not available in current raw data
                "query_resolution_rate": query_resolution_rate,
                "protocol_deviations": protocol_deviations,
                "clean_patient_rate": clean_patient_rate,
                "risk_level": risk_level,
                "predicted_risk": MLRiskService.predict_site_risk(missing_pages, sae_count, subject_count),
                "dqi": dqi,
                "milestone_readiness": milestone_readiness,
                "recommendation": RiskMonitorService.generate_recommendation(risk_level, missing_pages, sae_count, protocol_deviations)
            })
            
        # Sort by dqi (lowest first) to show riskier sites at top
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
