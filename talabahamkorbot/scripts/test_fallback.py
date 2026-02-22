import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.hemis_service import HemisService
from services.university_service import UniversityService

async def main():
    login = "395251101417"
    password = "6161234a"
    base_url = UniversityService.get_api_url(login)
    
    token, error = await HemisService.authenticate(login, password, base_url=base_url)
    if error:
        print(f"Auth failed: {error}")
        return
        
    data = await HemisService.get_student_contract(token, base_url=base_url)
    
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
