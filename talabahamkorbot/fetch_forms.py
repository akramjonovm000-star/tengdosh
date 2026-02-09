
import asyncio
import sys
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

async def fetch_forms():
    with open("forms.log", "w") as f:
        f.write(f"Fetching Education Forms using Admin Token...\n")
        if not HEMIS_ADMIN_TOKEN:
            f.write("Error: HEMIS_ADMIN_TOKEN is missing!\n")
            return

        client = await HemisService.get_client()
        
        # Try fetching education forms list
        url = "https://student.jmcu.uz/rest/v1/education/education-form-list"
        
        try:
            response = await client.get(url, headers={"Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}"})
            f.write(f"Ref V1 URL Status: {response.status_code}\n")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', {}).get('items', []) if isinstance(data, dict) else data
                for item in items:
                    f.write(f"ID: {item.get('id')} - Name: {item.get('name')}\n")
            else:
                # Try alternative URL (Code API)
                url_alt = "https://student.jmcu.uz/rest/v1/code/education-form-list"
                resp2 = await client.get(url_alt, headers={"Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}"})
                f.write(f"Alt URL Status: {resp2.status_code}\n")
                if resp2.status_code == 200:
                     data = resp2.json()
                     items = data.get('data', {}).get('items', []) if isinstance(data, dict) else data
                     for item in items:
                        f.write(f"ID: {item.get('code')} - Name: {item.get('name')}\n")

        except Exception as e:
            f.write(f"Error: {e}\n")
        finally:
            await HemisService.close_client()

if __name__ == "__main__":
    asyncio.run(fetch_forms())
