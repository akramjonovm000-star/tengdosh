
import requests

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "student_id_730"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

endpoints = [
    ("/ai/history", "GET"),
    ("/market", "GET"),
    ("/student/activities", "GET")
]

print(f"Verifying enforcement for {TOKEN}...")

for path, method in endpoints:
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=HEADERS)
        else:
            resp = requests.post(url, headers=HEADERS)
        
        print(f"{method} {path} -> Status: {resp.status_code}, Body: {resp.text}")
    except Exception as e:
        print(f"Error checking {path}: {e}")
