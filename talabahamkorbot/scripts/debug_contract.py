import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.hemis_service import HemisService
from services.university_service import UniversityService

async def main():
    login = "395251101417"
    password = "6161234a"
    base_url = UniversityService.get_api_url(login)
    
    print(f"Testing for login: {login}, base_url: {base_url}")
    
    token, error = await HemisService.authenticate(login, password, base_url=base_url)
    if error:
        print(f"Auth failed: {error}")
        return
        
    print(f"Auth successful. Token: {token[:20]}...")
    
    client = await HemisService.get_client()
    
    # Test /v1/student/contract-list
    url_list = f"{base_url}/student/contract-list"
    resp_list = await HemisService.fetch_with_retry(client, "GET", url_list, headers=HemisService.get_headers(token))
    print(f"Response code for contract-list: {resp_list.status_code}")
    if resp_list.status_code == 200:
        print("Data for contract-list:")
        import json
        print(json.dumps(resp_list.json(), indent=2, ensure_ascii=False))
    
    print("-" * 50)
    
    # Test /v1/student/contract
    url_single = f"{base_url}/student/contract"
    resp_single = await HemisService.fetch_with_retry(client, "GET", url_single, headers=HemisService.get_headers(token))
    print(f"Response code for contract (single): {resp_single.status_code}")
    if resp_single.status_code == 200:
         print("Data for contract (single):")
         print(json.dumps(resp_single.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
