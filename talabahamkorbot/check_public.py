import asyncio
from services.hemis_service import HemisService

async def check():
    count = await HemisService.get_public_student_total()
    print("Public Count:", count)

if __name__ == "__main__":
    asyncio.run(check())
