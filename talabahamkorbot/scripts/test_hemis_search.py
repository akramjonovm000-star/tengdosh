import asyncio
import logging
from services.hemis_service import HemisService
from config import HEMIS_ADMIN_TOKEN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_search_params():
    if not HEMIS_ADMIN_TOKEN:
        print("ERROR: HEMIS_ADMIN_TOKEN is not set.")
        return

    print(f"Testing with Token: {HEMIS_ADMIN_TOKEN[:10]}...")
    
    # Try searching for a specific common name
    search_term = "Aziz" 
    
    # Potential keys to test (Expanded)
    keys_to_test = [
        "search", "_search", "q", "query", 
        "name", "full_name", "firstname", "lastname",
        "student_id_number", "login", "code"
    ]
    
    for key in keys_to_test:
        filters = {key: search_term}
        try:
            items, total = await HemisService.get_admin_student_list(filters, page=1, limit=1)
            # Check if total count is DIFFERENT from the global total (6122)
            print(f"Key: '{key}' -> Total: {total}")
            
            if total > 0 and total < 6000:
                print(f"  >>> MATCH! '{key}' seems to filter results! <<<")
                print(f"  First Item: {items[0].get('full_name') or items[0].get('short_name')}")
            
        except Exception as e:
            print(f"Error testing '{key}': {e}")

if __name__ == "__main__":
    asyncio.run(test_search_params())
