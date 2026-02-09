
import asyncio
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

async def fetch_levels():
    with open("hemis_levels.log", "w") as f:
        f.write(f"Fetching Levels using Admin Token...\n")
        
        client = await HemisService.get_client()
        # Common endpoints for levels
        urls = [
            "https://student.jmcu.uz/rest/v1/education/level-list",
            "https://student.jmcu.uz/rest/v1/data/level-list",
            "https://student.jmcu.uz/rest/v1/code/level-list"
        ]
        
        for url in urls:
            try:
                f.write(f"Trying {url}...\n")
                response = await client.get(url, headers={"Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}"})
                f.write(f"Status: {response.status_code}\n")
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('data', {}).get('items', []) if isinstance(data, dict) else data
                    # Handle if it returns a plain list or dict
                    if isinstance(data, list): items = data
                    
                    for item in items:
                        f.write(f"ID: {item.get('id')}, Code: {item.get('code')}, Name: {item.get('name')}\n")
                    break # Stop if successful
            except Exception as e:
                f.write(f"Error on {url}: {e}\n")
        
        await HemisService.close_client()

if __name__ == "__main__":
    asyncio.run(fetch_levels())
