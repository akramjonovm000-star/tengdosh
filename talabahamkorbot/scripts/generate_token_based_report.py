import asyncio
import sys
import os
import csv
import httpx
from datetime import datetime

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from database.db_connect import get_session_factory
from database.models import Student

BASE_URL = "https://student.jmcu.uz/rest/v1"
TARGET_FACULTY = "PR va menejment fakulteti"
OUTPUT_FILE = "poll_report_pr.csv"

async def check_survey_status(client, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = await client.get(f"{BASE_URL}/student/survey", headers=headers)
        if r.status_code == 200:
            data = r.json().get("data", {})
            if data.get("finished"):
                return "Yakunlagan"
            elif data.get("in_progress"):
                return "Jarayonda"
            elif data.get("not_started"):
                return "Boshlanmagan"
            else:
                return "Noma'lum"
        elif r.status_code == 401:
            return "Token Eskirgan"
        else:
            return f"Xato: {r.status_code}"
    except Exception as e:
        return f"Xato: {str(e)}"

async def generate_report():
    print(f"[-] Fetching students for '{TARGET_FACULTY}'...")
    
    AsyncSessionLocal = get_session_factory()
    students_data = []
    
    async with AsyncSessionLocal() as session:
        stmt = select(Student).where(
            Student.faculty_name == TARGET_FACULTY,
            Student.hemis_token.isnot(None)
        )
        result = await session.execute(stmt)
        students = result.scalars().all()
        
        print(f"[-] Found {len(students)} students with tokens.")
        
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            for i, s in enumerate(students):
                status = await check_survey_status(client, s.hemis_token)
                print(f"    [{i+1}/{len(students)}] {s.full_name}: {status}")
                students_data.append({
                    "Ism Familiya": s.full_name,
                    "Yo'nalish": s.specialty_name,
                    "Guruh": s.group_number,
                    "Status": status,
                    "Oxirgi kirish": str(s.created_at)
                })

    # Write CSV
    if students_data:
        keys = students_data[0].keys()
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(students_data)
        print(f"[+] Report saved to {OUTPUT_FILE}")
    else:
        print("[!] No students found or processed.")

if __name__ == "__main__":
    asyncio.run(generate_report())
