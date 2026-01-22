
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core import models
from sqlalchemy import text

def check_db():
    db = SessionLocal()
    try:
        print("--- Checking 'edc_metrics' table for 'responsible_lf' ---")
        # Get distinct values
        rows = db.query(models.EDCMetrics.responsible_lf).distinct().all()
        for r in rows:
            print(f"Found: '{r[0]}'")
            
        print("\n--- Checking 'cra_activity_logs' table for 'cra_name' ---")
        rows = db.query(models.CRAActivityLog.cra_name).distinct().all()
        for r in rows:
            print(f"Found: '{r[0]}'")

    finally:
        db.close()

if __name__ == "__main__":
    check_db()
