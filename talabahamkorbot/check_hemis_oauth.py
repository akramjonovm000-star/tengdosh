import asyncio
import httpx
import base64

# Credentials from User Image
CLIENT_ID = "999"
CLIENT_SECRET = "746d4999359843467d434f348ef26215ecfeb799"
BASE_URL = "https://student.jmcu.uz/rest/v1"
OAUTH_URL = "https://student.jmcu.uz/oauth/token" # Guessing standard endpoint, will try others too

async def test_oauth():
    async with httpx.AsyncClient() as client:
        print(f"Testing Credentials for {BASE_URL}...")

        # 1. Try Client Credentials Flow
        print("\n--- Attempt 1: Client Credentials Grant ---")
        endpoints = [
            "https://student.jmcu.uz/oauth/access_token", # Standard usually
            "https://student.jmcu.uz/rest/v1/auth/access-token",
            "https://student.jmcu.uz/api/oauth/v1/token",
            "https://student.jmcu.uz/oauth/token" 
        ]
        
        for url in endpoints:
            try:
                print(f"Trying POST {url}...")
                resp = await client.post(
                    url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET
                    },
                    timeout=5
                )
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"SUCCESS! Endpoint: {url}")
                    print("Response:", resp.text)
            except Exception as e:
                print(f"Error {url}: {e}")

if __name__ == "__main__":
    asyncio.run(test_oauth())
