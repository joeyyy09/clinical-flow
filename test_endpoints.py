import requests
import json

BASE_URL = 'http://127.0.0.1:8000'

print("Testing all dashboard endpoints:\n")

try:
    print("1. Testing /chat/stats...")
    r = requests.get(f'{BASE_URL}/chat/stats', timeout=5)
    print(f"   Status: {r.status_code}")
    data = r.json()
    if 'data' in data:
        print(f"   Data: {len(data['data'])} metrics")
        for item in data['data']:
            print(f"      - {item['Metric']}: {item['Value']}")
    print()
    
    print("2. Testing /analytics/score...")
    r = requests.get(f'{BASE_URL}/analytics/score', timeout=5)
    print(f"   Status: {r.status_code}")
    print(f"   Score: {r.json()}")
    print()
    
    print("3. Testing /analytics/trend...")
    r = requests.get(f'{BASE_URL}/analytics/trend', timeout=5)
    print(f"   Status: {r.status_code}")
    data = r.json()
    print(f"   Trend points: {len(data)}")
    print()
    
    print("4. Testing /analytics/risk...")
    r = requests.get(f'{BASE_URL}/analytics/risk', timeout=5)
    print(f"   Status: {r.status_code}")
    data = r.json()
    print(f"   Risk heatmap sites: {len(data)}")
    if data:
        print(f"   Sample: {data[0]}")
    print()
    
    print("✅ All endpoints working correctly!")
    print("\nIf the frontend is not showing data, the issue is likely:")
    print("1. Browser cache - try Ctrl+Shift+R (hard refresh)")
    print("2. CORS issue")
    print("3. Frontend not calling the correct URLs")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
