import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import (
    HEMIS_CLIENT_ID, HEMIS_REDIRECT_URL,
    HEMIS_STAFF_CLIENT_ID, HEMIS_STAFF_REDIRECT_URL,
    HEMIS_AUTH_URL, HEMIS_TOKEN_URL, HEMIS_STAFF_CLIENT_SECRET
)
from services.hemis_service import HemisService

def debug_oauth():
    print("--- OAuth Configuration Debug ---")
    print(f"HEMIS_AUTH_URL: {HEMIS_AUTH_URL}")
    print(f"HEMIS_TOKEN_URL: {HEMIS_TOKEN_URL}")
    print("-" * 30)
    print(f"STUDENT Client ID: {HEMIS_CLIENT_ID}")
    print(f"STUDENT Redirect: {HEMIS_REDIRECT_URL}")
    print("-" * 30)
    print(f"STAFF Client ID: {HEMIS_STAFF_CLIENT_ID}")
    print(f"STAFF Redirect: {HEMIS_STAFF_REDIRECT_URL}")
    print(f"STAFF Secret Present: {bool(HEMIS_STAFF_CLIENT_SECRET)}")
    if HEMIS_STAFF_CLIENT_SECRET:
        print(f"STAFF Secret Length: {len(HEMIS_STAFF_CLIENT_SECRET)}")
    
    print("-" * 30)
    print("Generating URLs...")
    
    student_url = HemisService.generate_auth_url(role="student")
    print(f"Student URL: {student_url}")
    
    staff_url = HemisService.generate_auth_url(role="staff")
    print(f"Staff URL:   {staff_url}")

if __name__ == "__main__":
    debug_oauth()
