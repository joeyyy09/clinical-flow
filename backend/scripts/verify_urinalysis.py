
import sys
import os
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core import models

def verify_urinalysis():
    print("--- Verifying Urinalysis Data ---")
    db = SessionLocal()
    try:
        # 1. Search for "URINALYSIS" again just in case case-sensitivity was weird (ilike handles it but verify)
        count_urin = db.query(models.MissingLabData)\
            .filter(models.MissingLabData.test_name.ilike('%urin%'))\
            .count()
        print(f"Direct 'URINALYSIS' search count: {count_urin}")

        # 2. Check what IS in the database for 'Missing Lab name'
        print("\n--- Actual Top Test Names for 'Missing Lab name' ---")
        from sqlalchemy import func
        top_tests = db.query(models.MissingLabData.test_name, func.count(models.MissingLabData.id))\
            .filter(models.MissingLabData.issue.ilike('%Missing Lab name%'))\
            .group_by(models.MissingLabData.test_name)\
            .order_by(func.count(models.MissingLabData.id).desc())\
            .limit(10)\
            .all()
            
        for test, count in top_tests:
            print(f"Test: '{test}' | Count: {count}")
            
        # 3. Check specifically for 'UPHST' (Urine Ph/Specific Gravity?)
        print("\n--- Checking 'UPHST' ---")
        uphst = db.query(models.MissingLabData)\
            .filter(models.MissingLabData.test_name == 'UPHST')\
            .first()
        if uphst:
            print(f"Found UPHST! Example: {uphst.test_name} - {uphst.issue}")
            
    finally:
        db.close()

if __name__ == "__main__":
    verify_urinalysis()
