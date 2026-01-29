import asyncio
import httpx
import json

# Credentials from user's previous message
LOGIN = "395251101411"
PASSWORD = "6161234a"
BASE_URL = "https://student.jmcu.uz/rest/v1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

async def probe():
    async with httpx.AsyncClient(verify=False) as client:
        # 1. Login
        print("Logging in...")
        resp = await client.post(
            f"{BASE_URL}/auth/login",
            json={"login": int(LOGIN), "password": PASSWORD},
            headers=HEADERS
        )
        data = resp.json()
        if not data.get("success"):
            print("Login failed:", data)
            return
            
        token = data['data']['token']
        print("Token obtained.")
        
        auth_headers = HEADERS.copy()
        auth_headers['Authorization'] = f"Bearer {token}"
        
        endpoints = [
            "/account/me",
            "/data/student-gpa-list",
            "/data/schedule-list",
            "/education/schedule",
             "/data/subject-task-student-list" # Retrying
        ]

        for ep in endpoints:
             print(f"--- Probing {ep} ---")
             r = await client.get(f"{BASE_URL}{ep}", headers=auth_headers)
             print(f"Status: {r.status_code}")
             if r.status_code == 200:
                 try:
                    d = r.json()
                    items = d.get('data', {}).get('items', [])
                    if not items and isinstance(d.get('data'), list): items = d.get('data')
                    
                    print(f"Items count: {len(items)}")
                    if items:
                         print("Sample:", json.dumps(items[0], indent=2))
                 except:
                    print(f"Response (Non-JSON or Error): {r.text[:200]}")
             else:
                 print(f"Error: {r.text[:200]}")

if __name__ == "__main__":
    asyncio.run(probe())
