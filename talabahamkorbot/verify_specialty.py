
import asyncio
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

async def get_count(client, sid):
    url = f"{HemisService.BASE_URL}/data/student-list"
    try:
        r = await client.get(url, headers={"Authorization": f"Bearer {HEMIS_ADMIN_TOKEN}"}, params={"limit": 1, "_specialty": sid})
        if r.status_code == 200:
            return r.json().get("data", {}).get("pagination", {}).get("totalCount", 0)
    except:
        pass
    return 0

async def test_mapping(specialty_name, education_type=None):
    print(f"\nTesting mapping for: {specialty_name} (Type: {education_type})")
    all_specs = await HemisService.get_specialty_list()
    specialty_name_lower = specialty_name.lower()
    
    candidates = []
    clean_req = specialty_name_lower.replace(" ", "")
    for s in all_specs:
        s_name = s.get("name", "").lower()
        clean_s = s_name.replace(" ", "")
        if clean_req == clean_s or clean_req in clean_s or clean_s in clean_req:
            candidates.append(s)
    
    if candidates and education_type:
        type_prefix = "6" if "Bakalavr" in education_type else "7" if "Magistr" in education_type else None
        if type_prefix:
            typed = [c for c in candidates if str(c.get("code", "")).startswith(type_prefix)]
            if typed:
                candidates = typed

    exact = [c for c in candidates if specialty_name_lower == c.get("name", "").lower()]
    if exact:
        candidates = exact
    
    print(f"  Candidates to check: {[c.get('id') for c in candidates]}")
    
    if len(candidates) > 1:
        client = await HemisService.get_client()
        tasks = [get_count(client, c.get("id")) for c in candidates]
        counts = await asyncio.gather(*tasks)
        
        best_id = None
        max_count = -1
        for c, count in zip(candidates, counts):
            print(f"    ID {c.get('id')}: {count} students")
            if count > max_count:
                max_count = count
                best_id = c.get("id")
        
        print(f"  Best ID (by count): {best_id}")
    elif candidates:
        print(f"  Single ID: {candidates[0].get('id')}")

async def main():
    await test_mapping("Axborot xizmati va jamoatchilik bilan aloqalar", "Bakalavr")
    await test_mapping("Jurnalistika (Sport jurnalistikasi)", "Bakalavr")

if __name__ == "__main__":
    asyncio.run(main())
