import asyncio
import os
from dotenv import load_dotenv
load_dotenv('/home/user/talabahamkor/talabahamkorbot/.env')
from talabahamkorbot.services.hemis_service import HemisService

async def test():
    token = os.environ.get('HEMIS_ADMIN_TOKEN')
    client = await HemisService.get_client()
    
    url_group = f'{HemisService.BASE_URL}/data/group-list'
    # Get all Sirtqi Level 1 groups
    params = {'limit': 200, '_level': 1, '_education_form': 13}
    resp = await HemisService.fetch_with_retry(client, 'GET', url_group, params=params, headers={'Authorization': f'Bearer {token}'})
    
    if resp.status_code == 200:
        items = resp.json().get('data', {}).get('items', [])
        print(f'Found {len(items)} Sirtqi groups.')
        
        faculties = {}
        for g in items:
            dept = g.get('department', {})
            did = dept.get('id')
            dname = dept.get('name')
            if did not in faculties:
                faculties[did] = {'name': dname, 'count': 0}
            faculties[did]['count'] += 1
            
        print('\nFaculties with Sirtqi groups:')
        for did, info in faculties.items():
            print(f'ID: {did}, Name: {info["name"]}, Count: {info["count"]}')
            
    else:
        print(f'Error: {resp.status_code}')

asyncio.run(test())
