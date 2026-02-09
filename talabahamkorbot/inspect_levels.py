
import asyncio
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

async def main():
    try:
        print("Fetching students to inspect levels...", flush=True)
        # Fetch a few pages to get different levels if possible
        client = await HemisService.get_client()
        url = f"{HemisService.BASE_URL}/data/student-list"
        
        levels_found = {}
        
        # Try page 1, 10, 50 to get variety
        for page in [1, 10, 50]:
            print(f"Checking page {page}...", flush=True)
            response = await client.get(url, headers={"Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}"}, params={"limit": 20, "page": page})
            
            if response.status_code == 200:
                data = response.json().get("data", {}).get("items", [])
                for item in data:
                    lvl = item.get("level", {})
                    lid = lvl.get("id")
                    lname = lvl.get("name")
                    lcode = lvl.get("code")
                    if lid and lname and lid not in levels_found:
                        levels_found[lid] = f"{lname} (Code: {lcode})"
                        print(f"FOUND LEVEL: ID={lid} Name={lname} Code={lcode}", flush=True)
            else:
                print(f"Page {page} failed: {response.status_code}", flush=True)
                
        print("Summary of Levels Found:", flush=True)
        print(levels_found, flush=True)

    except Exception as e:
        print(f"Error: {e}", flush=True)
    finally:
        await HemisService.close_client()

if __name__ == "__main__":
    asyncio.run(main())
