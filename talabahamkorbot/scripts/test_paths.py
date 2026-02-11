import httpx
import asyncio

async def test_path(client, base, path):
    url = f"{base}{path}"
    try:
        resp = await client.post(url, json={"login": "test", "password": "test"})
        print(f"POST {url} -> {resp.status_code}")
    except Exception as e:
        print(f"POST {url} -> FAILED: {e}")

async def main():
    base = "http://127.0.0.1:8001"
    paths = [
        "/api/v1/auth/hemis",
        "/api/v1/auth/hemis/",
        "/auth/hemis",
        "/auth/hemis/",
        "/hemis",
        "/hemis/",
        "/v1/auth/hemis",
        "/api/auth/hemis"
    ]
    
    headers = {"Host": "tengdosh.uzjoku.uz"}
    async with httpx.AsyncClient(timeout=5.0, headers=headers) as client:
        for p in paths:
            await test_path(client, base, p)

if __name__ == "__main__":
    asyncio.run(main())
