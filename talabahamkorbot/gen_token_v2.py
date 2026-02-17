import sys
import os
import jwt
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Force load env to be sure
load_dotenv("/home/user/talabahamkor/talabahamkorbot/.env")

SECRET_KEY = os.getenv("SECRET_KEY", "talabahamkor_insecure_dev_key_PLEASE_CHANGE_IN_PROD")
ALGORITHM = "HS256"
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

def create_test_token():
    print(f"SECRET_KEY: {SECRET_KEY[:5]}...")
    print(f"ENCRYPTION_KEY: {ENCRYPTION_KEY[:5]}..." if ENCRYPTION_KEY else "None")

    if not ENCRYPTION_KEY:
        print("Error: ENCRYPTION_KEY not found override")
        return

    # Encrypt a dummy hemis token
    cipher = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
    encrypted_hemis = cipher.encrypt(b"dummy_hemis_token_verified").decode()

    # Create JWT
    to_encode = {
        "sub": "395251101397", 
        "type": "student",
        "id": 730, # Real ID
        "hemis_token": encrypted_hemis,
        "exp": datetime.utcnow() + timedelta(minutes=60)
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    print(encoded_jwt)

if __name__ == "__main__":
    create_test_token()
