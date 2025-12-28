import requests
import os

# Create a dummy excel file (empty but valid path)
filename = "test_upload.xlsx"
with open(filename, "w") as f:
    f.write("dummy content")

url = "http://127.0.0.1:8000/ingest/file"
files = {'file': (filename, open(filename, 'rb'))}

try:
    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
finally:
    if os.path.exists(filename):
        os.remove(filename)
