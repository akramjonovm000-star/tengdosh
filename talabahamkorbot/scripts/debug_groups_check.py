import asyncio
import os
import sys
# Manually add project root to path
sys.path.append('/home/user/talabahamkor/talabahamkorbot')

from dotenv import load_dotenv
load_dotenv('/home/user/talabahamkor/talabahamkorbot/.env')
from talabahamkorbot.services.hemis_service import HemisService

async def verify():
    print('--- Checking Groups for Specialty 58 ---')
    spec_id = 58
    
    # Check in Dept 4 (Jurnalistika)
    client = await HemisService.get_client()
    token = os.environ.get('HEMIS_ADMIN_TOKEN')
    
    print(f'1. Checking Dept 4 (Jurnalistika), Spec {spec_id}, Form 13 (Sirtqi)')
    r4 = await HemisService.fetch_with_retry(client, 'GET', f'{HemisService.BASE_URL}/data/group-list', 
        params={'limit': 1, '_department': 4, '_specialty': spec_id, '_education_form': 13}, 
        headers={'Authorization': f'Bearer {token}'})
    count4 = r4.json().get('data', {}).get('pagination', {}).get('totalCount', 0)
    print(f'   -> Count: {count4}')

    print(f'2. Checking Dept 35 (Sirtqi Section), Spec {spec_id}, Form 13 (Sirtqi)')
    r35 = await HemisService.fetch_with_retry(client, 'GET', f'{HemisService.BASE_URL}/data/group-list', 
        params={'limit': 1, '_department': 35, '_specialty': spec_id, '_education_form': 13}, 
        headers={'Authorization': f'Bearer {token}'})
    count35 = r35.json().get('data', {}).get('pagination', {}).get('totalCount', 0)
    print(f'   -> Count: {count35}')
    
    # Also check ID 33 which was also Dept 35 in candidates
    spec_id2 = 33
    print(f'3. Checking Dept 35, Spec {spec_id2}, Form 13')
    r33 = await HemisService.fetch_with_retry(client, 'GET', f'{HemisService.BASE_URL}/data/group-list', 
        params={'limit': 1, '_department': 35, '_specialty': spec_id2, '_education_form': 13}, 
        headers={'Authorization': f'Bearer {token}'})
    count33 = r33.json().get('data', {}).get('pagination', {}).get('totalCount', 0)
    print(f'   -> Count: {count33}')

asyncio.run(verify())
