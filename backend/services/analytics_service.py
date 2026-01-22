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
        Calculates study DQI (0-100) based on Hackathon weights:
        - Missing Data (25%): Missing Pages + Visits
        - Open Queries (20%): Total Queries
        - Non-Conformant (15%): Total Pages with Non-Conformant Data
        - SDV/Form Status (20%): Verification Rate
        - Safety (20%): Pending SAEs
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
            func.sum(models.EDCMetrics.pages_non_conformant).label('non_conformant'),
            func.sum(models.EDCMetrics.crfs_verified).label('verified'),
            func.sum(models.EDCMetrics.pages_entered).label('entered'),
            func.count(models.EDCMetrics.id).label('total_subjects')
        ).first()
        
        if not edc_metrics or not edc_metrics.total_subjects:
            return 100

        n_subjects = edc_metrics.total_subjects
        
        # 1. Missing Data Score (25%)
        missing_count = (edc_metrics.missing_pages or 0) + (edc_metrics.missing_visits or 0)
        missing_rate = missing_count / n_subjects
        s_missing = max(0, 100 - (missing_rate * 20)) 

        # 2. Query Score (20%)
        query_count = edc_metrics.total_queries or 0
        query_rate = query_count / n_subjects
        s_queries = max(0, 100 - (query_rate * 10)) 

        # 3. Non-Conformant Data Score (15%)
        nc_count = edc_metrics.non_conformant or 0
        nc_rate = nc_count / n_subjects
        s_nc = max(0, 100 - (nc_rate * 20))

        # 4. SDV/Form Status Score (20%)
        entered = edc_metrics.entered or 0
        verified = edc_metrics.verified or 0
        if entered > 0:
            sdv_rate = (verified / entered) * 100
            s_sdv = sdv_rate 
        else:
            s_sdv = 100

        # 5. Safety Score (20%)
        pending_saes = metrics.pending_saes or 0
        sae_rate = pending_saes / n_subjects
        s_safety = max(0, 100 - (sae_rate * 100)) 

        dqi = (s_missing * 0.25) + (s_queries * 0.20) + (s_nc * 0.15) + (s_sdv * 0.20) + (s_safety * 0.20)
        return int(dqi)

    @staticmethod
    def get_sae_trend(db: Session = None):
        """
        Returns SAE count trends for the last 6 months based on real data.
        """
        from datetime import datetime, timedelta
        import calendar
        from dateutil import parser
        
        # Return empty structure if no DB
        if not db:
            return [
                {"month": "Jul", "sae_count": 0},
                {"month": "Aug", "sae_count": 0},
                {"month": "Sep", "sae_count": 0},
                {"month": "Oct", "sae_count": 0},
                {"month": "Nov", "sae_count": 0},
                {"month": "Dec", "sae_count": 0}
            ]

        # 1. Get raw timestamps
        results = db.query(models.SAEMetrics.created_timestamp).all()
        
        # 2. Process in Python (safer for SQLite string dates)
        timestamps = []
        for r in results:
            if r[0]:
                try:
                    # Handle various formats or ISO string
                    dt = parser.parse(r[0])
                    timestamps.append(dt)
                except:
                    continue
        
        if not timestamps:
             return [
                {"month": "Jul", "sae_count": 0},
                {"month": "Aug", "sae_count": 0},
                {"month": "Sep", "sae_count": 0},
                {"month": "Oct", "sae_count": 0},
                {"month": "Nov", "sae_count": 0},
                {"month": "Dec", "sae_count": 0}
            ]

        # 3. Aggregate last 6 months
        today = datetime.now()
        trend_data = []
        
        # Iterate backwards 5 months + current month
        for i in range(5, -1, -1):
            target_date = today - timedelta(days=i*30) # Approx month
            target_month = target_date.month
            target_year = target_date.year
            month_name = calendar.month_abbr[target_month]
            
            count = sum(
                1 for t in timestamps 
                if t.month == target_month and t.year == target_year
            )
            
            trend_data.append({"month": month_name, "sae_count": count})
            
        return trend_data

    @staticmethod
    def calculate_data_quality_index(db: Session, site_id: str) -> int:
        """
        Calculates DQI for a specific site based on Hackathon weights:
        - Missing Data (25%): Missing Pages + Visits
        - Open Queries (20%): Total Queries
        - Non-Conformant (15%): Pages with non-conformant data
        - SDV/Form Status (20%): Verification rate
        - Safety (20%): Pending SAEs
        """
        from sqlalchemy import func
        
        # Aggregations for this SITE
        metrics = db.query(
            func.sum(models.EDCMetrics.missing_pages).label('missing_pages'),
            func.sum(models.EDCMetrics.missing_visits).label('missing_visits'),
            func.sum(models.EDCMetrics.total_queries).label('total_queries'),
            func.sum(models.EDCMetrics.pages_non_conformant).label('non_conformant'),
            func.sum(models.EDCMetrics.crfs_verified).label('verified'),
            func.sum(models.EDCMetrics.pages_entered).label('entered'),
            func.count(models.EDCMetrics.id).label('total_subjects')
        ).filter(models.EDCMetrics.site_id == site_id).first()
        
        if not metrics or not metrics.total_subjects:
            return 100
            
        n_subjects = metrics.total_subjects
        
        # 1. Missing Data Score (25%)
        # Target: 0 missing items
        missing_count = (metrics.missing_pages or 0) + (metrics.missing_visits or 0)
        missing_rate = missing_count / n_subjects
        s_missing = max(0, 100 - (missing_rate * 20)) # Penalty: -20 per missing item/subject

        # 2. Open Query Score (20%)
        # Target: 0 queries
        query_count = metrics.total_queries or 0
        query_rate = query_count / n_subjects
        s_queries = max(0, 100 - (query_rate * 10)) # Penalty: -10 per query/subject
        
        # 3. Non-Conformant Data Score (15%)
        # Target: 0 non-conformant pages
        nc_count = metrics.non_conformant or 0
        nc_rate = nc_count / n_subjects
        s_nc = max(0, 100 - (nc_rate * 20)) # Penalty: -20 per NC page/subject
        
        # 4. SDV/Form Status Score (20%)
        # Target: 100% verification of entered pages
        entered = metrics.entered or 0
        verified = metrics.verified or 0
        if entered > 0:
            sdv_rate = (verified / entered) * 100
            s_sdv = sdv_rate # Direct percentage score
        else:
            s_sdv = 100 # No pages entered means nothing to verify

        # 5. Safety Score (20%)
        # Target: 0 pending SAEs
        pending_saes = db.query(models.SAEMetrics).filter(
            (models.SAEMetrics.site == site_id) | (models.SAEMetrics.site == f"Site {site_id}"),
            models.SAEMetrics.review_status != 'Completed'
        ).count()
        
        sae_rate = pending_saes / n_subjects
        s_safety = max(0, 100 - (sae_rate * 100)) # Strict: 1 pending SAE = 0 score

        # Weighted Sum
        dqi = (s_missing * 0.25) + (s_queries * 0.20) + (s_nc * 0.15) + (s_sdv * 0.20) + (s_safety * 0.20)
        return int(dqi)
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

    @staticmethod
    def calculate_study_readiness(db: Session, threshold: float = 95.0) -> Dict:
        """
        Calculates Study-level readiness score using Optimized SQL to avoid N+1.
        """
        # 1. Total unique subjects
        total_subjects = db.query(models.EDCMetrics.subject_id).distinct().count()
        
        if total_subjects == 0:
            return {
                "total_patients": 0,
                "clean_patients": 0,
                "readiness_score": 0,
                "is_ready": False,
                "threshold": threshold,
                "status_color": "rose"
            }

        # 2. Get subjects who ARE NOT clean
        # We only care about subjects that are in EDCMetrics (active subjects)
        active_subjects = db.query(models.EDCMetrics.subject_id).distinct()
        
        # Dirty filters
        dirty_sae = db.query(models.SAEMetrics.patient_id).filter(
            models.SAEMetrics.review_status != 'Completed',
            models.SAEMetrics.patient_id.in_(active_subjects)
        )
        
        dirty_meddra = db.query(models.MedDRACoding.subject).filter(
            models.MedDRACoding.coding_status.ilike('%uncoded%'),
            models.MedDRACoding.subject.in_(active_subjects)
        )
        
        dirty_who = db.query(models.WHODrugCoding.subject).filter(
            models.WHODrugCoding.coding_status.ilike('%uncoded%'),
            models.WHODrugCoding.subject.in_(active_subjects)
        )
        
        dirty_edc = db.query(models.EDCMetrics.subject_id).filter(
            (models.EDCMetrics.missing_visits > 0) | 
            (models.EDCMetrics.missing_pages > 0) | 
            (models.EDCMetrics.total_queries > 0)
        )
        
        # Combine (Union) all dirty subject IDs - Union already handles distinctness
        dirty_subjects_union = dirty_sae.union(dirty_meddra, dirty_who, dirty_edc)
        dirty_count = db.query(dirty_subjects_union.subquery()).count()
        
        # Clean count is total minus dirty
        clean_count = max(0, total_subjects - dirty_count)
        readiness_score = round((clean_count / total_subjects) * 100, 1)
        is_ready = readiness_score >= threshold
        
        return {
            "total_patients": total_subjects,
            "clean_patients": clean_count,
            "readiness_score": readiness_score,
            "is_ready": is_ready,
            "threshold": threshold,
            "status_color": "emerald" if is_ready else "amber" if readiness_score > 80 else "rose"
        }

