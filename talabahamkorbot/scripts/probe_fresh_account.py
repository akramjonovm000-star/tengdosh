import httpx
import asyncio
import json

BASE_URL = "https://student.jmcu.uz/rest/v1"
LOGINS = ["395251101411", "395251101398"]
PASSWORDS = ["OshiqAli2623", "AD1870724", "ad1870724"]

async def probe():
    client = httpx.AsyncClient(verify=False, timeout=30.0)
    
    token = None
    for login in LOGINS:
        for pwd in PASSWORDS:
            print(f"[-] Trying Login: {login} with '{pwd}'...")
            try:
                resp = await client.post(f"{BASE_URL}/auth/login", json={"login": login, "password": pwd})
                if resp.status_code == 200:
                    print(f"    [+] SUCCESS: {login}")
                    token = resp.json().get("data", {}).get("token")
                    break 
                else:
                    print(f"    [-] Failed: {resp.status_code} Body: {resp.text}")
            except: pass
        if token: break
        
    if not token:
        print("[!] All Logins Failed.")
        return

    client.headers["Authorization"] = f"Bearer {token}"
    
    # 1. Check Survey Status
    print("[-] Checking Survey Status...")
    r = await client.get(f"{BASE_URL}/student/survey")
    if r.status_code == 200:
        data = r.json().get("data", {})
        print(f"    Raw Data Summary: Keys={list(data.keys())}")
        
        # recursive print helper
        def print_structure(d, indent=4):
            if isinstance(d, dict):
                for k, v in d.items():
                    print(" " * indent + f"{k}: {type(v)}")
                    if k == "not_started" or k == "in_progress":
                        print(json.dumps(v, indent=indent+4, ensure_ascii=False)[:1000]) 
        
        print_structure(data)
        
        # 2. If we find an ID, try to view questions
        active_surveys = data.get("not_started", []) + data.get("in_progress", [])
        for s in active_surveys:
            sid = s.get("id") 
            theme_id = s.get("quizRuleProjection", {}).get("themeId")
            print(f"    [-] Found Survey ID: {sid}, ThemeID: {theme_id}")
            
            # Try to get questions
            q_endpoints = [
                f"/student/survey/questions?id={sid}",
                f"/education/quiz/view?id={sid}",
                f"/student/quiz/view?id={sid}",
                f"/student/survey/view?id={sid}",
                f"/student/survey/structure?id={sid}",
                f"/student/survey/start?id={sid}",
            ]
            
            for qep in q_endpoints:
                try:
                    print(f"        Requesting {qep}...")
                    qr = await client.get(f"{BASE_URL}{qep}")
                    if qr.status_code == 200:
                        print(f"        [!] FOUND QUESTIONS at {qep}")
                        print(json.dumps(qr.json(), indent=4, ensure_ascii=False)[:2000])
                except Exception as e:
                    print(f"        Error on {qep}: {e}")

    else:
         print(f"    [!] Survey List Failed: {r.status_code}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(probe())
