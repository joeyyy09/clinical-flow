from sqlalchemy.orm import Session
from sqlalchemy import func
from core import models
import pandas as pd
import random
from typing import List, Dict

class AnalyticsService:
    @staticmethod
    def calculate_study_health_score(db: Session, study_id: str = None) -> int:
        """
        Calculates study DQI (0-100) based on strict weights:
        - Safety (40%): Pending SAEs
        - Missing Data (25%): Missing Pages + Visits
        - Queries (25%): Total/Open Queries
        - Coding (10%): Uncoded Terms
        """
        from sqlalchemy import func
        
        # Aggregations
        metrics = db.query(
            func.sum(models.SAEMetrics.review_status != 'Completed').label('pending_saes'),
            func.count(models.SAEMetrics.id).label('total_saes')
        ).first()
        
        edc_metrics = db.query(
            func.sum(models.EDCMetrics.missing_pages).label('missing_pages'),
            func.sum(models.EDCMetrics.missing_visits).label('missing_visits'),
            func.sum(models.EDCMetrics.total_queries).label('total_queries'),
            func.count(models.EDCMetrics.id).label('total_subjects')
        ).first()
        
        coding_meddra = db.query(models.MedDRACoding).filter(models.MedDRACoding.coding_status.ilike('%uncoded%')).count()
        coding_who = db.query(models.WHODrugCoding).filter(models.WHODrugCoding.coding_status.ilike('%uncoded%')).count()
        
        if not edc_metrics or not edc_metrics.total_subjects:
            return 100

        n_subjects = edc_metrics.total_subjects
        
        # 1. Safety Score (40%) - Target: 0 Pending SAEs per patient
        # Penalty: -10 points per 0.1 pending SAE per patient
        pending_saes = metrics.pending_saes or 0
        sae_rate = pending_saes / n_subjects
        s_safety = max(0, 100 - (sae_rate * 100)) # Very strict: 1 pending SAE/patient = 0 score

        # 2. Missing Data Score (25%) - Target: 0 missing items
        missing_count = (edc_metrics.missing_pages or 0) + (edc_metrics.missing_visits or 0)
        missing_rate = missing_count / n_subjects
        s_missing = max(0, 100 - (missing_rate * 20)) # 5 missing items/patient = 0 score

        # 3. Query Score (25%) - Target: 0 queries
        query_count = edc_metrics.total_queries or 0
        query_rate = query_count / n_subjects
        s_queries = max(0, 100 - (query_rate * 10)) # 10 queries/patient = 0 score

        # 4. Coding Score (10%) - Target: 0 uncoded
        uncoded_count = coding_meddra + coding_who
        coding_rate = uncoded_count / n_subjects
        s_coding = max(0, 100 - (coding_rate * 20)) # 5 uncoded/patient = 0 score

        dqi = (s_safety * 0.40) + (s_missing * 0.25) + (s_queries * 0.25) + (s_coding * 0.10)
        return int(dqi)

    @staticmethod
    def get_sae_trend():
        return [
            {"month": "Jul", "sae_count": 120},
            {"month": "Aug", "sae_count": 145},
            {"month": "Sep", "sae_count": 132},
            {"month": "Oct", "sae_count": 160},
            {"month": "Nov", "sae_count": 185},
            {"month": "Dec", "sae_count": 210}
        ]

    # ... (skipping calculate_data_quality_index site-level update for brevity, but essentially same logic)

    @staticmethod
    def check_clean_patient_status(db: Session, subject_id: str) -> bool:
        """
        Clean Patient STRICT Definition:
        1. Missing visits = 0
        2. Missing pages = 0
        3. Open queries = 0
        4. Pending SAEs = 0
        5. Uncoded MedDRA terms = 0
        6. Uncoded WHO Drug terms = 0
        """
        # 1-3: Check EDC Metrics
        m = db.query(models.EDCMetrics).filter(models.EDCMetrics.subject_id == subject_id).first()
        if not m: return False
        
        if m.missing_visits > 0 or m.missing_pages > 0 or m.total_queries > 0:
            return False
            
        # 4: Check SAEs
        pending_saes = db.query(models.SAEMetrics).filter(
            models.SAEMetrics.patient_id == subject_id,
            models.SAEMetrics.review_status != 'Completed'
        ).count()
        if pending_saes > 0: return False
        
        # 5: Check MedDRA
        uncoded_meddra = db.query(models.MedDRACoding).filter(
            models.MedDRACoding.subject == subject_id,
            models.MedDRACoding.coding_status.ilike('%uncoded%')
        ).count()
        if uncoded_meddra > 0: return False
        
        # 6: Check WHODrug
        uncoded_who = db.query(models.WHODrugCoding).filter(
            models.WHODrugCoding.subject == subject_id,
            models.WHODrugCoding.coding_status.ilike('%uncoded%')
        ).count()
        if uncoded_who > 0: return False
        
        return True

