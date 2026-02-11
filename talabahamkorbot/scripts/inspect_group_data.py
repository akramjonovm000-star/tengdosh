import asyncio
import logging
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def inspect_groups():
    if not HEMIS_ADMIN_TOKEN:
        print("ERROR: HEMIS_ADMIN_TOKEN is not set.")
        return

    print("Fetching groups to inspect structure...")
    # Fetch a few groups
    try:
        groups = await HemisService.get_group_list()
        if groups:
            print(f"Found {len(groups)} groups.")
            first = groups[0]
            print("First Group Keys:", first.keys())
            print("Specialty Data:", first.get("specialty"))
            print("Department Data:", first.get("department"))
            print("Edu Form:", first.get("educationForm"))
        else:
            print("No groups found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_groups())
