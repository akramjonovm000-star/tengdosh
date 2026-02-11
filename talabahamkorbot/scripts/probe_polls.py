import httpx
import asyncio
import json

# Provided Token
ADMIN_TOKEN = "LXjqwQE0Xemgq3E7LeB0tn2yMQWY0zXW"
BASE_URL = "https://student.jmcu.uz/rest/v1"

async def probe():
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    client = httpx.AsyncClient(verify=False, headers=headers, timeout=30.0)
    
    print(f"[-] Probing HEMIS API...")

    # . Deep Student Inspection
    print("\n[-] Deep Student Inspection...")
    try:
        # Get a student ID first
        resp = await client.get(f"{BASE_URL}/data/student-list", params={"limit": 1})
        if resp.status_code == 200:
            student = resp.json().get("data", {}).get("items", [])[0]
            sid = student.get("id")
            print(f"    Target Student ID: {sid} ({student.get('first_name')})")
            
            # Check /data/student-info
            print(f"    Probing /data/student-info?student_id={sid} ...")
            r = await client.get(f"{BASE_URL}/data/student-info", params={"student_id": sid})
            print(f"    /data/student-info: {r.status_code}")
            if r.status_code == 200:
                data = r.json().get("data", {})
                print(f"    Keys: {list(data.keys())}")
                # Check suspicious data keys
                suspicious = [k for k in data.keys() if "poll" in k or "survey" in k or "status" in k]
                for k in suspicious:
                    print(f"    -> {k}: {data[k]}")

            # Check /education/task-list (Trying admin access to student tasks?)
            print(f"    Probing /education/task-list ...")
            r = await client.get(f"{BASE_URL}/education/task-list", params={"_student": sid}) 
            print(f"    /education/task-list (Admin): {r.status_code}")
            
    except Exception as e:
        print(f"    [!] Error: {e}")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(probe())
