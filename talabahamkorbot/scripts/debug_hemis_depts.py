
import asyncio
import httpx
import os
import sys

# Add path
sys.path.append(os.getcwd())

from config import HEMIS_ADMIN_TOKEN

async def main():
    if not HEMIS_ADMIN_TOKEN:
        print("No Admin Token")
        return

    url = "https://student.jmcu.uz/rest/v1/data/department-list"
    headers = {"Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}"}
    
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.get(url, headers=headers, params={"limit": 300})
        if resp.status_code == 200:
            data = resp.json().get("data", {}).get("items", [])
            print("HEMIS Departments:")
            for d in sorted(data, key=lambda x: x.get('id', 0)):
                print(f"ID: {d.get('id')}, Name: {d.get('name')}, Type: {d.get('structureType', {}).get('name')}")
        else:
            print(f"Error: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    asyncio.run(main())
