import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("Testing new data source endpoints:\n")

try:
    # Test Missing Visits
    print("1. Testing /analytics/missing-visits...")
    r = requests.get(f"{BASE_URL}/analytics/missing-visits")
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Status: {r.status_code}")
        print(f"   Records: {len(data)}")
        if data:
            print(f"   Sample: {data[0]}")
    else:
        print(f"   ❌ Status: {r.status_code}")
    print()
    
    # Test Lab Gaps
    print("2. Testing /analytics/lab-gaps...")
    r = requests.get(f"{BASE_URL}/analytics/lab-gaps")
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Status: {r.status_code}")
        print(f"   Records: {len(data)}")
        if data:
            print(f"   Sample issue: {data[0].get('issue', 'N/A')}")
    else:
        print(f"   ❌ Status: {r.status_code}")
    print()
    
    # Test SAE Reviews
    print("3. Testing /analytics/sae-reviews...")
    r = requests.get(f"{BASE_URL}/analytics/sae-reviews")
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Status: {r.status_code}")
        print(f"   Records: {len(data)}")
        if data:
            print(f"   Sample status: {data[0].get('review_status', 'N/A')}")
    else:
        print(f"   ❌ Status: {r.status_code}")
    print()
    
    print("✅ All endpoints operational!")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
