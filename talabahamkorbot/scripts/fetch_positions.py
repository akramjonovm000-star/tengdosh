import httpx
import asyncio
import json

BASE_URL = "https://student.jmcu.uz/rest/v1"

async def fetch_positions():
    async with httpx.AsyncClient() as client:
        print(f"Connecting to {BASE_URL}/data/employee-positions ...")
        try:
            # Try 1: Open Data Endpoint
            response = await client.get(f"{BASE_URL}/data/employee-positions", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", [])
                print(f"Successfully fetched {len(items)} positions.")
                
                # Save to file for inspection
                with open("positions_dump.json", "w", encoding="utf-8") as f:
                    json.dump(items, f, indent=2, ensure_ascii=False)
                
                # Print first 20 names
                print("--- Top 20 Positions ---")
                for item in items[:20]:
                    print(f"- {item.get('name')}")
            else:
                print(f"Failed to fetch public positions: {response.status_code}")
                # Try 2: Alternative endpoint
                print("Trying /public/employee-positions ...")
                response = await client.get(f"{BASE_URL}/public/employee-positions", timeout=10)
                if response.status_code == 200:
                     print("Found at /public !")
                     print(response.json())
                else:
                    print("Public endpoint also failed.")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_positions())
