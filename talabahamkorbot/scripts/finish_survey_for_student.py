import httpx
import asyncio
import json
import random

BASE_URL = "https://student.jmcu.uz/rest/v1"
TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJoZW1pcy4zOTUiLCJhdWQiOiJzdHVkZW50IiwiZXhwIjoxNzcxMDM4NzYyLCJqdGkiOiIzOTUyNTExMDIwNDAiLCJzdWIiOiI5MTk1In0.-QVRYmAh7IQ9rR7yKLFtdYNZ2z5iy3Eh2XynKY-y72g"
SURVEY_ID = 4

# Load structure
with open("survey_structure.json", "r") as f:
    structure = json.load(f)

questions = structure["data"]["questions"]

async def finish_survey():
    client = httpx.AsyncClient(verify=False, timeout=30.0)
    client.headers["Authorization"] = f"Bearer {TOKEN}"
    
    print(f"[-] Starting survey completion for {len(questions)} questions...")
    
    for q in questions:
        qid = q["id"]
        qtype = q["buttonType"]
        variants = q["variants"]
        
        answer = None
        
        if qtype == "radio":
            # Pick a positive/neutral answer (usually index 0 or 'yaxshi', 'a'lo')
            # Let's pick the first one for simplicity, usually they differ
            # Or pick random? User said "finish one", didn't specify answers.
            # Let's pick index 0.
            if variants:
                answer = variants[0]
        elif qtype == "checkbox":
            if variants:
                answer = [variants[0]] # Send as list?
        elif qtype == "input":
            answer = "Taklifim yo'q"
            
        if answer is not None:
             print(f"    Submitting Q {qid} ({qtype}): {str(answer)[:20]}...")
             try:
                 resp = await client.post(f"{BASE_URL}/student/survey-answer", json={
                     "question_id": qid,
                     "answer": answer
                 })
                 if resp.status_code != 200:
                     print(f"    [!] Failed Q {qid}: {resp.status_code} {resp.text}")
             except Exception as e:
                 print(f"    [!] Error Q {qid}: {e}")
        
    print("[-] All answers submitted. Calling finish...")
    
    # Try different finish payloads
    finish_endpoints = [
        {"url": f"/student/survey-finish", "json": {"id": SURVEY_ID}},
        {"url": f"/student/survey-finish?id={SURVEY_ID}", "json": {}},
    ]
    
    success = False
    for attempt in finish_endpoints:
        try:
            print(f"    POST {attempt['url']} {attempt['json']}")
            r = await client.post(f"{BASE_URL}{attempt['url']}", json=attempt['json'])
            if r.status_code == 200:
                print(f"    [!] FINISH SUCCESS: {r.json()}")
                success = True
                break
            else:
                print(f"    [-] Finish Failed: {r.status_code}")
        except: pass
        
    if success:
        print("[-] Verifying status...")
        r = await client.get(f"{BASE_URL}/student/survey")
        print(f"    Status: {r.json().get('data', {}).get('finished', [])}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(finish_survey())
