
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core import models
from sqlalchemy import func

def dump_issues():
    db = SessionLocal()
    try:
        print("Fetching Subject Issue Counts across ALL Studies...")
        print("-" * 60)
        print(f"{'Study':<15} | {'Subject':<15} | {'Total Open Issues'}")
        print("-" * 60)
        
        # We'll use EDCMetrics as the primary source as it aggregates Issue Counts
        # specifically looking for 'open_issues_edrr' or 'total_queries' based on user request.
        # The screenshot showed "Total Open issue Count per subject", which often refers to EDRR or Query counts.
        # We will sum them to be comprehensive or just show EDRR if that's what the screenshot implied.
        # Given "EDRR" context in previous prompts, let's prioritize EDRR but fallback/add queries.
        
        # Actually, let's look at EDRRIssue table which is specific to that report
        edrr_issues = db.query(models.EDRRIssue).all()
        
        if edrr_issues:
            # Sort by Study then Subject
            edrr_issues.sort(key=lambda x: (x.study_id or "", x.subject or ""))
            
            for issue in edrr_issues:
                print(f"{issue.study_id:<15} | {issue.subject:<15} | {issue.open_issue_count}")
        else:
            # Fallback to EDCMetrics if EDRR table is empty (maybe ingestion put it there)
            metrics = db.query(models.EDCMetrics).all()
            metrics.sort(key=lambda x: (x.study_id or "", x.subject_id or ""))
            
            for m in metrics:
                # Calculate a total "Open Issue" count
                count = (m.open_issues_edrr or 0) + (m.open_issues_lnr or 0)
                # If count is 0, maybe they meant queries? Let's just show EDRR count as per screenshot likely source
                if count > 0:
                     print(f"{m.study_id:<15} | {m.subject_id:<15} | {count}")

        print("-" * 60)
        print("End of Report")
        
    finally:
        db.close()

if __name__ == "__main__":
    dump_issues()
