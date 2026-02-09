import asyncio
import os
from dotenv import load_dotenv
load_dotenv('/home/user/talabahamkor/talabahamkorbot/.env')
from talabahamkorbot.services.hemis_service import HemisService

async def test():
    token = os.environ.get('HEMIS_ADMIN_TOKEN')
    client = await HemisService.get_client()
    
    print('--- 1. Specialties for Faculty 4 (Jurnalistika) ---')
    url_spec = f'{HemisService.BASE_URL}/data/specialty-list'
    params_spec = {'limit': 200, '_department': 4}
    resp_s = await HemisService.fetch_with_retry(client, 'GET', url_spec, params=params_spec, headers={'Authorization': f'Bearer {token}'})
    spec_names_4 = []
    if resp_s.status_code == 200:
        s_items = resp_s.json().get('data', {}).get('items', [])
        for s in s_items:
            spec_names_4.append(s.get('name'))
            print(f"- {s.get('name')} (ID: {s.get('id')})")
    
    print('\n--- 2. Specialties for Dept 35 (Sirtqi Groups) ---')
    # We get specialties FROM the groups in Dept 35, or list specialties linked to Dept 35
    # Let's list specialties linked to Dept 35 first
    params_spec_35 = {'limit': 200, '_department': 35}
    resp_s35 = await HemisService.fetch_with_retry(client, 'GET', url_spec, params=params_spec_35, headers={'Authorization': f'Bearer {token}'})
    
    if resp_s35.status_code == 200:
        s35_items = resp_s35.json().get('data', {}).get('items', [])
        print(f'Found {len(s35_items)} specialties in Dept 35.')
        for s in s35_items:
            print(f"- {s.get('name')} (ID: {s.get('id')})")
            # Check partial match
            for n4 in spec_names_4:
                if n4 in s.get('name') or s.get('name') in n4:
                    print(f"  >>> POSSIBLE MATCH: '{n4}' <=> '{s.get('name')}'")

asyncio.run(test())
