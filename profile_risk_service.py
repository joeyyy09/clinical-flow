import time
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Fix imports to match backend structure
from backend.services.risk_monitor_service import RiskMonitorService
from backend.core.database import SessionLocal

def profile_service():
    print("Starting RiskMonitorService profiling...")
    
    db = SessionLocal()
    try:
        start_time = time.time()
        
        print("Executing get_detailed_risk_data...")
        results = RiskMonitorService.get_detailed_risk_data(db)
        
        end_time = time.time()
        print(f"Total execution time: {end_time - start_time:.4f}s")
        print(f"Number of sites returned: {len(results)}")
        
    except Exception as e:
        print(f"Error during profiling: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    profile_service()
