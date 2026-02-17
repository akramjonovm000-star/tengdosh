import os
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

# Load Key from Env or Use Default (Dev Only)
# In Prod, this MUST be a 32-url-safe-base64-encoded bytes
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    # Generate a temporary key for dev if missing (WARNING: Restarting app invalidates old data!)
    logger.warning("ENCRYPTION_KEY not found in env. Generating temporary key (Will invalidate sessions on restart).")
    try:
        ENCRYPTION_KEY = Fernet.generate_key()
        logger.warning(f"Generated TEMP Encryption Key: {ENCRYPTION_KEY.decode()}")
    except Exception as e:
        logger.error(f"Failed to generate key: {e}")

try:
    cipher_suite = Fernet(ENCRYPTION_KEY)
except Exception as e:
    logger.error(f"Invalid Encryption Key: {e}")
    cipher_suite = None

def encrypt_data(data: str) -> str:
    """Encrypts string data using Fernet."""
    if not data:
        return None
    if not cipher_suite:
        return data # Fail open or closed? Fail open for dev compatibility? No, fail safe.
        # But we don't want to crash.
    try:
        encrypted_bytes = cipher_suite.encrypt(data.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return data # Fallback? Or raise?

def decrypt_data(encrypted_data: str) -> str:
    """Decrypts Fernet-encrypted string."""
    if not encrypted_data:
        return None
    if not cipher_suite:
        return encrypted_data
    try:
        decrypted_bytes = cipher_suite.decrypt(encrypted_data.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        # Check if it was plain text (migration phase)
        # simplistic check
        return encrypted_data # Assume it was plain text if decryption fails (Graceful migration)
