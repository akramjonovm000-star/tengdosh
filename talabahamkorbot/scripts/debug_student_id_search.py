import asyncio
import os
import sys
# Manually add project root to path
sys.path.append('/home/user/talabahamkor/talabahamkorbot')

from dotenv import load_dotenv
load_dotenv('/home/user/talabahamkor/talabahamkorbot/.env')
from talabahamkorbot.services.hemis_service import HemisService

async def verify():
    print('--- Testing Student Search by ID ---')
    client = await HemisService.get_client()
    token = os.environ.get('HEMIS_ADMIN_TOKEN')
    url = f'{HemisService.BASE_URL}/data/student-list'
    
    # 1. Get a student to find their ID
    r1 = await HemisService.fetch_with_retry(client, 'GET', url, 
        params={'limit': 1, 'search': "Abdulla"}, 
        headers={'Authorization': f'Bearer {token}'})
    
    target_id = None
    target_hemis_id = None
    if r1.status_code == 200:
        items = r1.json().get('data', {}).get('items', [])
        if items:
            s = items[0]
            target_id = s.get('id')
            target_hemis_id = s.get('student_id_number') # or whatever field holds the visible ID
            print(f'Found Student: {s.get("full_name")}')
            print(f'  ID (PK): {target_id}')
            print(f'  Hemis ID Number: {target_hemis_id}')
            # Print all keys to find the user-facing ID
            # print(s.keys())
    
    if not target_id:
        print('Could not find a student to test with.')
        return

    # 2. Test searching by ID (PK)
    print(f'\n2. Search by ID (PK): "{target_id}"')
    r2 = await HemisService.fetch_with_retry(client, 'GET', url, 
        params={'limit': 5, 'search': str(target_id)}, 
        headers={'Authorization': f'Bearer {token}'})
    count2 = r2.json().get('data', {}).get('pagination', {}).get('totalCount', 0)
    print(f'   -> Count: {count2}')

    # 3. Test searching by Hemis ID Number (if different)
    if target_hemis_id and str(target_hemis_id) != str(target_id):
        print(f'\n3. Search by Hemis ID Number: "{target_hemis_id}"')
        r3 = await HemisService.fetch_with_retry(client, 'GET', url, 
            params={'limit': 5, 'search': str(target_hemis_id)}, 
            headers={'Authorization': f'Bearer {token}'})
        count3 = r3.json().get('data', {}).get('pagination', {}).get('totalCount', 0)
        print(f'   -> Count: {count3}')
    
    # 4. Try _search param for ID?
    print(f'\n4. Testing _search with ID: "{target_id}"')
    r4 = await HemisService.fetch_with_retry(client, 'GET', url, 
        params={'limit': 5, '_search': str(target_id)}, 
        headers={'Authorization': f'Bearer {token}'})
    count4 = r4.json().get('data', {}).get('pagination', {}).get('totalCount', 0)
    print(f'   -> Count: {count4}')

asyncio.run(verify())
