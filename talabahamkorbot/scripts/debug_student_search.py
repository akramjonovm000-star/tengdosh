import asyncio
import os
import sys
# Manually add project root to path
sys.path.append('/home/user/talabahamkor/talabahamkorbot')

from dotenv import load_dotenv
load_dotenv('/home/user/talabahamkor/talabahamkorbot/.env')
from talabahamkorbot.services.hemis_service import HemisService

async def verify():
    print('--- Testing Student Search Params ---')
    # Use a common name likely to exist
    query = "Abdulla" 
    
    client = await HemisService.get_client()
    token = os.environ.get('HEMIS_ADMIN_TOKEN')
    url = f'{HemisService.BASE_URL}/data/student-list'
    
    # 1. Test 'search'
    print(f'\n1. Testing params={{"search": "{query}"}}')
    r1 = await HemisService.fetch_with_retry(client, 'GET', url, 
        params={'limit': 5, 'search': query}, 
        headers={'Authorization': f'Bearer {token}'})
    
    if r1.status_code == 200:
        data = r1.json().get('data', {})
        count = data.get('pagination', {}).get('totalCount', 0)
        items = data.get('items', [])
        print(f'   -> Count: {count}')
        if items:
            print(f'   -> First: {items[0].get("full_name")}')
    else:
        print(f'   -> Error: {r1.status_code}')

    # 2. Test '_search'
    print(f'\n2. Testing params={{"_search": "{query}"}}')
    r2 = await HemisService.fetch_with_retry(client, 'GET', url, 
        params={'limit': 5, '_search': query}, 
        headers={'Authorization': f'Bearer {token}'})
    
    if r2.status_code == 200:
        data = r2.json().get('data', {})
        count = data.get('pagination', {}).get('totalCount', 0)
        items = data.get('items', [])
        print(f'   -> Count: {count}')
        if items:
            print(f'   -> First: {items[0].get("full_name")}')
    else:
        print(f'   -> Error: {r2.status_code}')

asyncio.run(verify())
