from sqlalchemy.orm import Session
from sqlalchemy import func
from core import models
import pandas as pd
import random
from typing import List, Dict

class AnalyticsService:
    @staticmethod
    def calculate_study_health_score(db: Session, study_id: str = None) -> int:
        """Calculates a heuristic health score (0-100) for a study."""
        query_sae = db.query(models.SAEMetrics)
        query_missing = db.query(models.MissingPages)
        
        if study_id:
            query_sae = query_sae.filter(models.SAEMetrics.study_id == study_id)
            query_missing = query_missing.filter(models.MissingPages.study_id == study_id)

        df_sae = pd.read_sql(query_sae.statement, db.bind)
        df_missing = pd.read_sql(query_missing.statement, db.bind)
        
        if not df_sae.empty:
            total_saes = len(df_sae)
            pending = len(df_sae[df_sae['review_status'] != 'Reviewed'])
            sae_score = max(0, 100 - (pending / total_saes * 50))
        else:
            sae_score = 100

        if not df_missing.empty:
            total_missing = len(df_missing)
            missing_density = total_missing / 100 
            missing_score = max(0, 100 - (missing_density * 2))
        else:
            missing_score = 100
            
        return int((sae_score * 0.4) + (missing_score * 0.6))

    @staticmethod
    def calculate_data_quality_index(db: Session, site_number: str) -> int:
        """Calculates a Data Quality Index (DQI) for a specific site."""
        missing_count = db.query(models.MissingPages).filter(models.MissingPages.site_number == site_number).count()
        missing_score = max(0, 100 - (missing_count * 10))
        
        latency = random.randint(1, 10) 
        latency_score = max(0, 100 - (latency * 5))
        
        sae_total = db.query(models.SAEMetrics).filter(models.SAEMetrics.site.contains(site_number)).count()
        if sae_total == 0:
            sae_score = 100
        else:
            pending = db.query(models.SAEMetrics).filter(models.SAEMetrics.site.contains(site_number), models.SAEMetrics.review_status != 'Reviewed').count()
            sae_score = int(((sae_total - pending) / sae_total) * 100)
        
        return int((missing_score * 0.4) + (latency_score * 0.3) + (sae_score * 0.3))

    @staticmethod
    def get_sae_trend() -> List[Dict]:
        """Returns mock SAE trend data."""
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        values = [12, 19, 3, 5, 2, 30]
        return [{"month": m, "sae_count": v} for m, v in zip(months, values)]
