
import requests
import os

url = "http://127.0.0.1:8000/ingest/file"
file_path = "test_data.txt"

# Create a dummy file
with open(file_path, "w") as f:
    f.write("Dummy clinical data")

try:
    with open(file_path, "rb") as f:
        files = {"file": (file_path, f, "text/plain")}
        print(f"Sending request to {url}...")
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
finally:
    if os.path.exists(file_path):
        os.remove(file_path)
