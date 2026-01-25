
import os
import pandas as pd
import re
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import SessionLocal, engine
from core import models

class IngestionService:
    # Go up 3 levels: backend/services/ingestion.py -> backend/services -> backend -> root
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    RULES_DATA_DIR = os.path.join(BASE_DIR, "rules", "dataset")

    """
    SECURITY COMPLIANCE NOTE:
    -------------------------
    This ingestion pipeline processes Clinical Trial Data.
    1. Anonymization: Input files in 'rules/dataset' are pre-anonymized (Upstream Process).
    2. PII Handling: Subject IDs are treated as pseudonymous identifiers.
    3. Audit Trail: All data interactions are logged via 'ingestion_logs'.
    """

    @staticmethod
    def get_study_id_from_filename(filename):
        # Matches "Study 1", "Study_1", "Study-1", "Study22"
        match = re.search(r"Study[ _-]*\d+", filename, re.IGNORECASE)
        if match:
            # Normalize to STUDY_1 format
            clean_id = re.sub(r"[ _-]", "_", match.group(0).upper())
            if "_" not in clean_id: # Handle Study22 -> STUDY_22
                clean_id = clean_id.replace("STUDY", "STUDY_")
            return clean_id
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
        """Ingest SAE Dashboard - handles both DM and Safety tabs"""
        try:
            study_id = IngestionService.get_study_id_from_filename(filepath)
            
            # Try both tab names
            tabs_to_try = ['SAE Dashboard_DM', 'SAE Dashboard_Safety', 0]  # 0 = first sheet
            count = 0
            
            for tab in tabs_to_try:
                try:
                    df = pd.read_excel(filepath, sheet_name=tab)
                    
                    for _, row in df.iterrows():
                        item = models.SAEMetrics(
                            study_id=study_id,
                            country=str(IngestionService.get_column_value(row, ['Country', 'Ctry'])),
                            site=str(IngestionService.get_column_value(row, ['Site', 'Site ID', 'Site Number'])),
                            patient_id=str(IngestionService.get_column_value(row, ['Patient ID', 'Subject', 'Subject ID'])),
                            review_status=str(IngestionService.get_column_value(row, ['Review Status', 'Status'])),
                            action_status=str(IngestionService.get_column_value(row, ['Action Status', 'Action'])),
                            # New review tracking fields
                            discrepancy_id=str(IngestionService.get_column_value(row, ['Discrepancy ID'])),
                            form_name=str(IngestionService.get_column_value(row, ['Form Name'])),
                            created_timestamp=str(IngestionService.get_column_value(row, ['Discrepancy Created Timestamp in Dashboard', 'Created Timestamp'])),
                            case_status=str(IngestionService.get_column_value(row, ['Case Status']))
                        )
                        db.add(item)
                        count += 1
                    print(f"  ✓ Processed tab: {tab}")
                except Exception as tab_error:
                    # Tab might not exist, try next one
                    continue
                    
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
                    missing_days=missing,
                    # New Fields
                    overall_status=str(IngestionService.get_column_value(row, ['Overall Subject Status'])),
                    visit_status=str(IngestionService.get_column_value(row, ['Visit Level Subject Status'])),
                    folder_name=str(IngestionService.get_column_value(row, ['FolderName', 'Folder'])),
                    form_type=str(IngestionService.get_column_value(row, ['Form Type (Summary or Visit)', 'Form Type']))
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
            # Read first few rows without header to inspect structure
            # We assume Row 0, 1, 2 are headers. Row 3 is metadata. Data starts later.
            df_raw = pd.read_excel(filepath, header=None)
            
            # Coalesce headers
            if len(df_raw) < 4:
                print(f"Skipping {os.path.basename(filepath)} - too few rows")
                return

            row0 = df_raw.iloc[0].tolist()
            row1 = df_raw.iloc[1].tolist()
            row2 = df_raw.iloc[2].tolist()
            
            new_columns = []
            for r0, r1, r2 in zip(row0, row1, row2):
                val0 = str(r0).strip() if pd.notna(r0) else ""
                val1 = str(r1).strip() if pd.notna(r1) else ""
                val2 = str(r2).strip() if pd.notna(r2) else ""
                
                # Priority: Row 2 > Row 1 > Row 0
                final_col = val2 if val2 else (val1 if val1 else val0)
                new_columns.append(final_col)
                
            df_raw.columns = new_columns
            
            # Drop the header rows (0, 1, 2, 3)
            # Row 3 is "Responsible LF" metadata row
            df = df_raw.iloc[4:]
            
            # Find the start of data. Look for 'Study' in 'Project Name' or similar.
            # Or just drop rows where 'Site ID' is NaN.
            # Normalizing column name to find 'Site ID'
            site_col = next((c for c in new_columns if IngestionService.normalize_column(c) in ['site_id', 'site', 'sitenumber']), None)
            
            if site_col:
                df = df[df[site_col].notna()]
                # Further filter: remove potential sub-header repeats or footer garbage
                df = df[df[site_col].astype(str).str.contains(r'\d', na=False)] 
            
            count = 0
            
            # Helper to safely get int
            def get_int(row, keys):
                val = IngestionService.get_column_value(row, keys)
                try: 
                    return int(float(val)) if pd.notna(val) and str(val).strip() != '' else 0
                except: 
                    return 0
            
            # Helper to safely get float
            def get_float(row, keys):
                val = IngestionService.get_column_value(row, keys)
                try: 
                    return float(val) if pd.notna(val) else 0.0
                except: 
                    return 0.0

            for _, row in df.iterrows():
                item = models.EDCMetrics(
                    study_id=IngestionService.get_study_id_from_filename(filepath),
                    project_name=str(IngestionService.get_column_value(row, ['Project Name', 'Project'])),
                    region=str(IngestionService.get_column_value(row, ['Region'])),
                    country=str(IngestionService.get_column_value(row, ['Country', 'Ctry'])),
                    site_id=str(IngestionService.get_column_value(row, ['Site ID', 'Site', 'Site Number'])),
                    subject_id=str(IngestionService.get_column_value(row, ['Subject ID', 'Subject', 'Patient ID'])),
                    latest_visit=str(IngestionService.get_column_value(row, ['Latest Visit (SV) (Source: Rave EDC: BO4)', 'Latest Visit'])),
                    subject_status=str(IngestionService.get_column_value(row, ['Subject Status (Source: PRIMARY Form)', 'Subject Status'])),
                    
                    # New Metrics
                    input_files=get_int(row, ['Input files', 'Input Files']),
                    cpmd=str(IngestionService.get_column_value(row, ['CPMD'])),
                    ssm=str(IngestionService.get_column_value(row, ['SSM'])),
                    missing_visits=get_int(row, ['Missing Visits']),
                    missing_pages=get_int(row, ['Missing Page', 'Missing Pages']),
                    coded_terms=get_int(row, ['# Coded terms', 'Coded terms']),
                    uncoded_terms=get_int(row, ['# Uncoded Terms', 'Uncoded Terms']),
                    open_issues_lnr=get_int(row, ['# Open issues in LNR', 'Open issues in LNR']),
                    open_issues_edrr=get_int(row, ['# Open Issues reported for 3rd party reconciliation in EDRR', 'Open Issues EDRR']),
                    inactivated_forms=get_int(row, ['Inactivated forms and folders']),
                    esae_review_dm=get_int(row, ['# eSAE dashboard review for DM']),
                    esae_review_safety=get_int(row, ['# eSAE dashboard review for safety']),
                    
                    # Statuses
                    visit_status=str(IngestionService.get_column_value(row, ['Visit status'])),
                    page_status=str(IngestionService.get_column_value(row, ['Page status (Source: (Rave EDC : BO4))', 'Page status'])),
                    queries_status=str(IngestionService.get_column_value(row, ['Queries status (Source:(Rave EDC : BO4))', 'Queries status'])),
                    page_action_status=str(IngestionService.get_column_value(row, ['Page Action Status (Source: (Rave EDC : BO4))', 'Page Action Status'])),
                    
                    # Compliance
                    protocol_deviations=get_int(row, ['Protocol Deviations (Source:(Rave EDC : BO4))', 'Protocol Deviations']),
                    pi_signatures=str(IngestionService.get_column_value(row, ['PI Signatures (Source: (Rave EDC : BO4))', 'PI Signatures'])),
                    expected_visits=get_int(row, ['# Expected Visits (Rave EDC : BO4)', 'Expected Visits']),
                    pages_entered=get_int(row, ['# Pages Entered', 'Pages Entered']),
                    pages_non_conformant=get_int(row, ['# Pages with Non-Conformant data']),
                    total_crfs_query_non_conformant=get_int(row, ['# Total CRFs with queries & Non-Conformant data']),
                    total_crfs_clean=get_int(row, ['# Total CRFs without queries & Non-Conformant data']),
                    clean_entered_crf_pct=get_float(row, ['% Clean Entered CRF']),
                    
                    # Query Breakdowns
                    dm_queries=get_int(row, ['# DM Queries']),
                    clinical_queries=get_int(row, ['# Clinical Queries']),
                    medical_queries=get_int(row, ['# Medical Queries']),
                    site_queries=get_int(row, ['# Site Queries']),
                    field_monitor_queries=get_int(row, ['# Field Monitor Queries']),
                    coding_queries=get_int(row, ['# Coding Queries']),
                    safety_queries=get_int(row, ['# Safety Queries']),
                    total_queries=get_int(row, ['#Total Queries', 'Total Queries']),
                    
                    # Verification & Lock
                    crfs_verified=get_int(row, ['# Forms Verified', 'Forms Verified']), # Note: Mapping "Forms Verified" to crfs_verified/forms_verified
                    forms_verified=get_int(row, ['# Forms Verified', 'Forms Verified']),
                    crfs_frozen=get_int(row, ['# CRFs Frozen']),
                    crfs_locked=get_int(row, ['# CRFs Locked']),
                    crfs_unlocked=get_int(row, ['# CRFs Unlocked']),
                    
                    # Signatures
                    crfs_signed=get_int(row, ['# CRFs Signed']),
                    crfs_overdue_45=get_int(row, ['CRFs overdue for signs within 45 days of Data entry']),
                    crfs_overdue_45_90=get_int(row, ['CRFs overdue for signs between 45 to 90 days of Data entry']),
                    crfs_overdue_90=get_int(row, ['CRFs overdue for signs beyond 90 days of Data entry']),
                    broken_signatures=get_int(row, ['Broken Signatures']),
                    never_signed=get_int(row, ['CRFs Never Signed']),
                    queries_resolved=get_int(row, ['# Queries Resolved', 'Queries Resolved', 'Resolved Queries']),
                    responsible_lf=str(IngestionService.get_column_value(row, ['Responsible LF for action']))
                )
                db.add(item)
                count += 1
            db.commit()
            print(f"✅ Ingested {count} EDC Metrics from {os.path.basename(filepath)}")
        except Exception as e:
            print(f"❌ Error ingesting EDC Metrics {os.path.basename(filepath)}: {e}")

    @staticmethod
    def ingest_visit_projections(db: Session, filepath: str):
        """Ingest Visit Projection Tracker (Missing Visits tab)"""
        try:
            df = pd.read_excel(filepath, sheet_name='Missing Visits')
            study_id = IngestionService.get_study_id_from_filename(filepath)
            count = 0
            
            for _, row in df.iterrows():
                # Helper to safely get int
                def get_int(keys):
                    val = IngestionService.get_column_value(row, keys)
                    try: 
                        return int(float(val)) if pd.notna(val) and str(val).strip() != '' else 0
                    except: 
                        return 0
                
                item = models.VisitProjection(
                    study_id=study_id,
                    country=str(IngestionService.get_column_value(row, ['Country'])),
                    site=str(IngestionService.get_column_value(row, ['Site', 'Site ID'])),
                    subject=str(IngestionService.get_column_value(row, ['Subject', 'Subject ID'])),
                    visit=str(IngestionService.get_column_value(row, ['Visit'])),
                    projected_date=str(IngestionService.get_column_value(row, ['Projected Date'])),
                    days_outstanding=get_int(['# Days Outstanding', 'Days Outstanding'])
                )
                db.add(item)
                count += 1
            db.commit()
            print(f"✅ Ingested {count} Visit Projections from {os.path.basename(filepath)}")
        except Exception as e:
            print(f"❌ Error ingesting Visit Projections {os.path.basename(filepath)}: {e}")

    @staticmethod
    def ingest_missing_lab_data(db: Session, filepath: str):
        """Ingest Missing Lab Names and Ranges"""
        try:
            df = pd.read_excel(filepath)
            study_id = IngestionService.get_study_id_from_filename(filepath)
            count = 0
            
            for _, row in df.iterrows():
                item = models.MissingLabData(
                    study_id=study_id,
                    country=str(IngestionService.get_column_value(row, ['Country'])),
                    site_number=str(IngestionService.get_column_value(row, ['Site number', 'Site'])),
                    subject=str(IngestionService.get_column_value(row, ['Subject', 'Subject ID'])),
                    visit=str(IngestionService.get_column_value(row, ['Visit'])),
                    form_name=str(IngestionService.get_column_value(row, ['Form Name'])),
                    lab_category=str(IngestionService.get_column_value(row, ['Lab category', 'Category'])),
                    lab_name=str(IngestionService.get_column_value(row, ['Lab Name'])),
                    lab_date=str(IngestionService.get_column_value(row, ['Lab Date'])),
                    test_name=str(IngestionService.get_column_value(row, ['Test Name'])),
                    test_description=str(IngestionService.get_column_value(row, ['Test description', 'Description'])),
                    issue=str(IngestionService.get_column_value(row, ['Issue'])),
                    comments=str(IngestionService.get_column_value(row, ['Comments']))
                )
                db.add(item)
                count += 1
            db.commit()
            print(f"✅ Ingested {count} Missing Lab Data records from {os.path.basename(filepath)}")
        except Exception as e:
            print(f"❌ Error ingesting Missing Lab Data {os.path.basename(filepath)}: {e}")

    @staticmethod
    def ingest_inactivated_forms(db: Session, filepath: str):
        try:
            df = pd.read_excel(filepath)
            study_id = IngestionService.get_study_id_from_filename(filepath)
            count = 0
            for _, row in df.iterrows():
                item = models.InactivatedForm(
                    study_id=study_id,
                    country=str(IngestionService.get_column_value(row, ['Country'])),
                    site=str(IngestionService.get_column_value(row, ['Site'])),
                    subject=str(IngestionService.get_column_value(row, ['Subject'])),
                    folder=str(IngestionService.get_column_value(row, ['Folder'])),
                    form=str(IngestionService.get_column_value(row, ['Form'])),
                    record_position=str(IngestionService.get_column_value(row, ['RecordPosition'])),
                    audit_action=str(IngestionService.get_column_value(row, ['Audit Action']))
                )
                db.add(item)
                count += 1
            db.commit()
            print(f"✅ Ingested {count} Inactivated Forms from {os.path.basename(filepath)}")
        except Exception as e:
            print(f"❌ Error ingesting Inactivated Forms {os.path.basename(filepath)}: {e}")

    @staticmethod
    def ingest_edrr_issues(db: Session, filepath: str):
        try:
            df = pd.read_excel(filepath)
            study_id = IngestionService.get_study_id_from_filename(filepath)
            count = 0
            for _, row in df.iterrows():
                issues = IngestionService.get_column_value(row, ['Total Open issue Count per subject', 'Open Issues'])
                try: count_val = int(issues)
                except: count_val = 0
                
                item = models.EDRRIssue(
                    study_id=study_id,
                    subject=str(IngestionService.get_column_value(row, ['Subject'])),
                    open_issue_count=count_val
                )
                db.add(item)
                count += 1
            db.commit()
            print(f"✅ Ingested {count} EDRR Issues from {os.path.basename(filepath)}")
        except Exception as e:
            print(f"❌ Error ingesting EDRR Issues {os.path.basename(filepath)}: {e}")

    @staticmethod
    def ingest_coding_reports(db: Session, filepath: str):
        """Handle both MedDRA and WHODrug reports"""
        try:
            df = pd.read_excel(filepath)
            study_id = IngestionService.get_study_id_from_filename(filepath)
            count_meddra = 0
            count_who = 0
            
            # Detect type based on columns
            cols = [c.lower() for c in df.columns]
            
            # Helper for MedDRA
            if any('meddra' in c for c in cols) or 'GlobalCodingReport_MedDRA' in filepath:
                for _, row in df.iterrows():
                    item = models.MedDRACoding(
                        study_id=study_id,
                        dictionary=str(IngestionService.get_column_value(row, ['Dictionary'])),
                        version=str(IngestionService.get_column_value(row, ['Dictionary Version number'])),
                        subject=str(IngestionService.get_column_value(row, ['Subject'])),
                        form=str(IngestionService.get_column_value(row, ['Form'])),
                        logline=str(IngestionService.get_column_value(row, ['Logline'])),
                        field_oid=str(IngestionService.get_column_value(row, ['Field OID'])),
                        supplement_term=str(IngestionService.get_column_value(row, ['Supplement Term Value1'])),
                        coding_status=str(IngestionService.get_column_value(row, ['Coding Status'])),
                        require_coding=str(IngestionService.get_column_value(row, ['Require Coding']))
                    )
                    db.add(item)
                    count_meddra += 1
                print(f"✅ Ingested {count_meddra} MedDRA records")

            # Helper for WHODrug
            elif any('whod' in c or 'trade name' in c for c in cols) or 'GlobalCodingReport_WHODD' in filepath:
                for _, row in df.iterrows():
                    item = models.WHODrugCoding(
                        study_id=study_id,
                        dictionary=str(IngestionService.get_column_value(row, ['Dictionary'])),
                        version=str(IngestionService.get_column_value(row, ['Dictionary Version number'])),
                        subject=str(IngestionService.get_column_value(row, ['Subject'])),
                        form=str(IngestionService.get_column_value(row, ['Form'])),
                        logline=str(IngestionService.get_column_value(row, ['Logline'])),
                        field_oid=str(IngestionService.get_column_value(row, ['Field OID'])),
                        trade_name=str(IngestionService.get_column_value(row, ['Trade Name'])),
                        coding_status=str(IngestionService.get_column_value(row, ['Coding Status'])),
                        require_coding=str(IngestionService.get_column_value(row, ['Require Coding']))
                    )
                    db.add(item)
                    count_who += 1
                print(f"✅ Ingested {count_who} WHODrug records")
            
            db.commit()
        except Exception as e:
            print(f"❌ Error ingesting Coding Report {os.path.basename(filepath)}: {e}")


    @staticmethod
    def ingest_cra_activity_logs(db: Session, filepath: str):
        """Ingest CRA Activity Logs"""
        try:
            df = pd.read_excel(filepath)
            # Assuming columns: CRA Name, Site ID, Action, Details, Timestamp
            count = 0
            for _, row in df.iterrows():
                # Handle potential timestamp formats
                ts_val = IngestionService.get_column_value(row, ['Timestamp', 'Date', 'Time'])
                try:
                    from dateutil import parser
                    timestamp = parser.parse(str(ts_val)) if ts_val else None
                except:
                    timestamp = None

                item = models.CRAActivityLog(
                    cra_name=str(IngestionService.get_column_value(row, ['CRA Name', 'CRA', 'Name'])),
                    site_id=str(IngestionService.get_column_value(row, ['Site ID', 'Site', 'Site Number'])),
                    action=str(IngestionService.get_column_value(row, ['Action', 'Type'])),
                    details=str(IngestionService.get_column_value(row, ['Details', 'Description', 'Notes'])),
                    timestamp=timestamp
                )
                db.add(item)
                count += 1
            db.commit()
            print(f"✅ Ingested {count} CRA Activity Logs from {os.path.basename(filepath)}")
        except Exception as e:
            print(f"❌ Error ingesting CRA Activity Logs {os.path.basename(filepath)}: {e}")

    @staticmethod
    def run_full_pipeline():
        print(f"🚀 Starting full ingestion pipeline...")
        db = SessionLocal()
        scan_dirs = [IngestionService.DATA_DIR, IngestionService.RULES_DATA_DIR, os.path.join(os.getcwd(), "uploads")]
        
        for directory in scan_dirs:
            if not os.path.exists(directory): 
                print(f"Directory not found: {directory}")
                continue
                
            print(f"📂 Scanning {directory}...")
            for root, dirs, files in os.walk(directory):
                for file in files:
                    full_path = os.path.join(root, file)
                    if file.startswith("~$") or file.startswith(".") or not file.endswith(('.xlsx', '.xls')): continue
                    
                    # Fuzzy matching for various file naming conventions
                    filename_lower = file.lower()
                    
                    try:
                        if "esae" in filename_lower or ("sae" in filename_lower and "dashboard" in filename_lower):
                            IngestionService.ingest_sae_metrics(db, full_path)
                        elif "missing" in filename_lower and "page" in filename_lower:
                            IngestionService.ingest_missing_pages(db, full_path)
                        elif "edc_metrics" in filename_lower or "edc metrics" in filename_lower:
                            IngestionService.ingest_edc_metrics(db, full_path)
                        elif "visit projection" in filename_lower or "visit_projection" in filename_lower:
                            IngestionService.ingest_visit_projections(db, full_path)
                        elif "missing" in filename_lower and "lab" in filename_lower:
                            IngestionService.ingest_missing_lab_data(db, full_path)
                        elif "inactivated" in filename_lower:
                            IngestionService.ingest_inactivated_forms(db, full_path)
                        elif "edrr" in filename_lower:
                            IngestionService.ingest_edrr_issues(db, full_path)
                        elif "coding" in filename_lower and ("meddra" in filename_lower or "whod" in filename_lower or "global" in filename_lower):
                            IngestionService.ingest_coding_reports(db, full_path)
                        elif "cra" in filename_lower and ("activity" in filename_lower or "log" in filename_lower):
                            IngestionService.ingest_cra_activity_logs(db, full_path)
                    except Exception as e:
                        print(f"⚠️ Failed to ingest {file}: {e}")
        
        IngestionService.calculate_derived_latencies(db)
        
        # 3. AI Enrichment Step
        print("🤖 Triggering AI Risk Models...")
        try:
            from services.ml_prediction_service import MLPredictionService
            # Force re-evaluation of all sites with new data
            MLPredictionService.predict_batch(None) 
            print("✅ AI Risk Scores Updated")
        except Exception as e:
            print(f"⚠️ AI Model Trigger Warning: {e}")

        db.close()
        print("✨ Ingestion Pipeline Complete")

    @staticmethod
    def calculate_derived_latencies(db: Session):
        print("⚡ Calculating Derived Query Latencies...")
        try:
            # Get Max Missing Days per Subject
            mp_results = db.query(models.MissingPages.subject_name, func.max(models.MissingPages.missing_days))\
                           .group_by(models.MissingPages.subject_name).all()
            latency_map = {r[0]: (r[1] or 0) for r in mp_results if r[0]}

            # Get Max Days Outstanding per Subject
            vp_results = db.query(models.VisitProjection.subject, func.max(models.VisitProjection.days_outstanding))\
                           .group_by(models.VisitProjection.subject).all()
            for r in vp_results:
                subj = r[0]
                if not subj: continue
                days = r[1] or 0
                if days > latency_map.get(subj, 0):
                    latency_map[subj] = days
            
            # Update EDCMetrics
            # Only if total_queries > 0 (Meaning they HAVE queries to be latent)
            subjects = db.query(models.EDCMetrics).filter(models.EDCMetrics.total_queries > 0).all()
            updated_count = 0
            for s in subjects:
                if s.subject_id in latency_map:
                    lat = latency_map[s.subject_id]
                    if lat > 0:
                        s.query_latency = lat
                        updated_count += 1
            db.commit()
            print(f"✅ Updated derived latency for {updated_count} subjects having open queries.")
        except Exception as e:
            print(f"⚠️ Latency derivation warning: {e}")

