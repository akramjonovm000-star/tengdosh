import httpx
import asyncio
import json

BASE_URL = "https://student.jmcu.uz/rest/v1"
TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJoZW1pcy4zOTUiLCJhdWQiOiJzdHVkZW50IiwiZXhwIjoxNzcxMDM4NzYyLCJqdGkiOiIzOTUyNTExMDIwNDAiLCJzdWIiOiI5MTk1In0.-QVRYmAh7IQ9rR7yKLFtdYNZ2z5iy3Eh2XynKY-y72g"

async def probe():
    client = httpx.AsyncClient(verify=False, timeout=30.0)
    client.headers["Authorization"] = f"Bearer {TOKEN}"
    
    print("[-] Checking Survey Status with Token...")
    try:
        r = await client.get(f"{BASE_URL}/student/survey")
        if r.status_code == 200:
            data = r.json().get("data", {})
            print(f"    Raw Data Summary: Keys={list(data.keys())}")
            
            # Look for active survey ID
            active_surveys = data.get("not_started", []) + data.get("in_progress", [])
            print(f"    [DUMP] Active Surveys: {json.dumps(active_surveys, indent=4, ensure_ascii=False)}")
            
            for s in active_surveys:
                # Based on dump: quizRuleProjection -> id
                sid = s.get("quizRuleProjection", {}).get("id")
                theme_id = s.get("quizRuleProjection", {}).get("themeId")
                
                print(f"    [-] Found Survey ID: {sid}, ThemeID: {theme_id}")
                
                # Try to get questions or start it
                # Try POST with body
                post_attempts = [
                    {"url": "/student/survey-start", "json": {"id": sid}},
                    {"url": "/student/survey-start", "json": {"id": theme_id}},
                    {"url": "/student/survey-start", "json": {"quizId": sid}},
                    {"url": "/student/survey-start", "json": {"structureId": sid}},
                    {"url": "/student/survey-start", "json": {"themeId": theme_id}},
                ]
                
                for attempt in post_attempts:
                    qep = attempt["url"]
                    body = attempt["json"]
                    try:
                        print(f"        POST {qep} with {body}...")
                        qr = await client.post(f"{BASE_URL}{qep}", json=body)
                            
                        if qr.status_code == 200:
                            print(f"        [!] FOUND RESPONSE at {qep} with {body}")
                            print(json.dumps(qr.json(), indent=4, ensure_ascii=False)[:3000])
                            
                            with open("survey_structure.json", "w") as f:
                                json.dump(qr.json(), f, indent=4, ensure_ascii=False)
                            print("        [+] Saved to survey_structure.json")
                            return
                        else:
                            print(f"        [-] Failed {qep}: {qr.status_code}")
                    except Exception as e:
                        print(f"        Error: {e}")
        else:
            print(f"    [!] Failed to get survey list: {r.status_code} {r.text}")
            
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(probe())
