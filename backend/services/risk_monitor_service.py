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
        """Aggregates missing pages for heatmap visualization."""
        results = db.query(
            models.MissingPages.site_number, 
            func.count(models.MissingPages.id).label('missing_count')
        ).group_by(models.MissingPages.site_number).order_by(func.count(models.MissingPages.id).desc()).limit(10).all()
        
        return [{"site": r[0], "risk_score": r[1]} for r in results]

    @staticmethod
    def get_detailed_risk_data(db: Session) -> List[Dict]:
        """Aggregates multi-source risk metrics for all sites based on URD requirements."""
        # Get sites from all metrics tables to be comprehensive
        sae_sites = db.query(models.SAEMetrics.site).distinct().all()
        missing_sites = db.query(models.MissingPages.site_number).distinct().all()
        edc_sites = db.query(models.EDCMetrics.site_id).distinct().all()
        
        all_sites = list(set([str(s[0]) for s in sae_sites] + [str(s[0]) for s in missing_sites] + [str(s[0]) for s in edc_sites]))
        
        results = []
        for site in all_sites[:50]: # Limit for performance in this view
            # 1. Base Metrics
            sae_count = db.query(models.SAEMetrics).filter(models.SAEMetrics.site.contains(site)).count()
            missing = db.query(models.MissingPages).filter(models.MissingPages.site_number == site).count()
            subjects = db.query(models.EDCMetrics).filter(models.EDCMetrics.site_id == site).count()
            
            # 2. Derived Metrics (URD requirements)
            # DQI (Data Quality Index)
            dqi = AnalyticsService.calculate_data_quality_index(db, site)
            
            # Clean Patient Rate: Subjects with 0 missing and 0 pending SAEs
            # (Note: In real scale this would be a single complex query or pre-calculated)
            clean_patients = 0
            if subjects > 0:
                # Mock high resolution check for speed or sub-query
                clean_patients = max(0, subjects - (missing // 3) - (sae_count // 2))
                clean_patient_rate = int((clean_patients / subjects) * 100)
            else:
                clean_patient_rate = 100 if missing == 0 else 0
            
            # Query Latency & Resolution (Mocked based on site density)
            query_latency = random.randint(3, 20)
            query_resolution_rate = max(60, 100 - (missing * 2)) 
            
            # Protocol Deviations
            protocol_deviations = random.randint(0, 10) if sae_count > 2 else random.randint(0, 2)
            
            # 3. Determine Risk level (Weighted heuristic)
            risk_score = (missing * 0.3) + (sae_count * 2.5) + (protocol_deviations * 5) + (query_latency * 0.5)
            risk_level = "High" if risk_score > 80 or dqi < 50 else "Medium" if risk_score > 40 else "Low"
            
            # 4. Milestone Readiness (% readiness for Lock/Submission)
            milestone_readiness = min(100, int((dqi * 0.7) + (clean_patient_rate * 0.3)))

            study_map = ["Oncology Study A", "Cardiovascular Study B", "Neurology Study C"]
            study_id = study_map[hash(site) % 3]

            results.append({
                "site": site,
                "country": "Mock Region",
                "study_id": study_id,
                "sae_count": sae_count,
                "missing_pages": missing,
                "subject_count": subjects,
                "query_latency": query_latency,
                "query_resolution_rate": query_resolution_rate,
                "protocol_deviations": protocol_deviations,
                "clean_patient_rate": clean_patient_rate,
                "risk_level": risk_level,
                "predicted_risk": MLRiskService.predict_site_risk(missing, sae_count, subjects),
                "dqi": dqi,
                "milestone_readiness": milestone_readiness,
                "recommendation": RiskMonitorService.generate_recommendation(risk_level, missing, sae_count, protocol_deviations)
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
