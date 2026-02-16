import requests
import json
import base64

BASE_URL = "http://localhost:8000/api/v1"

# 1. Login with User-Agent A
UA_MOBILE = "TalabaHamkor/1.0 (Mobile)"
UA_HACKER = "curl/7.68.0"

print(f"🔹 1. Logging in with User-Agent: {UA_MOBILE}...")
login_payload = {
    "login": "demo", 
    "password": "123" # Needs ENABLE_DEMO_AUTH=1
}

# Ensure we hit the endpoint that returns a REAL JWT now
headers_mobile = {
    "User-Agent": UA_MOBILE,
    "Content-Type": "application/json"
}

try:
    resp = requests.post(f"{BASE_URL}/auth/hemis", json=login_payload, headers=headers_mobile)
    if resp.status_code == 200:
        data = resp.json()["data"]
        token = data["token"]
        print(f"✅ Login Success! Token: {token[:15]}...")
    else:
        print(f"❌ Login Failed: {resp.status_code} - {resp.text}")
        exit(1)
except Exception as e:
    print(f"❌ Connection Error: {e}")
    exit(1)

# 2. Access Protected Resource with SAME User-Agent (Should Succeed)
print(f"\n🔹 2. Accessing Protected Resource with CORRECT User-Agent...")
headers_mobile["Authorization"] = f"Bearer {token}"
resp = requests.get(f"{BASE_URL}/student/me", headers=headers_mobile)
if resp.status_code == 200:
    print(f"✅ Access Granted (200 OK)")
else:
    print(f"❌ Access Denied (Unexpected): {resp.status_code} - {resp.text}")

# 3. Access Protected Resource with DIFFERENT User-Agent (Should Fail)
print(f"\n🔹 3. Accessing Protected Resource with HACKER User-Agent ({UA_HACKER})...")
headers_hacker = {
    "User-Agent": UA_HACKER,
    "Authorization": f"Bearer {token}"
}
resp = requests.get(f"{BASE_URL}/student/me", headers=headers_hacker)

if resp.status_code == 401:
    print(f"✅ Access Denied (401 Unauthorized) - SECURITY WORKING!")
    print(f"   Server Response: {resp.json()['detail']}")
elif resp.status_code == 422:
    print(f"⚠️ Validation Error (422) - Might be due to other reasons.")
else:
    print(f"❌ Access Granted (Status: {resp.status_code}) - SECURITY FAILED!")
