import httpx
import asyncio

async def test_login():
    url = "http://localhost:8000/api/v1/auth/hemis"
    payload = {
        "login": "Sanjar_botirovich",
        "password": "102938"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            print(f"Status: {response.status_code}")
            print(f"Body: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())
