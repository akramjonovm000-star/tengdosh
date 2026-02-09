
import asyncio
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

async def test_group_mapping(group_name):
    print(f"\nTesting mapping for group: {group_name}")
    gid = await HemisService.resolve_group_id(group_name)
    print(f"Resolved ID: {gid}")

async def main():
    # Test with the corrected name (with LI)
    await test_group_mapping("25-23 AXBOROT XIZMATI VA JAMOATCHILIK BILAN ALOQALAR (KUNDUZGI) (O‘ZBEK)")
    # Test with the shortened name (without LI) to check prefix fallback
    await test_group_mapping("25-23 AXBOROT XIZMATI VA JAMOATCHIK BILAN ALOQALAR (KUNDUZGI) (O‘ZBEK)")
    # Test another group
    await test_group_mapping("25-117 XORIJIY TIL VA ADABIYOTI (INGLIZ TILI)")

if __name__ == "__main__":
    asyncio.run(main())
