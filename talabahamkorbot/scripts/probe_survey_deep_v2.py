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
    
    # Try combinations
    prefixes = ["/student", "/education", "/data"]
    nouns = ["survey", "poll", "quiz", "questionnaire"]
    actions = ["structure", "questions", "items", "meta", "detail", "view", "start"]
    
    ids = [4, 25]
    
    for p in prefixes:
        for n in nouns:
            for a in actions:
                for i in ids:
                    path = f"{p}/{n}/{a}"
                    try:
                        # Try with query param
                        url = f"{BASE_URL}{path}"
                        params = {"id": i}
                        # print(f"Trying {url} id={i}...")
                        r = await client.get(url, params=params)
                        if r.status_code == 200:
                            print(f"[!] SUCCESS: {url}?id={i}")
                            print(f"    DATA: {str(r.json())[:200]}...")
                            return # Stop on first
                    except: pass
                    
                    try:
                         # Try with REST path
                        url = f"{BASE_URL}{path}/{i}"
                        # print(f"Trying {url}...")
                        r = await client.get(url)
                        if r.status_code == 200:
                            print(f"[!] SUCCESS: {url}")
                            print(f"    DATA: {str(r.json())[:200]}...")
                            return
                    except: pass

    await client.aclose()
    print("[-] Done.")

if __name__ == "__main__":
    asyncio.run(probe())
