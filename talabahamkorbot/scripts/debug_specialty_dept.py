import asyncio
import os
from dotenv import load_dotenv
load_dotenv('/home/user/talabahamkor/talabahamkorbot/.env')
from talabahamkorbot.services.hemis_service import HemisService

async def test():
    token = os.environ.get('HEMIS_ADMIN_TOKEN')
    client = await HemisService.get_client()
    
    print('--- Check Specialty Department Info ---')
    url_spec = f'{HemisService.BASE_URL}/data/specialty-list'
    params_spec = {'limit': 10} 
    resp_s = await HemisService.fetch_with_retry(client, 'GET', url_spec, params=params_spec, headers={'Authorization': f'Bearer {token}'})
    
    if resp_s.status_code == 200:
        s_items = resp_s.json().get('data', {}).get('items', [])
        if s_items:
            s = s_items[0]
            print(f'Sample Specialty: {s.get("name")}')
            print(f'Department key exists: {"department" in s}')
            print(f'Department data: {s.get("department")}')
        else:
            print('No specialties found.')
    else:
        print(f'Error: {resp_s.status_code}')

asyncio.run(test())
