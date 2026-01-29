import asyncio
import time
from services.hemis_service import HemisService

async def test_hemis_speed():
    print("--- Starting Hemis Connection Test ---")
    start = time.time()
    
    # 1. Test Base URL Connectivity
    print(f"Testing Connectivity to {HemisService.BASE_URL}...")
    try:
        import httpx
        async with httpx.AsyncClient(verify=False) as client:
            resp = await client.get(f"{HemisService.BASE_URL}/gui/version", timeout=5)
            print(f"Version Check: {resp.status_code} (took {time.time() - start:.2f}s)")
    except Exception as e:
        print(f"Version Check FAILED: {e} (took {time.time() - start:.2f}s)")

    # 2. Simulate Login (if we had creds, but we don't know user's creds here).
    # Instead, we'll try to reach the OAuth profiel endpoint which is used in fallback.
    
    print("\nTesting OAuth Profile Endpoint connectivity...")
    oauth_start = time.time()
    try:
        from config import HEMIS_PROFILE_URL
        async with httpx.AsyncClient(verify=False) as client:
             # Just checking if host is reachable, will get 401 without token but that's fine
             resp = await client.get(HEMIS_PROFILE_URL, timeout=5)
             print(f"OAuth Profile Check: {resp.status_code} (took {time.time() - oauth_start:.2f}s)")
    except Exception as e:
         print(f"OAuth Profile Check FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_hemis_speed())
