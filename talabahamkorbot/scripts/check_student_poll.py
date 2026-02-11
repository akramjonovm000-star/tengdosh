import httpx
import asyncio
import argparse

BASE_URL = "https://student.jmcu.uz/rest/v1"

async def check_poll(login, password):
    client = httpx.AsyncClient(verify=False, timeout=30.0)
    print(f"[-] Checking Poll Status for {login}...")
    
    try:
        # 1. Login
        resp = await client.post(f"{BASE_URL}/auth/login", json={"login": login, "password": password})
        if resp.status_code != 200:
            print(f"    [!] Login Failed: {resp.status_code}")
            return "Login Failed"

        token = resp.json().get("data", {}).get("token")
        client.headers["Authorization"] = f"Bearer {token}"
        
        # 2. Check Survey
        r = await client.get(f"{BASE_URL}/student/survey")
        if r.status_code == 200:
            data = r.json().get("data", {})
            
            # Check finished
            finished = data.get("finished", [])
            if finished:
                poll = finished[0]
                print(f"    [*] STATUS: FINISHED (Quiz ID: {poll.get('quizRuleProjection', {}).get('id')})")
                return "Finished"
            
            # Check In Progress
            in_progress = data.get("in_progress", [])
            if in_progress:
                print(f"    [*] STATUS: IN PROGRESS")
                return "In Progress"
                
            # Check Not Started
            not_started = data.get("not_started", [])
            if not_started:
                print(f"    [*] STATUS: NOT STARTED")
                return "Not Started"
                
            print("    [?] Status Unknown (No poll found)")
            return "Unknown"
            
        else:
            print(f"    [!] Survey API Error: {r.status_code}")
            return "API Error"
            
    except Exception as e:
        print(f"    [!] Error: {e}")
        return "Error"
    finally:
        await client.aclose()

if __name__ == "__main__":
    # Example usage: python3 check_student_poll.py
    # Ideally expects args, but hardcoded for demo
    asyncio.run(check_poll("395251101411", "OshiqAli2623"))
