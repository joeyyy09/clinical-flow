
from sqlalchemy import create_engine, text
import os

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Assumes script is in backend/scripts/ or root?
# If running from root, db is likely in backend/clinical_trials.db or similar.
# Let's try to find the db path hardcoded for verification.
DB_PATH = "sqlite:///backend/clinical_trials.db"

try:
    engine = create_engine(DB_PATH)
    with engine.connect() as conn:
        print("--- Checking VisitProjection Table ---")
        result = conn.execute(text("SELECT count(*) FROM visit_projections WHERE days_outstanding > 0"))
        count = result.scalar()
        print(f"Overdue Visits Count: {count}")

        if count > 0:
            print("Top 5 Overdue:")
            rows = conn.execute(text("SELECT * FROM visit_projections WHERE days_outstanding > 0 ORDER BY days_outstanding DESC LIMIT 5"))
            for row in rows:
                print(row)
        else:
            print("No overdue visits found in DB.")

except Exception as e:
    print(f"Error checking DB: {e}")
