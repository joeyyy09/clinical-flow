
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def verify_readiness():
    print("--- Verifying Readiness Checks ---")
    
    # 1. Check /analytics/readiness endpoint
    try:
        response = requests.get(f"{BASE_URL}/analytics/readiness")
        if response.status_code == 200:
            data = response.json()
            print(f"Readiness Data: {json.dumps(data, indent=2)}")
            
            # Validation
            fields = ["total_patients", "clean_patients", "readiness_score", "is_ready", "threshold"]
            for field in fields:
                if field in data:
                    print(f"✅ Field '{field}' present: {data[field]}")
                else:
                    print(f"❌ Field '{field}' MISSING!")
            
            # Logic check
            expected_ready = data["readiness_score"] >= data["threshold"]
            if data["is_ready"] == expected_ready:
                print(f"✅ Readiness logic consistent: {data['is_ready']}")
            else:
                print(f"❌ Readiness logic INCONSISTENT! Expected {expected_ready}, got {data['is_ready']}")
                
        else:
            print(f"❌ Endpoint /analytics/readiness failed with status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    verify_readiness()
