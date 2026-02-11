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
    token = resp.json().get("data", {}).get("token")
    client.headers["Authorization"] = f"Bearer {token}"
    
    print("[-] Probing for Questions...")
    
    # Try different combinations of IDs
    ids = [4, 25] # 4=id, 25=themeId
    
    endpoints = [
        "/student/survey/view",
        "/student/quiz/view",
        "/education/quiz/view",
        "/education/poll/view",
    ]
    
    for ep in endpoints:
        for i in ids:
            try:
                url = f"{BASE_URL}{ep}"
                params = {"id": i}
                print(f"    GET {url}?id={i}...")
                r = await client.get(url, params=params)
                print(f"    Status: {r.status_code}")
                if r.status_code == 200:
                    print(f"    DATA: {r.json()}")
            except: pass

    # Try to see "My Answers" if finished
    print("[-] Probing My Answers...")
    try:
        url = f"{BASE_URL}/student/survey-answer"
        r = await client.get(url, params={"id": 4})
        print(f"    GET {url}?id=4: {r.status_code}")
        if r.status_code == 200:
            print(f"    DATA: {r.json()}")
    except: pass

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(probe())
