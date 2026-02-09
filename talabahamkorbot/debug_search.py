
import asyncio
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

async def main():
    with open("debug_search.log", "w") as f:
        if not HEMIS_ADMIN_TOKEN:
            f.write("No Admin Token found!\n")
            return

        f.write("--- DEBUGGING LEVEL FILTER ---\n")
        client = await HemisService.get_client()
        
        # Try different level IDs
        test_ids = [1, 2, 3, 4, 11, 12, 13, 14, 21, 22]
        
        for lvl_id in test_ids:
            f.write(f"\nTesting _level={lvl_id}...\n")
            try:
                url = f"{HemisService.BASE_URL}/data/student-list"
                params = {
                    "limit": 1,
                    "page": 1,
                    "_level": lvl_id
                }
                response = await client.get(url, headers={"Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}"}, params=params)
                
                if response.status_code == 200:
                    data = response.json().get("data", {})
                    total = data.get("pagination", {}).get("totalCount", 0)
                    items = data.get("items", [])
                    f.write(f"Result: {total} students found.\n")
                    if items:
                        l_name = items[0].get("level", {}).get("name")
                        l_id = items[0].get("level", {}).get("id")
                        f.write(f"Sample Student Level: {l_name} (ID: {l_id})\n")
                else:
                    f.write(f"Failed: {response.status_code}\n")
                    f.write(response.text + "\n")
            except Exception as e:
                f.write(f"Error: {e}\n")

        await HemisService.close_client()

if __name__ == "__main__":
    asyncio.run(main())
