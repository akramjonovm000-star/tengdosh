
import asyncio
import json
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

async def main():
    if not HEMIS_ADMIN_TOKEN: return
    client = await HemisService.get_client()
    
    endpoints = [
        "/data/group-list",
        "/education/group-list",
        "/data/group",
        "/education/group",
        "/metadata/group-list"
    ]
    
    print("\n--- TESTING GROUP ENDPOINTS ---")
    for ep in endpoints:
        url = f"{HemisService.BASE_URL}{ep}"
        r = await client.get(url, headers={"Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}"}, params={"limit": 100})
        print(f"Endpoint {ep}: Status {r.status_code}")
        if r.status_code == 200:
            data = r.json().get("data", {})
            items = data if isinstance(data, list) else data.get("items", [])
            print(f"Found {len(items)} groups.")
            for item in items[:10]:
                print(f"  {item.get('name')}: ID {item.get('id')}")
            break
    else:
        # Fallback: Search via student list _query
        print("\n--- FALLBACK: SEARCHING VIA STUDENT LIST ---")
        url = f"{HemisService.BASE_URL}/data/student-list"
        # Try to find a specific group from the screenshot: "25-22 AXBOROT XIZMATI VA JAMOATCHILIK BILAN ALOQALAR (KUNDUZGI) (O'ZBEK)"
        r = await client.get(url, headers={"Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}"}, params={"_query": "25-22", "limit": 10})
        if r.status_code == 200:
            items = r.json().get("data", {}).get("items", [])
            for item in items:
                group = item.get("group")
                if group:
                    print(f"  Group: {group.get('name')} (ID: {group.get('id')})")
                    break

    await HemisService.close_client()

if __name__ == "__main__":
    asyncio.run(main())
