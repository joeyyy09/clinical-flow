import sys
import os
import pandas as pd

# Add current directory to path
sys.path.append(os.getcwd())

from core.database import SessionLocal
from services.ingestion_service import IngestionService
from core import models

# Hardcoded path to the problematic file
target_file = r"c:\Users\megha\clinical-flow\data\QC Anonymized Study Files\Study 1_CPID_Input Files - Anonymization\Study 1_CPID_EDC_Metrics_URSV2.0_14 NOV 2025_updated.xlsx"

print(f"Testing ingestion for: {target_file}")
if not os.path.exists(target_file):
    print("❌ File does not exist!")
    # Search for it?
    base = r"c:\Users\megha\clinical-flow\data"
    for root, dirs, files in os.walk(base):
        for f in files:
            if "EDC_Metrics" in f:
                print(f"Found alternative: {os.path.join(root, f)}")
    exit()

try:
    # 1. Inspect Headers
    df = pd.read_excel(target_file)
    print("--- HEADERS (default) ---")
    print(list(df.columns)[:10]) # First 10
    
    # 2. Try Ingestion
    print("\n--- Running IngestionService.ingest_edc_metrics ---")
    db = SessionLocal()
    IngestionService.ingest_edc_metrics(db, target_file)
    db.commit() # explicit commit just in case
    db.close()
    
    # 3. Verify
    db = SessionLocal()
    # Use raw sql
    from sqlalchemy import text
    count = db.execute(text("SELECT count(*) FROM edc_metrics")).fetchone()[0]
    print(f"\n--- VERIFICATION ---")
    print(f"EDC Metrics Count in DB: {count}")
    db.close()
    
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"❌ Error: {e}")
