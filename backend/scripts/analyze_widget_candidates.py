
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core import models
from sqlalchemy import func

def analyze_candidates():
    db = SessionLocal()
    try:
        print("--- Analyzing Data Candidates ---")
        
        # 1. Missing Lab Data
        lab_count = db.query(models.MissingLabData).count()
        print(f"\n1. Missing Lab Data Records: {lab_count}")
        if lab_count > 0:
            sample = db.query(models.MissingLabData).first()
            print(f"   Sample: Site={sample.site_number}, Test={sample.test_name}, Issue={sample.issue}")

        # 2. Protocol Deviations (Sum from EDCMetrics)
        dev_count = db.query(func.sum(models.EDCMetrics.protocol_deviations)).scalar() or 0
        print(f"\n2. Total Protocol Deviations: {dev_count}")
        
        # 3. Visit Projections (Overdue)
        overdue_visits = db.query(models.VisitProjection).filter(models.VisitProjection.days_outstanding > 0).count()
        print(f"\n3. Overdue Visits (>0 days): {overdue_visits}")
        if overdue_visits > 0:
             max_days = db.query(func.max(models.VisitProjection.days_outstanding)).scalar()
             print(f"   Max Days Outstanding: {max_days}")

    finally:
        db.close()

if __name__ == "__main__":
    analyze_candidates()
