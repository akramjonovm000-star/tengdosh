
import asyncio
import httpx
from bs4 import BeautifulSoup
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_scapping():
    login = "395251101411" # Extracted from logs
    password = "dummy_password_replaced_by_user_if_needed" 
    # Use dummy first to see if we even get past CSRF check (which usually returns 200 OK + error text for Bad Creds, but 400 for CSRF)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            base_web_url = "https://student.jmcu.uz"
            login_url = f"{base_web_url}/dashboard/login"
            
            # 1. GET Login Page to fetch CSRF token
            logger.info("Fetching Login Page for CSRF...")
            resp = await client.get(login_url, timeout=10)
            print(f"GET Status: {resp.status_code}")
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # PRINT ALL INPUTS TO SEE REAL NAMES
            inputs = soup.find_all("input")
            print("--- FORM INPUTS ---")
            csrf_token = None
            for i in inputs:
                name = i.get("name")
                val = i.get("value")
                print(f"Input: {name} = {val}")
                if name == "_csrf" or name == "_csrf-frontend":
                    csrf_token = val
            
            # Also check meta
            meta = soup.find("meta", {"name": "csrf-token"})
            if meta:
                print(f"Meta CSRF: {meta.get('content')}")
                if not csrf_token: csrf_token = meta.get('content')
            
            print(f"Using CSRF: {csrf_token}")

            # 2. POST Login Data
            # Try capturing cookies explicitly if needed, but httpx client does it.
            
            payload = {
                "_csrf": csrf_token,
                "LoginForm[login]": login,
                "LoginForm[password]": "wrongpassword", # Just to test 400 vs 200
                "LoginForm[rememberMe]": "1"
            }
            
            print(f"Posting Payload Keys: {list(payload.keys())}")
            
            login_resp = await client.post(login_url, data=payload, timeout=15)
            print(f"POST Status: {login_resp.status_code}")
            print(f"POST URL: {login_resp.url}")
            
            if login_resp.status_code == 400:
                print("--- 400 RESPONSE CONTENT ---")
                print(login_resp.text[:500]) # Print start of error
                
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_scapping())
