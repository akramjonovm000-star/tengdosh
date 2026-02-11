import asyncio
import os
import sys
# Manually add project root to path
sys.path.append('/home/user/talabahamkor/talabahamkorbot')

from dotenv import load_dotenv
load_dotenv('/home/user/talabahamkor/talabahamkorbot/.env')
from talabahamkorbot.services.hemis_service import HemisService

async def verify():
    print('--- Testing Partial ID Search ---')
    client = await HemisService.get_client()
    token = os.environ.get('HEMIS_ADMIN_TOKEN')
    url = f'{HemisService.BASE_URL}/data/student-list'
    
    # Use the known ID from previous run: 395261100002
    target_full = "395261100002"
    target_partial = "395261"
    
    # 1. Test Full ID
    print(f'\n1. Search Full ID: "{target_full}"')
    r1 = await HemisService.fetch_with_retry(client, 'GET', url, 
        params={'limit': 5, 'search': target_full}, 
        headers={'Authorization': f'Bearer {token}'})
    print(f'   -> Count: {r1.json().get("data", {}).get("pagination", {}).get("totalCount", 0)}')

    # 2. Test Partial ID
    print(f'\n2. Search Partial ID: "{target_partial}"')
    r2 = await HemisService.fetch_with_retry(client, 'GET', url, 
        params={'limit': 5, 'search': target_partial}, 
        headers={'Authorization': f'Bearer {token}'})
    print(f'   -> Count: {r2.json().get("data", {}).get("pagination", {}).get("totalCount", 0)}')

asyncio.run(verify())
