import asyncio
import os
import sys
# Manually add project root to path
sys.path.append('/home/user/talabahamkor/talabahamkorbot')

from dotenv import load_dotenv
load_dotenv('/home/user/talabahamkor/talabahamkorbot/.env')
from talabahamkorbot.services.hemis_service import HemisService

async def verify():
    print('--- Testing Student Search by Login ---')
    client = await HemisService.get_client()
    token = os.environ.get('HEMIS_ADMIN_TOKEN')
    url = f'{HemisService.BASE_URL}/data/student-list'
    
    # 1. Get a student to find their Login
    r1 = await HemisService.fetch_with_retry(client, 'GET', url, 
        params={'limit': 1, 'search': "Abdulla"}, 
        headers={'Authorization': f'Bearer {token}'})
    
    target_login = None
    if r1.status_code == 200:
        items = r1.json().get('data', {}).get('items', [])
        if items:
            s = items[0]
            target_login = s.get('login')
            print(f'Found Student: {s.get("full_name")}')
            print(f'  Login: {target_login}')
    
    if not target_login:
        print('Could not find a student to test with.')
        return

    # 2. Test searching by Login
    print(f'\n2. Search by Login: "{target_login}"')
    r2 = await HemisService.fetch_with_retry(client, 'GET', url, 
        params={'limit': 5, 'search': str(target_login)}, 
        headers={'Authorization': f'Bearer {token}'})
    count2 = r2.json().get('data', {}).get('pagination', {}).get('totalCount', 0)
    print(f'   -> Count: {count2}')


asyncio.run(verify())
