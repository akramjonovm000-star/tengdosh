import asyncio
import os
from dotenv import load_dotenv
load_dotenv('/home/user/talabahamkor/talabahamkorbot/.env')
from talabahamkorbot.services.hemis_service import HemisService

async def verify():
    print('--- Verifying Context-Aware Specialty Resolution ---')
    spec_name = "Axborot xizmati va jamoatchilik bilan aloqalar"
    
    # 1. Test Regular Context (Jurnalistika = 4)
    # Expecting an ID that belongs to Faculty 4. 
    # Based on previous debug, we don't know the exact ID for Fac 4, but we know 58 is the "global" one.
    # Let's see if it changes or stays same, but mainly valid ID.
    id_fac4 = await HemisService.resolve_specialty_id(spec_name, faculty_id=4)
    print(f'Context: Faculty 4 -> ID: {id_fac4}')
    
    # Check dept of this ID
    if id_fac4:
        client = await HemisService.get_client()
        token = os.environ.get('HEMIS_ADMIN_TOKEN')
        r = await HemisService.fetch_with_retry(client, 'GET', f'{HemisService.BASE_URL}/data/specialty-list', params={'_id': id_fac4}, headers={'Authorization': f'Bearer {token}'})
        if r.status_code == 200:
            items = r.json().get('data', {}).get('items', [])
            if items:
                print(f'  Dept of ID {id_fac4}: {items[0].get("department", {}).get("name")} (ID: {items[0].get("department", {}).get("id")})')

    # 2. Test Sirtqi Context (Form 13)
    # Expecting ID from Dept 35
    id_sirtqi = await HemisService.resolve_specialty_id(spec_name, education_form="Sirtqi")
    print(f'Context: Form Sirtqi -> ID: {id_sirtqi}')

    if id_sirtqi:
        client = await HemisService.get_client()
        token = os.environ.get('HEMIS_ADMIN_TOKEN')
        r = await HemisService.fetch_with_retry(client, 'GET', f'{HemisService.BASE_URL}/data/specialty-list', params={'_id': id_sirtqi}, headers={'Authorization': f'Bearer {token}'})
        if r.status_code == 200:
            items = r.json().get('data', {}).get('items', [])
            if items:
                print(f'  Dept of ID {id_sirtqi}: {items[0].get("department", {}).get("name")} (ID: {items[0].get("department", {}).get("id")})')

asyncio.run(verify())
