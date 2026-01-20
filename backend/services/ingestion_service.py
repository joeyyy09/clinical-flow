
import os
import pandas as pd
import re
from sqlalchemy.orm import Session
from core.database import SessionLocal, engine
from core import models

class IngestionService:
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    RULES_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rules", "dataset")

    @staticmethod
    def get_study_id_from_filename(filename):
        match = re.search(r"Study \d+", filename, re.IGNORECASE)
        if match:
            return match.group(0).upper().replace(" ", "_")
        return "UNKNOWN_STUDY"

    @staticmethod
    def normalize_column(col_name):
        if not isinstance(col_name, str):
            return str(col_name)
        clean = re.sub(r'[^a-zA-Z0-9\s]', '', col_name)
        return clean.strip().lower().replace(' ', '_')

    @staticmethod
    def get_column_value(row, possible_names):
        row_map = {IngestionService.normalize_column(k): k for k in row.index}
        for name in possible_names:
            norm_name = IngestionService.normalize_column(name)
            if norm_name in row_map:
                val = row[row_map[norm_name]]
                return val if pd.notna(val) else ''
        return ''

    @staticmethod
    def ingest_sae_metrics(db: Session, filepath: str):
        try:
            df = pd.read_excel(filepath)
            study_id = IngestionService.get_study_id_from_filename(filepath)
            count = 0
            for _, row in df.iterrows():
                item = models.SAEMetrics(
                    study_id=study_id,
                    country=str(IngestionService.get_column_value(row, ['Country', 'Ctry'])),
                    site=str(IngestionService.get_column_value(row, ['Site', 'Site ID', 'Site Number'])),
                    patient_id=str(IngestionService.get_column_value(row, ['Patient ID', 'Subject', 'Subject ID'])),
                    review_status=str(IngestionService.get_column_value(row, ['Review Status', 'Status'])),
                    action_status=str(IngestionService.get_column_value(row, ['Action Status', 'Action']))
                )
                db.add(item)
                count += 1
            db.commit()
            print(f"✅ Ingested {count} SAE Metrics from {os.path.basename(filepath)}")
        except Exception as e:
            print(f"❌ Error ingesting SAE Metrics {os.path.basename(filepath)}: {e}")

    @staticmethod
    def ingest_missing_pages(db: Session, filepath: str):
        try:
            df = pd.read_excel(filepath)
            study_id = IngestionService.get_study_id_from_filename(filepath)
            count = 0
            for _, row in df.iterrows():
                missing_val = IngestionService.get_column_value(row, ['No. #Days Page Missing', 'Days Missing', 'Missing Days'])
                try: missing = int(missing_val)
                except: missing = 0
                    
                item = models.MissingPages(
                    study_id=study_id,
                    site_number=str(IngestionService.get_column_value(row, ['SiteNumber', 'Site', 'Site ID'])),
                    subject_name=str(IngestionService.get_column_value(row, ['SubjectName', 'Subject', 'Patient'])),
                    form_name=str(IngestionService.get_column_value(row, ['FormName', 'Form', 'Page Name'])),
                    visit_date=str(IngestionService.get_column_value(row, ['Visit date', 'Date', 'Visit'])),
                    missing_days=missing
                )
                db.add(item)
                count += 1
            db.commit()
            print(f"✅ Ingested {count} Missing Pages from {os.path.basename(filepath)}")
        except Exception as e:
            print(f"❌ Error ingesting Missing Pages {os.path.basename(filepath)}: {e}")

    @staticmethod
    def ingest_edc_metrics(db: Session, filepath: str):
        try:
            df = pd.read_excel(filepath)
            count = 0
            for _, row in df.iterrows():
                item = models.EDCMetrics(
                    study_id=IngestionService.get_study_id_from_filename(filepath),
                    site_id=str(IngestionService.get_column_value(row, ['Site ID', 'Site', 'SiteNumber'])),
                    subject_id=str(IngestionService.get_column_value(row, ['Subject ID', 'Subject', 'Patient ID'])),
                    subject_status=str(IngestionService.get_column_value(row, ['Subject Status (Source: PRIMARY Form)', 'Subject Status', 'Status'])),
                    latest_visit=str(IngestionService.get_column_value(row, ['Latest Visit (SV) (Source: Rave EDC: BO4)', 'Latest Visit', 'Visit']))
                )
                db.add(item)
                count += 1
            db.commit()
            print(f"✅ Ingested {count} EDC Metrics from {os.path.basename(filepath)}")
        except Exception as e:
            print(f"❌ Error ingesting EDC Metrics {os.path.basename(filepath)}: {e}")

    @staticmethod
    def run_full_pipeline():
        print(f"🚀 Starting full ingestion pipeline...")
        db = SessionLocal()
        scan_dirs = [IngestionService.DATA_DIR, IngestionService.RULES_DATA_DIR, os.path.join(os.getcwd(), "uploads")]
        
        for directory in scan_dirs:
            if not os.path.exists(directory): continue
            for root, dirs, files in os.walk(directory):
                for file in files:
                    full_path = os.path.join(root, file)
                    if file.startswith("~$") or file.startswith(".") or not file.endswith(('.xlsx', '.xls')): continue
                    
                    if "SAE Dashboard" in file or "eSAE" in file:
                        IngestionService.ingest_sae_metrics(db, full_path)
                    elif "Missing_Pages" in file:
                        IngestionService.ingest_missing_pages(db, full_path)
                    elif "EDC_Metrics" in file:
                        IngestionService.ingest_edc_metrics(db, full_path)
        db.close()
        print("✨ Ingestion Pipeline Complete")
