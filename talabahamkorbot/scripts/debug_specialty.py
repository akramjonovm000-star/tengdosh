import asyncio
import os
from dotenv import load_dotenv
load_dotenv('/home/user/talabahamkor/talabahamkorbot/.env')
from talabahamkorbot.services.hemis_service import HemisService

async def test():
    token = os.environ.get('HEMIS_ADMIN_TOKEN')
    client = await HemisService.get_client()
    
    print('--- 1. Fetching All Specialties ---')
    # Fetch all specialties to find the target one
    url_spec = f'{HemisService.BASE_URL}/data/specialty-list'
    params_spec = {'limit': 500} # Fetch plenty
    resp_s = await HemisService.fetch_with_retry(client, 'GET', url_spec, params=params_spec, headers={'Authorization': f'Bearer {token}'})
    
    target_name = "Axborot xizmati va jamoatchilik bilan aloqalar"
    norm_target = HemisService._normalize_name(target_name)
    print(f'Target: "{target_name}" (Norm: {norm_target})')
    
    found = False
    if resp_s.status_code == 200:
        s_items = resp_s.json().get('data', {}).get('items', [])
        print(f'Total specialties fetched: {len(s_items)}')
        
        for s in s_items:
            s_name = s.get('name')
            s_norm = HemisService._normalize_name(s_name)
            
            # Check for close match
            if norm_target in s_norm or s_norm in norm_target:
                print(f'MATCH FOUND: "{s_name}" (ID: {s.get("id")})')
                found = True
            
            # Also print anything starting with "Axborot"
            if s_name.lower().startswith("axborot"):
                 print(f'Potential Candidate: "{s_name}" (ID: {s.get("id")})')
                 
    else:
        print(f'Error: {resp_s.status_code}')

    if not found:
        print('Target specialty NOT FOUND in the list.')

    print('\n--- 2. Testing resolve_specialty_id ---')
    resolved_id = await HemisService.resolve_specialty_id(target_name)
    print(f'Result for "{target_name}": {resolved_id}')
    
    # Also test valid resolution for "Axborot xizmati va jamoatchilik bilan aloqalar (kunduzgi)" if that exists
    # The user might be selecting a string that includes brackets in some contexts, but here they said the clean name.

asyncio.run(test())
