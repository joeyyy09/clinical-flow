
import os
import pandas as pd
import re
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

# Create tables
models.Base.metadata.create_all(bind=engine)

# Dynamic path resolution: Go up one level from 'backend' to find 'data'
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def get_study_id_from_filename(filename):
    # Simple heuristic: extract "Study XX"
    match = re.search(r"Study \d+", filename, re.IGNORECASE)
    if match:
        return match.group(0).upper().replace(" ", "_")
    return "UNKNOWN_STUDY"

def normalize_column(col_name):
    """Normalize column name to lowercase, stripped, and alphanumeric only."""
    if not isinstance(col_name, str):
        return str(col_name)
    # Remove special chars and extra spaces
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', col_name)
    return clean.strip().lower().replace(' ', '_')

def get_column_value(row, possible_names):
    """Try to fetch value using a list of possible column names."""
    # Create a normalized map of the row's index
    row_map = {normalize_column(k): k for k in row.index}
    
    for name in possible_names:
        norm_name = normalize_column(name)
        if norm_name in row_map:
            val = row[row_map[norm_name]]
            return val if pd.notna(val) else ''
    return ''

def ingest_sae_metrics(db: Session, filepath: str):
    try:
        df = pd.read_excel(filepath)
        study_id = get_study_id_from_filename(filepath)
        
        count = 0
        for _, row in df.iterrows():
            item = models.SAEMetrics(
                study_id=study_id,
                country=str(get_column_value(row, ['Country', 'Ctry'])),
                site=str(get_column_value(row, ['Site', 'Site ID', 'Site Number'])),
                patient_id=str(get_column_value(row, ['Patient ID', 'Subject', 'Subject ID'])),
                review_status=str(get_column_value(row, ['Review Status', 'Status'])),
                action_status=str(get_column_value(row, ['Action Status', 'Action']))
            )
            db.add(item)
            count += 1
        db.commit()
        print(f"✅ Ingested {count} SAE Metrics from {os.path.basename(filepath)}")
    except Exception as e:
        print(f"❌ Error ingesting SAE Metrics {os.path.basename(filepath)}: {e}")

def ingest_missing_pages(db: Session, filepath: str):
    try:
        df = pd.read_excel(filepath)
        study_id = get_study_id_from_filename(filepath)

        count = 0
        for _, row in df.iterrows():
            # Handle mixed types for missing days
            missing_val = get_column_value(row, ['No. #Days Page Missing', 'Days Missing', 'Missing Days'])
            try:
                missing = int(missing_val)
            except:
                missing = 0
                
            item = models.MissingPages(
                study_id=study_id,
                site_number=str(get_column_value(row, ['SiteNumber', 'Site', 'Site ID'])),
                subject_name=str(get_column_value(row, ['SubjectName', 'Subject', 'Patient'])),
                form_name=str(get_column_value(row, ['FormName', 'Form', 'Page Name'])),
                visit_date=str(get_column_value(row, ['Visit date', 'Date', 'Visit'])),
                missing_days=missing
            )
            db.add(item)
            count += 1
        db.commit()
        print(f"✅ Ingested {count} Missing Pages from {os.path.basename(filepath)}")
    except Exception as e:
        print(f"❌ Error ingesting Missing Pages {os.path.basename(filepath)}: {e}")

def ingest_edc_metrics(db: Session, filepath: str):
    try:
        df = pd.read_excel(filepath)
        
        count = 0
        for _, row in df.iterrows():
            item = models.EDCMetrics(
                study_id=get_study_id_from_filename(filepath),
                site_id=str(get_column_value(row, ['Site ID', 'Site', 'SiteNumber'])),
                subject_id=str(get_column_value(row, ['Subject ID', 'Subject', 'Patient ID'])),
                subject_status=str(get_column_value(row, ['Subject Status (Source: PRIMARY Form)', 'Subject Status', 'Status'])),
                latest_visit=str(get_column_value(row, ['Latest Visit (SV) (Source: Rave EDC: BO4)', 'Latest Visit', 'Visit']))
            )
            db.add(item)
            count += 1
        db.commit()
        print(f"✅ Ingested {count} EDC Metrics from {os.path.basename(filepath)}")
    except Exception as e:
        print(f"❌ Error ingesting EDC Metrics {os.path.basename(filepath)}: {e}")

def run_ingestion():
    print(f"🚀 Starting ingestion from: {DATA_DIR}")
    if not os.path.exists(DATA_DIR):
        print(f"❌ DATA_DIR not found: {DATA_DIR}")
        return

    db = SessionLocal()
<<<<<<< HEAD
    
    # Define directories to scan
    scan_dirs = [DATA_DIR, os.path.join(os.getcwd(), "uploads")]
    
    for directory in scan_dirs:
        if not os.path.exists(directory):
            print(f"Directory not found, skipping: {directory}")
            continue
            
        print(f"Scanning directory: {directory}")
        # Recursive walk
        for root, dirs, files in os.walk(directory):
            for file in files:
                full_path = os.path.join(root, file)
                if file.startswith("~$") or file.startswith("."): continue # Skip temp/hidden files
                
                if "SAE Dashboard" in file or "eSAE" in file:
                    ingest_sae_metrics(db, full_path)
                elif "Global_Missing_Pages" in file:
                    ingest_missing_pages(db, full_path)
                elif "EDC_Metrics" in file:
                    ingest_edc_metrics(db, full_path)
                # Add more handlers as needed
=======
    # Recursive walk
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            full_path = os.path.join(root, file)
            if file.startswith("~$") or not file.endswith(('.xlsx', '.xls')): 
                continue 
            
            print(f"Processing: {file}...")
            if "SAE Dashboard" in file or "eSAE" in file:
                ingest_sae_metrics(db, full_path)
            elif "Global_Missing_Pages" in file:
                ingest_missing_pages(db, full_path)
            elif "EDC_Metrics" in file:
                ingest_edc_metrics(db, full_path)
            else:
                print(f"⚠️ Skipped unidentified file: {file}")
>>>>>>> 782bab7 (feat: Implement Scientific AI Agent with Gemini, fix ingestion, refine UI)
            
    db.close()
    print("✨ Ingestion Complete")

if __name__ == "__main__":
    run_ingestion()
