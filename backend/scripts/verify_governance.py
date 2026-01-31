import sys
import os
# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ingestion_service import IngestionService
from core.database import SessionLocal, engine, Base
from core import models
from sqlalchemy import func

def verify_governance():
    print("🧪 Starting Verification: Data Governance & Lineage")
    
    # 0. Ensure tables exist
    print("🔧 Ensuring DB tables exist...")
    Base.metadata.create_all(bind=engine)
    
    # 1. Trigger Pipeline
    print("\n▶️ Triggering Ingestion Pipeline...")
    IngestionService.run_full_pipeline(source="verification_script")
    
    db = SessionLocal()
    try:
        # 2. Verify IngestionRun
        print("\n🔍 Verifying IngestionRun In Records...")
        latest_run = db.query(models.IngestionRun).order_by(models.IngestionRun.id.desc()).first()
        
        if latest_run:
            print(f"   ✅ Found Run ID: {latest_run.id}")
            print(f"   Status: {latest_run.status}")
            print(f"   Source: {latest_run.source}")
            print(f"   Files Processed: {latest_run.files_processed}")
            
            if latest_run.status == "COMPLETED":
                print("   ✅ Run Status is COMPLETED")
            else:
                print(f"   ❌ Run Status is {latest_run.status} (Expected COMPLETED)")
        else:
            print("   ❌ No IngestionRun found!")
            return

        # 3. Verify RiskHistory
        print("\n🔍 Verifying RiskHistory Records...")
        history_count = db.query(models.RiskHistory).filter(models.RiskHistory.ingestion_run_id == latest_run.id).count()
        print(f"   ✅ Found {history_count} RiskHistory records linked to Run ID {latest_run.id}")
        
        if history_count > 0:
            sample = db.query(models.RiskHistory).filter(models.RiskHistory.ingestion_run_id == latest_run.id).first()
            print(f"   Sample Record: Site {sample.site_id} | Risk: {sample.risk_level} (Score: {sample.risk_score})")
        else:
            print("   ⚠️ No RiskHistory records created. Is there data in the system?")

    except Exception as e:
        print(f"❌ Verification Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_governance()
