import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database.db_connect import AsyncSessionLocal
from database.models import TgAccount
from services.hemis_service import HemisService

# Configure logging to see details
logging.basicConfig(level=logging.INFO)

USER_TG_ID = 8155790902

async def main():
    print("--- 1. Fetching Credentials ---")
    async with AsyncSessionLocal() as session:
        stmt = select(TgAccount).options(joinedload(TgAccount.student)).where(TgAccount.telegram_id == USER_TG_ID)
        result = await session.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account or not account.student:
            print("❌ User not found in DB")
            return
            
        login = account.student.hemis_login
        password = account.student.hemis_password
        
        print(f"User: {login}")
        # print(f"Pass: {password}") # Don't print password
        
        if not password:
            print("❌ Password not found in DB")
            return

    print(f"User: {login}")
    
    # Debugging logic inside HemisService is hard to see.
    # Let's reproduce the code here for verbose output.
    import httpx
    from bs4 import BeautifulSoup
    
    client = httpx.AsyncClient(follow_redirects=False, timeout=20.0) # Disable redirects to see 302
    try:
        login_url = "https://student.jmcu.uz/dashboard/login"
        page = await client.get(login_url)
        print(f"GET Cookies: {dict(client.cookies)}")
        
        soup = BeautifulSoup(page.text, 'html.parser')
        csrf_nodes = soup.find_all('input', {'name': '_csrf-frontend'})
        if not csrf_nodes:
            print("❌ CSRF check via name='_csrf-frontend' FAILED")
            print("Dumping forms:")
            for f in soup.find_all('form'):
                print(f"Form action: {f.get('action')}")
                print(f"Inputs: {[i.get('name') for i in f.find_all('input')]}")
            return

        csrf = csrf_nodes[0]['value']
        print(f"CSRF: {csrf}")
        
        payload = {
            '_csrf-frontend': csrf,
            'FormStudentLogin[login]': login,
            'FormStudentLogin[password]': password,
            'FormStudentLogin[rememberMe]': '0',
            'FormStudentLogin[hasCaptcha]': '0' # Try disabling captcha explicitly
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": login_url,
            "Origin": "https://student.jmcu.uz"
        }
        
        resp = await client.post(login_url, data=payload, headers=headers)
        print(f"POST Status: {resp.status_code}")
        if 'location' in resp.headers:
            print(f"Redirect To: {resp.headers['location']}")
            
        if resp.status_code == 200:
             print("Response Text Preview:")
             print(resp.text[:500])
             
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
