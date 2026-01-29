import httpx
import asyncio

async def test_login():
    url = "https://student.jmcu.uz/rest/v1/auth/login"
    
    # Payload 1: String Login
    payload_str = {"login": "1234567890", "password": "wrong_password"}
    
    # Payload 2: Int Login
    payload_int = {"login": 1234567890, "password": "wrong_password"}
    
    async with httpx.AsyncClient(verify=False) as client:
        print(f"--- Testing URL: {url} ---")
        
        # Test 1
        print("\nTest 1 (String Login):")
        try:
            resp = await client.post(url, json=payload_str)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")
            
        # Test 2
        print("\nTest 2 (Int Login):")
        try:
            resp = await client.post(url, json=payload_int)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())
