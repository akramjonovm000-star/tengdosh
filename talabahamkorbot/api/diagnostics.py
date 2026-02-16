from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.string_formatter import StringFormatter

router = APIRouter(prefix="/diagnostics", tags=["System"])

class DiagnosticsResponse(BaseModel):
    format_key: str
    algorithm: str = "RSA-OAEP-SHA256"

@router.get("/config", response_model=DiagnosticsResponse)
async def get_system_config():
    """
    Returns the System Formatting Key.
    """
    try:
        pem = StringFormatter.get_public_key_pem()
        return {"format_key": pem}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DiagnosticPayload(BaseModel):
    data: str # Base64

@router.post("/test/format")
async def test_format(payload: DiagnosticPayload):
    """
    Debug endpoint to test formatter.
    """
    decrypted = StringFormatter.decrypt_data(payload.data)
    if decrypted is None:
       return {"success": False, "error": "Formatting failed"}
    return {"success": True, "snippet": decrypted[:5] + "***"}
