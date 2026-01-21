import sys
import os
import datetime

# Add the backend directory to the path so we can import models and database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import SessionLocal, engine, Base
from core import models

def seed_cra_data():
    print("🌱 Seeding CRA Activity Logs and Performance data...")
    db = SessionLocal()
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # 1. Clear existing CRA Activity Logs (optional)
        db.query(models.CRAActivityLog).delete()
        
        # 2. Add sample Activity Logs
        logs = [
            models.CRAActivityLog(
                cra_name="John Doe", 
                site_id="SITE-001", 
                action="On-site Visit", 
                details="Completed source data verification for 5 subjects.",
                timestamp=datetime.datetime.now() - datetime.timedelta(hours=2)
            ),
            models.CRAActivityLog(
                cra_name="Jane Smith", 
                site_id="SITE-010", 
                action="Remote Review", 
                details="Resolved 15 queries related to vital signs.",
                timestamp=datetime.datetime.now() - datetime.timedelta(days=1)
            ),
            models.CRAActivityLog(
                cra_name="John Doe", 
                site_id="SITE-001", 
                action="Query Management", 
                details="Issued 3 new queries for missing lab reports.",
                timestamp=datetime.datetime.now() - datetime.timedelta(days=2)
            ),
            models.CRAActivityLog(
                cra_name="Robert Brown", 
                site_id="SITE-005", 
                action="Site Initiation", 
                details="Conducted SIV for new sub-investigator.",
                timestamp=datetime.datetime.now() - datetime.timedelta(days=3)
            )
        ]
        db.add_all(logs)
        
        # 3. Update some EDCMetrics to show performance
        # We need some existing metrics to update
        metrics = db.query(models.EDCMetrics).limit(5).all()
        if not metrics:
            print("⚠️ No EDCMetrics found in database. Seeding sample metrics...")
            sample_metrics = [
                models.EDCMetrics(
                    study_id="STUDY_001", project_name="Test Project", site_id="SITE-001", 
                    subject_id="SUB-001", responsible_lf="John Doe", total_queries=45, 
                    queries_resolved=120, clean_entered_crf_pct=85.0
                ),
                models.EDCMetrics(
                    study_id="STUDY_001", project_name="Test Project", site_id="SITE-010", 
                    subject_id="SUB-010", responsible_lf="Jane Smith", total_queries=12, 
                    queries_resolved=150, clean_entered_crf_pct=92.5
                ),
                models.EDCMetrics(
                    study_id="STUDY_001", project_name="Test Project", site_id="SITE-005", 
                    subject_id="SUB-005", responsible_lf="Robert Brown", total_queries=78, 
                    queries_resolved=40, clean_entered_crf_pct=65.0
                )
            ]
            db.add_all(sample_metrics)
        else:
            # Update existing ones with resolved queries
            for i, m in enumerate(metrics):
                if not m.responsible_lf:
                    m.responsible_lf = "John Doe" if i % 2 == 0 else "Jane Smith"
                m.queries_resolved = 100 + (i * 20)
                m.total_queries = 20 + (i * 10)
        
        db.commit()
        print("✅ Seeding complete.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_cra_data()
