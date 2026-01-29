import httpx
import asyncio

async def test_string_vs_int():
    url = "https://student.jmcu.uz/rest/v1/auth/login"
    
    # Payload 1: String digits
    payload_str = {"login": "3902001", "password": "wrong_password"}
    
    # Payload 2: Int digits
    payload_int = {"login": 3902001, "password": "wrong_password"}
    
    async with httpx.AsyncClient(verify=False) as client:
        print(f"--- Testing URL: {url} ---")
        
        print("\nTest 1 (String Digits):")
        try:
            resp = await client.post(url, json=payload_str)
            print(f"Status: {resp.status_code}")
        except Exception as e:
            print(f"Error: {e}")
            
        print("\nTest 2 (Int Digits):")
        try:
            resp = await client.post(url, json=payload_int)
            print(f"Status: {resp.status_code}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_string_vs_int())
