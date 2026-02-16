import asyncio
import os
import sys
import httpx

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import HEMIS_ADMIN_TOKEN
# Base URL from HemisService
# BASE_URL = "https://student.jmcu.uz/rest/v1" 
# Use the same base URL logic
BASE_URL = "https://student.jmcu.uz/rest/v1"

async def main():
    print("Probing HEMIS for Staff: Shohrux Matayev...")
    
    headers = {
        "Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient(verify=False) as client:
        # Try common endpoints
        endpoints = [
            "/data/employee-list",
            "/employee/list",
            "/data/staff-list"
        ]
        
        found = False
        
        for ep in endpoints:
            url = f"{BASE_URL}{ep}"
            print(f"Checking {url}...")
            try:
                # Search params if supported
                params = {"search": "Shohrux"}
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("data", {}).get("items", []) or data.get("data", [])
                    print(f"  Got {len(items)} items.")
                    
                    for item in items:
                        name = item.get("name", "") or item.get("full_name", "") or f"{item.get('firstname')} {item.get('surname')}"
                        if "Shohrux" in name or "Matayev" in name or "Mataev" in name:
                            print(f"\n🎉 FOUND MATCH!")
                            print(f"ID: {item.get('id')}")
                            print(f"Name: {name}")
                            print(f"Employee ID: {item.get('employee_id_number')}")
                            print(f"Login: {item.get('login')}")
                            print(f"Data: {item}")
                            found = True
            except Exception as e:
                print(f"  Error: {e}")
                
        if not found:
            print("❌ Not found in standard endpoints with search 'Shohrux'.")

if __name__ == "__main__":
    asyncio.run(main())
