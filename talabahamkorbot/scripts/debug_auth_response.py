import requests
import json

url = "http://localhost:8000/api/v1/auth/hemis"
payload = {
    "login": "nazokat",
    "password": "demo123"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
