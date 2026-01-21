from sqlalchemy.orm import Session
from sqlalchemy import func
from core import models
from typing import List, Dict

class CRAService:
    @staticmethod
    def get_cra_performance_metrics(db: Session) -> List[Dict]:
        """
        Aggregates query performance metrics by CRA (responsible_lf).
        """
        results = db.query(
            models.EDCMetrics.responsible_lf,
            func.sum(models.EDCMetrics.total_queries).label('pending_queries'),
            func.sum(models.EDCMetrics.queries_resolved).label('resolved_queries'),
            func.avg(models.EDCMetrics.clean_entered_crf_pct).label('avg_dqi')
        ).filter(models.EDCMetrics.responsible_lf != None)\
         .filter(models.EDCMetrics.responsible_lf != "")\
         .group_by(models.EDCMetrics.responsible_lf).all()

        return [
            {
                "cra_name": r.responsible_lf,
                "pending_queries": int(r.pending_queries or 0),
                "resolved_queries": int(r.resolved_queries or 0),
                "avg_dqi": round(float(r.avg_dqi or 0), 1)
            } for r in results
        ]

    @staticmethod
    def get_cra_activity_logs(db: Session, limit: int = 10) -> List[Dict]:
        """
        Returns recent CRA activity logs.
        """
        logs = db.query(models.CRAActivityLog)\
                 .order_by(models.CRAActivityLog.timestamp.desc())\
                 .limit(limit).all()
        
        return [
            {
                "id": l.id,
                "cra_name": l.cra_name,
                "site_id": l.site_id,
                "action": l.action,
                "details": l.details,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None
            } for l in logs
        ]

    @staticmethod
    def get_underperforming_sites(db: Session) -> List[Dict]:
        """
        Identifies sites with high query counts or low DQI.
        """
        sites = db.query(
            models.EDCMetrics.site_id,
            models.EDCMetrics.responsible_lf,
            func.sum(models.EDCMetrics.total_queries).label('pending_queries'),
            func.avg(models.EDCMetrics.clean_entered_crf_pct).label('dqi')
        ).group_by(models.EDCMetrics.site_id, models.EDCMetrics.responsible_lf)\
         .order_by(func.sum(models.EDCMetrics.total_queries).desc())\
         .limit(10).all()
        
        return [
            {
                "site_id": s.site_id,
                "cra_name": s.responsible_lf,
                "pending_queries": int(s.pending_queries or 0),
                "dqi": round(float(s.dqi or 0), 1)
            } for s in sites if (s.pending_queries or 0) > 50 or (s.dqi or 100) < 70
        ]
