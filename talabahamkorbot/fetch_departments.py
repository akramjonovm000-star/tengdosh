
import asyncio
import sys
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

async def fetch_deps():
    with open("departments.log", "w") as f:
        f.write(f"Fetching Departments using Admin Token...\n")
        
        client = await HemisService.get_client()
        url = "https://student.jmcu.uz/rest/v1/data/department-list"
        
        try:
            response = await client.get(url, headers={"Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}"})
            f.write(f"Ref V1 URL Status: {response.status_code}\n")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', {}).get('items', []) if isinstance(data, dict) else data
                for item in items:
                    f.write(f"ID: {item.get('id')} - Name: {item.get('name')}\n")
        except Exception as e:
            f.write(f"Error: {e}\n")
        finally:
            await HemisService.close_client()

if __name__ == "__main__":
    asyncio.run(fetch_deps())
