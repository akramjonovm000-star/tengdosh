import asyncio
import os
from dotenv import load_dotenv
load_dotenv('/home/user/talabahamkor/talabahamkorbot/.env')
from talabahamkorbot.services.hemis_service import HemisService

async def test():
    token = os.environ.get('HEMIS_ADMIN_TOKEN')
    client = await HemisService.get_client()
    
    print('--- 1. Fetching Specialties for Faculty 4 (Jurnalistika) ---')
    url_spec = f'{HemisService.BASE_URL}/data/specialty-list'
    # Fetch all specialties for Faculty 4
    params_spec = {'limit': 200, '_department': 4}
    resp_s = await HemisService.fetch_with_retry(client, 'GET', url_spec, params=params_spec, headers={'Authorization': f'Bearer {token}'})
    spec_ids_4 = set()
    if resp_s.status_code == 200:
        s_items = resp_s.json().get('data', {}).get('items', [])
        print(f'Found {len(s_items)} specialties in Faculty 4.')
        for s in s_items:
            spec_ids_4.add(s.get('id'))
    
    if not spec_ids_4:
        print('No specialties found for Faculty 4. Exiting.')
        return

    print('\n--- 2. Fetching Sirtqi Groups (Dept 35) ---')
    url_group = f'{HemisService.BASE_URL}/data/group-list'
    params_g = {'limit': 200, '_department': 35, '_education_form': 13}
    resp_g = await HemisService.fetch_with_retry(client, 'GET', url_group, params=params_g, headers={'Authorization': f'Bearer {token}'})
    
    matches = 0
    if resp_g.status_code == 200:
        g_items = resp_g.json().get('data', {}).get('items', [])
        print(f'Found {len(g_items)} Sirtqi groups in Dept 35.')
        
        for g in g_items:
            sid = g.get('specialty', {}).get('id')
            if sid in spec_ids_4:
                print(f'MATCH: Group {g.get("name")} (ID: {g.get("id")}) has Specialty {sid} (Belongs to Faculty 4)')
                matches += 1
            
        print(f'\nTotal Matches: {matches}')
    else:
        print(f'Error fetching groups: {resp_g.status_code}')

asyncio.run(test())
