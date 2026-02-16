import os
import logging
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

KEYS_DIR = "keys"
PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, "private.pem")
PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, "public.pem")

class RSAManager:
    _private_key = None
    _public_key = None

    @classmethod
    def ensure_keys_exist(cls):
        """Generates RSA keys if they don't exist."""
        if not os.path.exists(KEYS_DIR):
            os.makedirs(KEYS_DIR)
            
        if not os.path.exists(PRIVATE_KEY_PATH) or not os.path.exists(PUBLIC_KEY_PATH):
            logger.info("Generating new RSA Key Pair...")
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Save Private
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            with open(PRIVATE_KEY_PATH, 'wb') as f:
                f.write(pem)
                
            # Save Public
            public_key = private_key.public_key()
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            with open(PUBLIC_KEY_PATH, 'wb') as f:
                f.write(pem)
            logger.info("RSA Keys generated and saved.")

    @classmethod
    def get_public_key_pem(cls) -> str:
        """Returns Public Key in PEM format (string)."""
        cls.ensure_keys_exist()
        with open(PUBLIC_KEY_PATH, 'rb') as f:
            return f.read().decode('utf-8')

    @classmethod
    def decrypt_data(cls, encrypted_b64: str) -> str:
        """Decrypts base64 encoded RSA encrypted string."""
        import base64
        cls.ensure_keys_exist()
        
        # Load Private Key if needed
        if cls._private_key is None:
            with open(PRIVATE_KEY_PATH, "rb") as key_file:
                cls._private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_b64)
            original_message = cls._private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return original_message.decode('utf-8')
        except Exception as e:
            logger.error(f"RSA Decryption failed: {e}")
            return None
