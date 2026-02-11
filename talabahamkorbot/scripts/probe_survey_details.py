import httpx
import asyncio
import json

BASE_URL = "https://student.jmcu.uz/rest/v1"
LOGIN = "395251101411"
PASS = "OshiqAli2623"

async def probe():
    client = httpx.AsyncClient(verify=False, timeout=30.0)
    print("[-] Logging in...")
    resp = await client.post(f"{BASE_URL}/auth/login", json={"login": LOGIN, "password": PASS})
    if resp.status_code != 200:
        print("[!] Login failed")
        return
        
    token = resp.json().get("data", {}).get("token")
    client.headers["Authorization"] = f"Bearer {token}"
    
    print("[-] Probing Survey Structure...")
    # Based on previous probe: quizRuleProjection id is 4. themeId is 25.
    
    endpoints = [
        "/student/survey",
        "/student/survey?active=true",
        "/student/survey-start?id=4", 
        # Since it's finished, maybe we can't 'start' it, but let's see error
        "/education/poll/view?id=4",
        "/student/survey/4",
        "/student/survey/questions?id=4"
    ]
    
    for ep in endpoints:
        try:
            url = f"{BASE_URL}{ep}"
            print(f"    GET {url}...")
            r = await client.get(url)
            print(f"    Status: {r.status_code}")
            if r.status_code == 200:
                print(f"    DATA: {r.json()}")
        except: pass
        
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(probe())
