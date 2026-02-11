import asyncio
import os
import sys
# Manually add project root to path
sys.path.append('/home/user/talabahamkor/talabahamkorbot')

from dotenv import load_dotenv
load_dotenv('/home/user/talabahamkor/talabahamkorbot/.env')
from talabahamkorbot.services.hemis_service import HemisService

async def verify():
    print('--- Testing Student Search by PK ID ---')
    client = await HemisService.get_client()
    token = os.environ.get('HEMIS_ADMIN_TOKEN')
    url = f'{HemisService.BASE_URL}/data/student-list'
    
    # 1. Get a student/ID
    r1 = await HemisService.fetch_with_retry(client, 'GET', url, 
        params={'limit': 1, 'search': "Abdulla"}, 
        headers={'Authorization': f'Bearer {token}'})
    
    target_id = None
    if r1.status_code == 200:
        items = r1.json().get('data', {}).get('items', [])
        if items:
            s = items[0]
            target_id = s.get('id')
            print(f'Found Student: {s.get("full_name")}')
            print(f'  ID (PK): {target_id}')

    if not target_id:
        print('Could not find a student to test with.')
        return

    # 2. Test searching by params={'_id': target_id}
    print(f'\n2. Test _id filter: "{target_id}"')
    r2 = await HemisService.fetch_with_retry(client, 'GET', url, 
        params={'limit': 5, '_id': target_id}, 
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
