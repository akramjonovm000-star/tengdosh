import httpx
import asyncio
import json

ADMIN_TOKEN = "LXjqwQE0Xemgq3E7LeB0tn2yMQWY0zXW"
BASE_URL = "https://student.jmcu.uz/rest/v1"

# Student Creds
STUDENT_LOGIN = "395251101411"
STUDENT_PASS = "OshiqAli2623"

async def probe():
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    client = httpx.AsyncClient(verify=False, headers=headers, timeout=30.0)
    
    print("[-] 1. Testing Admin Token with student_id param...")
    try:
        # Get a student
        resp = await client.get(f"{BASE_URL}/data/student-list", params={"limit": 1})
        if resp.status_code == 200:
            items = resp.json().get("data", {}).get("items", [])
            if items:
                sid = items[0].get("id")
                print(f"    Target Student ID: {sid} ({items[0].get('first_name')})")
                
                # Try /data/poll-list?student_id=...
                url = f"{BASE_URL}/data/poll-list"
                print(f"    Requesting {url}?student_id={sid} ...")
                r = await client.get(url, params={"student_id": sid})
                print(f"    Status: {r.status_code}")
                if r.status_code == 200:
                    data = r.json().get("data", {})
                    polls = data.get("items", [])
                    print(f"    Polls Found: {len(polls)}")
                    for p in polls:
                         print(f"    - {p}")
            else:
                 print("    [!] No students found to test with.")
    except Exception as e:
        print(f"    [!] Error: {e}")

    await client.aclose()

    print("\n[-] 2. Testing Student Login...")
    client_student = httpx.AsyncClient(verify=False, timeout=30.0)
    try:
        # Login
        login_url = f"{BASE_URL}/auth/login"
        print(f"    Logging in to {login_url}...")
        resp = await client_student.post(login_url, json={"login": STUDENT_LOGIN, "password": STUDENT_PASS})
        print(f"    Login Status: {resp.status_code}")
        
        if resp.status_code == 200:
            token_data = resp.json().get("data", {})
            token = token_data.get("token")
            print(f"    Got Token: {token[:10]}...")
            
            client_student.headers["Authorization"] = f"Bearer {token}"
            
            # Check Polls as Student
            endpoints = [
                "/education/poll-list",
                "/student/survey",
                "/poll/list"
            ]
            
            for ep in endpoints:
                 url = f"{BASE_URL}{ep}"
                 print(f"    Requesting {url}...")
                 r = await client_student.get(url)
                 print(f"    {ep}: {r.status_code}")
                 if r.status_code == 200:
                     print(f"    DATA: {r.json()}")

    except Exception as e:
        print(f"    [!] Student Login Error: {e}")

    await client_student.aclose()

if __name__ == "__main__":
    asyncio.run(probe())
