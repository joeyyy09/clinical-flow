
import os
import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

# Create tables
models.Base.metadata.create_all(bind=engine)

DATA_DIR = "/Users/harshithhh/Desktop/Nest-Assignment/data/QC Anonymized Study Files"

def get_study_id_from_filename(filename):
    # Simple heuristic: extract "Study XX"
    import re
    match = re.search(r"Study \d+", filename, re.IGNORECASE)
    if match:
        return match.group(0).upper().replace(" ", "_")
    return "UNKNOWN_STUDY"

def ingest_sae_metrics(db: Session, filepath: str):
    try:
        df = pd.read_excel(filepath)
        # Normalize columns
        df.columns = [c.strip() for c in df.columns]
        
        study_id = get_study_id_from_filename(filepath)
        
        for _, row in df.iterrows():
            item = models.SAEMetrics(
                study_id=study_id,
                country=str(row.get('Country', '')),
                site=str(row.get('Site', '')),
                patient_id=str(row.get('Patient ID', '')),
                review_status=str(row.get('Review Status', '')),
                action_status=str(row.get('Action Status', ''))
            )
            db.add(item)
        db.commit()
        print(f"Ingested SAE Metrics from {filepath}")
    except Exception as e:
        print(f"Error ingesting SAE Metrics {filepath}: {e}")

def ingest_missing_pages(db: Session, filepath: str):
    try:
        df = pd.read_excel(filepath)
        df.columns = [c.strip() for c in df.columns]
        study_id = get_study_id_from_filename(filepath)

        for _, row in df.iterrows():
            # Handle mixed types for missing days
            missing = row.get('No. #Days Page Missing', 0)
            try:
                missing = int(missing)
            except:
                missing = 0
                
            item = models.MissingPages(
                study_id=study_id,
                site_number=str(row.get('SiteNumber', '')),
                subject_name=str(row.get('SubjectName', '')),
                form_name=str(row.get('FormName', '')),
                visit_date=str(row.get('Visit date', '')),
                missing_days=missing
            )
            db.add(item)
        db.commit()
        print(f"Ingested Missing Pages from {filepath}")
    except Exception as e:
        print(f"Error ingesting Missing Pages {filepath}: {e}")

def ingest_edc_metrics(db: Session, filepath: str):
    try:
        df = pd.read_excel(filepath)
        df.columns = [c.strip() for c in df.columns]
        
        # EDC Metrics sometimes have different headers, need to be careful
        # Using a mapping based on my previous inspection might be fragile, so I'll be defensive
        
        for _, row in df.iterrows():
             # Fallback logic for column names based on inspection
            site = row.get('Site ID') or row.get('Site') or ''
            subj = row.get('Subject ID') or row.get('Subject') or ''
            status = row.get('Subject Status (Source: PRIMARY Form)') or row.get('Subject Status') or ''
            
            item = models.EDCMetrics(
                study_id=get_study_id_from_filename(filepath),
                site_id=str(site),
                subject_id=str(subj),
                subject_status=str(status),
                latest_visit=str(row.get('Latest Visit (SV) (Source: Rave EDC: BO4)', ''))
            )
            db.add(item)
        db.commit()
        print(f"Ingested EDC Metrics from {filepath}")
    except Exception as e:
        print(f"Error ingesting EDC Metrics {filepath}: {e}")

def run_ingestion():
    db = SessionLocal()
    # Recursive walk
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            full_path = os.path.join(root, file)
            if file.startswith("~$"): continue # Skip temp files
            
            if "SAE Dashboard" in file or "eSAE" in file:
                ingest_sae_metrics(db, full_path)
            elif "Global_Missing_Pages" in file:
                ingest_missing_pages(db, full_path)
            elif "EDC_Metrics" in file:
                ingest_edc_metrics(db, full_path)
            # Add more handlers as needed
            
    db.close()

if __name__ == "__main__":
    run_ingestion()
