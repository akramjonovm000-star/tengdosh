import asyncio
import sys
import os
import csv
import httpx
import json
from datetime import datetime
from sqlalchemy import select

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connect import get_session_factory
from database.models import Student

BASE_URL = "https://student.jmcu.uz/rest/v1"
OUTPUT_FILE = "survey_completion_report.csv"
DEFAULT_SURVEY_ID = 4
CONCURRENCY_LIMIT = 20

# Survey Logic
async def get_survey_status(client, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = await client.get(f"{BASE_URL}/student/survey", headers=headers)
        if r.status_code == 200:
            data = r.json().get("data", {})
            return data
        return None
    except:
        return None

async def solve_survey(client, token, survey_data):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Get Survey ID
    survey_id = DEFAULT_SURVEY_ID
    
    # 2. Check active polls if needed
    try:
        r = await client.get(f"{BASE_URL}/education/poll-list", headers=headers)
        if r.status_code == 200:
            items = r.json().get("data", {}).get("items", [])
            if items:
                survey_id = items[0].get("id", DEFAULT_SURVEY_ID)
    except: pass

    # 3. Start Survey
    # print(f"    Starting Survey {survey_id}...")
    r = await client.post(f"{BASE_URL}/student/survey-start", headers=headers, json={"id": survey_id})
    
    # Response should contain questions
    questions = r.json().get("data", {}).get("questions", [])
    if not questions:
        # Try fetching running survey
        r = await client.get(f"{BASE_URL}/student/survey", headers=headers)
        questions = r.json().get("data", {}).get("questions", [])

    if not questions:
        return False

    # 4. Answer Questions
    for q in questions:
        qid = q["id"]
        qtype = q["buttonType"]
        variants = q["variants"]
        answer = None
        
        if qtype == "radio" and variants:
            answer = variants[0]
        elif qtype == "checkbox" and variants:
            answer = [variants[0]]
        elif qtype == "input":
            answer = "Taklifim yo'q"
            
        if answer is not None:
             await client.post(f"{BASE_URL}/student/survey-answer", headers=headers, json={
                 "question_id": qid,
                 "answer": answer
             })
             
    # 5. Finish Survey
    payloads = [
        {"id": survey_id},
        {"quiz_rule_id": survey_id},
        {}
    ]
    
    for p in payloads:
        r = await client.post(f"{BASE_URL}/student/survey-finish", headers=headers, json=p)
        if r.status_code == 200:
            return True
            
    return False

async def process_student(sem, client, s, i, total, report_data):
    async with sem:
        try:
            print(f"[{i+1}/{total}] {s.full_name} ({s.hemis_login}) checking...")
            
            status_data = await get_survey_status(client, s.hemis_token)
            final_status = "Noma'lum"
            
            if not status_data:
                final_status = "Token Eskirgan/Xato"
            else:
                if status_data.get("finished"):
                    final_status = "Yakunlagan (Oldindan)"
                else:
                    success = await solve_survey(client, s.hemis_token, status_data)
                    if success:
                        final_status = "Yakunlandi (Bot)"
                        print(f"    [+] {s.full_name}: DONE")
                    else:
                        final_status = "Xatolik (Tugata olmadi)"
                        print(f"    [-] {s.full_name}: ID {s.hemis_login} Failed")
            
            report_data.append({
                "Hemis Login": s.hemis_login,
                "Name": s.full_name,
                "Group": s.group_number,
                "Result": final_status,
                "Token": "YES" if s.hemis_token else "NO"
            })
        except Exception as e:
            print(f"    Error processing {s.full_name}: {e}")
            report_data.append({
                "Hemis Login": s.hemis_login,
                "Name": s.full_name,
                "Group": s.group_number,
                "Result": f"Exception: {e}",
                "Token": "YES"
            })

async def main():
    print("[-] Starting Concurrent Bulk Survey Solver...")
    AsyncSessionLocal = get_session_factory()
    
    report_data = []
    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    async with AsyncSessionLocal() as session:
        # Get all students with tokens
        stmt = select(Student).where(Student.hemis_token.isnot(None))
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        print(f"[-] Found {len(students)} students with tokens. Processing...")
        
        async with httpx.AsyncClient(verify=False, timeout=60.0, limits=httpx.Limits(max_keepalive_connections=20, max_connections=30)) as client:
            tasks = []
            for i, s in enumerate(students):
                tasks.append(process_student(sem, client, s, i, len(students), report_data))
            
            await asyncio.gather(*tasks)
                
    # Save Report
    if report_data:
        keys = report_data[0].keys()
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(report_data)
        print(f"[+] Report saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
