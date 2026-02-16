from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.rsa_manager import RSAManager

router = APIRouter(prefix="/security", tags=["Security"])

class PublicKeyResponse(BaseModel):
    public_key: str
    algorithm: str = "RSA-OAEP-SHA256"

@router.get("/public-key", response_model=PublicKeyResponse)
async def get_public_key():
    """
    Returns the Server's RSA Public Key.
    Clients should use this to encrypt sensitive credentials (password) before sending.
    """
    try:
        pem = RSAManager.get_public_key_pem()
        return {"public_key": pem}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SecurePayload(BaseModel):
    encrypted_data: str # Base64

@router.post("/debug/decrypt")
async def debug_decrypt(payload: SecurePayload):
    """
    Debug endpoint to test RSA encryption from client.
    """
    decrypted = RSAManager.decrypt_data(payload.encrypted_data)
    if decrypted is None:
       return {"success": False, "error": "Decryption failed"}
    return {"success": True, "decrypted_snippet": decrypted[:5] + "***"}
