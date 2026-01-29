import asyncio
import httpx
from bs4 import BeautifulSoup

async def main():
    url = "https://student.jmcu.uz/dashboard/login"
    print(f"--- Fetching {url} ---")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        form = soup.find('form')
        if form:
             print("✅ Form Found")
             inputs = form.find_all('input')
             for inp in inputs:
                 name = inp.get('name')
                 val = inp.get('value', '')
                 print(f"Input: {name} | Value: {val[:20]}")
        else:
             print("❌ Form NOT Found")
             # maybe its id="login-form"?
             lform = soup.find(id='login-form')
             if lform:
                 print("✅ Form ID 'login-form' Found")
                 inputs = lform.find_all('input')
                 for inp in inputs:
                     print(f"Input: {inp.get('name')}")

if __name__ == "__main__":
    asyncio.run(main())
