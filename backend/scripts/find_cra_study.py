
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core import models

def find_cra_study():
    db = SessionLocal()
    try:
        # Check for John Doe
        cra = "John Doe"
        print(f"Looking for '{cra}'...")
        results = db.query(models.EDCMetrics.study_id).filter(models.EDCMetrics.responsible_lf == cra).distinct().all()
        
        if results:
            print(f"Found '{cra}' in these Studies:")
            for r in results:
                print(f"- {r[0]}")
        else:
            print(f"'{cra}' not found in any study.")

        # Check for Jane Smith
        cra = "Jane Smith"
        print(f"\nLooking for '{cra}'...")
        results = db.query(models.EDCMetrics.study_id).filter(models.EDCMetrics.responsible_lf == cra).distinct().all()
        
        if results:
            print(f"Found '{cra}' in these Studies:")
            for r in results:
                print(f"- {r[0]}")
        else:
            print(f"'{cra}' not found in any study.")

    finally:
        db.close()

if __name__ == "__main__":
    find_cra_study()
