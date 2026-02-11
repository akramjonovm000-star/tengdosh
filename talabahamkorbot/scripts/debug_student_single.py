import asyncio
import os
import sys
# Manually add project root to path
sys.path.append('/home/user/talabahamkor/talabahamkorbot')

from dotenv import load_dotenv
load_dotenv('/home/user/talabahamkor/talabahamkorbot/.env')
from talabahamkorbot.services.hemis_service import HemisService

async def verify():
    print('--- Testing Get Single Student by ID Path ---')
    client = await HemisService.get_client()
    token = os.environ.get('HEMIS_ADMIN_TOKEN')
    
    # 1. Get a student/ID
    r1 = await HemisService.fetch_with_retry(client, 'GET', f'{HemisService.BASE_URL}/data/student-list', 
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

    # 2. Test GET /data/student-list/{id}
    print(f'\n2. Test Path /data/student-list/{target_id}')
    # No params, just path?
    # Or maybe it's generally not supported?
    # Usually HEMIS uses /data/student-info?student_id=...? No.
    
    # Try fetch without params first
    url = f'{HemisService.BASE_URL}/data/student-list'
    
    # Try appending ID to url is unsafe if not sure, but fetch_with_retry takes url.
    # Let's try direct path construction
    detail_url = f'{HemisService.BASE_URL}/data/student-list?_id={target_id}' 
    # Wait, I already tested params={'_id': ...}. 
    # I want to test URL path: /data/student-list/9357
    
    r2 = await client.get(f'{HemisService.BASE_URL}/data/student-list/{target_id}', 
        headers={'Authorization': f'Bearer {token}'})
        
    print(f'   -> Status: {r2.status_code}')
    if r2.status_code == 200:
        print(f'   -> Data: {r2.json()}')
    else:
        print(f'   -> Response: {r2.text[:200]}')

asyncio.run(verify())
