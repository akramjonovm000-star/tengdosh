import asyncio
import httpx
from bs4 import BeautifulSoup
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from config import HEMIS_URL
HEMIS_URL = "https://student.jmcu.uz"

# Target User with known password (from logs/db)
# I will use the ID from the user screenshot: 8303 (Student ID?) No, ID: 8300 in screenshot 1.
# Or I can query the DB for ANY student with a password.

from database.db_connect import AsyncSessionLocal
from database.models import Student
from sqlalchemy import select

async def probe_pdfs():
    print(f"🚀 Probing {HEMIS_URL} for PDF links...")
    
    async with AsyncSessionLocal() as session:
        # Get a student with password
        result = await session.execute(select(Student).where(Student.hemis_password.is_not(None)))
        student = result.scalars().first()
        
        if not student:
            print("❌ No student with saved password found in DB.")
            return
            
        print(f"👤 Using Student: {student.full_name} ({student.hemis_id})")
        
        if not student.hemis_token:
            print("❌ No HEMIS Token found for this student.")
            return

        print(f"🔑 Using Token: {student.hemis_token[:10]}...")
        
        async with httpx.AsyncClient(timeout=30) as client:
            headers = {
                "Authorization": f"Bearer {student.hemis_token}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            # Targets to check with API Token
            targets = [
                "/rest/v1/account/me", # Auth Check
                "/rest/v1/education/transcript",
                "/rest/v1/education/reference",
                "/student/transcript", # Web URL with Token? Sometimes works if they share session logic (unlikely but worth try)
                "/education/transcript",
                "/education/reference"
            ]
            
            for path in targets:
                url = f"{HEMIS_URL}{path}"
                print(f"\n🔎 Checking: {url}")
                resp = await client.get(url, headers=headers, follow_redirects=True)
                print(f"   📡 Status: {resp.status_code}")
                print(f"   📄 Type: {resp.headers.get('content-type', 'N/A')}")
                if resp.status_code == 200:
                    if 'application/pdf' in resp.headers.get('content-type', ''):
                        print(f"   ✅ SUCCESS! Found PDF at: {url}")
                        return
                    elif 'json' in resp.headers.get('content-type', ''):
                        print(f"   ℹ️ JSON Data: {resp.text[:200]}")


            # 3. Probe Dashboard for Links
            print(f"🔎 Scanning Dashboard: {HEMIS_URL}/dashboard/index")
            resp = await client.get(f"{HEMIS_URL}/dashboard/index", follow_redirects=True)
            
            print(f"📡 Final URL: {resp.url}")
            print(f"📡 Status: {resp.status_code}")
            print(f"📄 Response Length: {len(resp.text)}")
            if len(resp.text) == 0:
                 print("⚠️ EMPTY BODY! Headers:", resp.headers)
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Print all links to find patterns
            links = soup.find_all('a')
            print(f"🔗 Total Links Found: {len(links)}")
            
            for link in links:
                href = link.get('href', '')
                text = link.text.strip()
                # Print everything for debug
                print(f"   🔗 Found: [{text}] -> {href}")
                
                # Check for "Hujjatlar" specifically
                if "hujjat" in text.lower() or "reference" in href or "transcript" in href or "ma'lumot" in text.lower():
                     print(f"      🌟 POTENTIAL MATCH!")


if __name__ == "__main__":
    asyncio.run(probe_pdfs())
