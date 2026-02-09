
import asyncio
import httpx
import json

async def fetch_urls():
    # Try the local university first
    url = "https://student.jmcu.uz/rest/v1/public/university-api-urls"
    
    print(f"Fetching from: {url}")
    
    async with httpx.AsyncClient(verify=False) as client:
        try:
            resp = await client.get(url, timeout=10)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                # Save to file for easy reading
                with open("uni_urls.json", "w") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                
                print("Data saved to uni_urls.json")
                
                # Print summary
                items = data.get("data", [])
                print(f"Total entries: {len(items)}")
                for item in items[:5]:
                    print(f" - {item.get('name')} ({item.get('code')}): {item.get('api_url')}")
            else:
                print(f"Error: {resp.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_urls())
