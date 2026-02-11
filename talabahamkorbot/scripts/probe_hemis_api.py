import httpx
import asyncio
import json

ADMIN_TOKEN = "LXjqwQE0Xemgq3E7LeB0tn2yMQWY0zXW"
BASE_URL = "https://hemis.jmcu.uz/rest/v1"

async def probe():
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    client = httpx.AsyncClient(verify=False, headers=headers, timeout=30.0)
    
    print(f"[-] Probing HEMIS (Employee) API at {BASE_URL}...")

    endpoints = [
        "/data/poll-list",
        "/education/poll-list",
        "/report/list",
        "/data/report-list",
        "/reports",
        "/employee/poll-list"
    ]

    for ep in endpoints:
        try:
            url = f"{BASE_URL}{ep}"
            print(f"    Requesting {url}...")
            r = await client.get(url)
            print(f"    Status: {r.status_code}")
            if r.status_code == 200:
                print(f"    DATA: {r.json()}")
        except Exception as e:
            print(f"    [!] Error: {e}")

    # Check Docs for HEMIS API
    try:
        docs_url = "https://hemis.jmcu.uz/rest/docs.json"
        print(f"    Fetching docs from {docs_url}...")
        r = await client.get(docs_url)
        if r.status_code == 200:
             paths = list(r.json().get("paths", {}).keys())
             candidates = [p for p in paths if "poll" in p or "survey" in p or "report" in p]
             print(f"    Candidates: {candidates}")
    except: pass

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(probe())
