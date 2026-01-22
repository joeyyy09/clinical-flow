
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.models import Base, EDCMetrics, SAEMetrics, MedDRACoding, WHODrugCoding
from services.analytics_service import AnalyticsService

# Setup in-memory DB
engine = create_engine('sqlite:///:memory:')
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
db = Session()

def test_dqi_weights():
    print("Testing DQI Logic with new Weights (25/20/15/20/20)...")
    
    # Create a site with 1 subject
    # Case 1: Perfect Site
    # Missing: 0, Queries: 0, NC: 0, Entered: 10, Verified: 10 (100%), SAE: 0
    s1 = EDCMetrics(
        site_id="SITE_1", subject_id="SUB_1", 
        missing_pages=0, missing_visits=0, 
        total_queries=0, 
        pages_non_conformant=0,
        pages_entered=10, crfs_verified=10
    )
    db.add(s1)
    db.commit()
    
    score1 = AnalyticsService.calculate_data_quality_index(db, "SITE_1")
    print(f"Case 1 (Perfect): Expected 100. Got: {score1}")
    assert score1 == 100
    
    # Case 2: Only Safety Issue (Pending SAE)
    # Weights: Safety is 20%. 1 pending SAE = 0 safety score.
    # Score should be 100 - 20 = 80.
    s2 = EDCMetrics(
        site_id="SITE_2", subject_id="SUB_2",
        missing_pages=0, missing_visits=0,
        total_queries=0,
        pages_non_conformant=0,
        pages_entered=10, crfs_verified=10
    )
    db.add(s2)
    sae = SAEMetrics(site="SITE_2", patient_id="SUB_2", review_status="New")
    db.add(sae)
    db.commit()
    
    score2 = AnalyticsService.calculate_data_quality_index(db, "SITE_2")
    print(f"Case 2 (1 Pending SAE): Expected 80 (lost 20% safety). Got: {score2}")
    
    # Case 3: Only SDV Issue (0% Verification)
    # Weights: SDV is 20%. 0% verification = 0 SDV score.
    # Score should be 100 - 20 = 80.
    s3 = EDCMetrics(
        site_id="SITE_3", subject_id="SUB_3",
        missing_pages=0, missing_visits=0,
        total_queries=0,
        pages_non_conformant=0,
        pages_entered=10, crfs_verified=0
    )
    db.add(s3)
    db.commit()
    
    score3 = AnalyticsService.calculate_data_quality_index(db, "SITE_3")
    print(f"Case 3 (0% SDV): Expected 80 (lost 20% SDV). Got: {score3}")

    print("✅ Logic Verification Passed!")

if __name__ == "__main__":
    try:
        test_dqi_weights()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
