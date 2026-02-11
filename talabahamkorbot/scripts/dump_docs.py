import httpx
import asyncio
import json

async def dump_paths():
    client = httpx.AsyncClient(verify=False, timeout=30.0)
    try:
        resp = await client.get("https://student.jmcu.uz/rest/docs.json")
        if resp.status_code == 200:
            paths = list(resp.json().get("paths", {}).keys())
            paths.sort()
            with open("docs_paths.txt", "w") as f:
                for p in paths:
                    f.write(f"{p}\n")
            print(f"[*] Dumped {len(paths)} paths to docs_paths.txt")
        else:
            print(f"[!] Failed: {resp.status_code}")
    except Exception as e:
        print(f"[!] Error: {e}")
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(dump_paths())
