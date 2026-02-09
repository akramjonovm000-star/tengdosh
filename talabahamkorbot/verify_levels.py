
import asyncio
import sys
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

async def main():
    try:
        client = await HemisService.get_client()
        url = "https://student.jmcu.uz/rest/v1/education/level-list"
        print(f"Requesting: {url}", flush=True)
        
        response = await client.get(url, headers={"Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}"})
        print(f"Status: {response.status_code}", flush=True)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', {}).get('items', [])
            for item in items:
                print(f"LEVEL: {item['name']} (ID: {item['id']}, Code: {item.get('code')})", flush=True)
        else:
            print("Failed to fetch levels", flush=True)
            print(response.text, flush=True)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await HemisService.close_client()

if __name__ == "__main__":
    asyncio.run(main())
