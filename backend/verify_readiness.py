
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_milestone_readiness():
    print("Testing Milestone Readiness endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/analytics/milestone-readiness")
        response.raise_for_status()
        data = response.json()
        
        print(f"Response: {json.dumps(data, indent=2)}")
        
        assert "total_subjects" in data
        assert "clean_patients" in data
        assert "readiness_score" in data
        assert "threshold" in data
        assert "is_ready" in data
        assert "status_color" in data
        
        assert isinstance(data["readiness_score"], int)
        assert 0 <= data["readiness_score"] <= 100
        assert isinstance(data["is_ready"], bool)
        
        print("Backend Verification: SUCCESS")
    except Exception as e:
        print(f"Backend Verification: FAILED - {e}")

if __name__ == "__main__":
    test_milestone_readiness()
