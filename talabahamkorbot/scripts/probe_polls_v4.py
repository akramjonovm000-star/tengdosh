import httpx
import asyncio
import json

ADMIN_TOKEN = "LXjqwQE0Xemgq3E7LeB0tn2yMQWY0zXW"
BASE_URL = "https://student.jmcu.uz/rest/v1"
TARGET_LOGIN = "397251101398"

async def probe():
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    client = httpx.AsyncClient(verify=False, headers=headers, timeout=30.0)
    
    print(f"[-] Searching for student {TARGET_LOGIN}...")
    try:
        # Search by search param (usually works for ID/Login)
        resp = await client.get(f"{BASE_URL}/data/student-list", params={"search": TARGET_LOGIN})
        # Also try filtering by student_id_number if exposed?
        
        sid = None
        if resp.status_code == 200:
            items = resp.json().get("data", {}).get("items", [])
            print(f"    Found {len(items)} matches.")
            for s in items:
                # Check if login or id matches
                print(f"    - ID: {s.get('id')} Name: {s.get('full_name')} Login: {s.get('student_id_number')}")
                if str(s.get('student_id_number')) == TARGET_LOGIN:
                    sid = s.get("id")
                    break
        
        if sid:
            print(f"    [*] Target ID: {sid}")
            
            # Now Check Poll List for THIS student
            url = f"{BASE_URL}/data/poll-list"
            print(f"    Requesting {url}?student_id={sid} ...")
            r = await client.get(url, params={"student_id": sid})
            print(f"    Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json().get("data", {})
                polls = data.get("items", [])
                print(f"    Polls Found via Admin: {len(polls)}")
                print(f"    Raw: {polls}")
        else:
             print("    [!] Exact match for student not found.")

    except Exception as e:
        print(f"    [!] Error: {e}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(probe())
