
from datetime import datetime, timedelta
from typing import Optional, Union
import os
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# SECURITY CONFIG
# In production, this MUST be set via environment variable
SECRET_KEY = os.environ.get("SECRET_KEY", "talabahamkor_insecure_dev_key_PLEASE_CHANGE_IN_PROD")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def hash_user_agent(user_agent: str) -> str:
    """Creates a short hash of the User-Agent string for binding."""
    import hashlib
    if not user_agent:
        return "unknown"
    return hashlib.md5(user_agent.encode()).hexdigest()[:8]

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, user_agent: str = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    if user_agent:
        to_encode.update({"ua": hash_user_agent(user_agent)})
        
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """
    Verifies JWT token.
    Returns payload if valid, None if invalid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# RATE LIMITING
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize Limiter with global default limits
# This object is imported by main.py and other routers
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
