
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, engine
from core import models
from sqlalchemy import text

def clean_db():
    print("🧹 Cleaning Mock Data (John Doe/Jane Smith) from Database...")
    db = SessionLocal()
    try:
        # 1. Update EDCMetrics
        mock_names = ["John Doe", "Jane Smith", "Robert Brown"]
        count = 0
        
        # We replace with "" (Empty String) or "Unassigned"
        # Empty string is safer if the UI handles it, but "Unassigned" is explicit
        # Let's use "Unassigned" so the user sees it clearly
        
        for name in mock_names:
            rows = db.query(models.EDCMetrics).filter(models.EDCMetrics.responsible_lf == name).all()
            for r in rows:
                r.responsible_lf = "Unassigned"
                count += 1
                
        # 2. Delete Fake Activity Logs
        deleted = db.query(models.CRAActivityLog).filter(models.CRAActivityLog.cra_name.in_(mock_names)).delete(synchronize_session=False)
        
        db.commit()
        print(f"✅ Updated {count} records in EDC Metrics to 'Unassigned'")
        print(f"✅ Deleted {deleted} fake Activity Logs")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clean_db()
