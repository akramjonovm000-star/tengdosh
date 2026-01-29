import asyncio
import httpx

async def probe_auth_form():
    url = "https://student.jmcu.uz/rest/v1/auth/login"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    payload = {
        "login": "395251101411",
        "password": "wrong_password" 
    }
    
    print(f"POSTing FORM to {url}")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, data=payload, headers=headers, timeout=20)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(probe_auth_form())
