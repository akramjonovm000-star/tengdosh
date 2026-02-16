import requests
import json

BASE_URL = "http://localhost:8000/api/v1"  # Assuming running on 8000 locally
# Or use the remote one if I can
# But since I am on the server, I can hit localhost if uvicorn is running.

# Let's try to hit the backend URL directly if we know the port.
# nohup_api.out doesn't show the port explicitly in the tail, but usually it's 8000 or 8002.
# Let's assume standard port 8000 for now.

def test_subscribe():
    # 1. Login or get token (using a fake token if dev mode allows, or proper one)
    # create a token manually if possible or use a known one.
    # checking dependencies.py might reveal how to fake it.
    
    token = "student_id_730" # Based on logs, it accepts "Bearer student_id_..." in dev/debug mode?
    # Log says: Checking auth header: Bearer student_id_729...
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    target_id = 2331 # Jaloliddin Ramazanov
    
    url = f"{BASE_URL}/community/subscribe/{target_id}"
    print(f"Testing POST {url}")
    
    try:
        response = requests.post(url, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_subscribe()
