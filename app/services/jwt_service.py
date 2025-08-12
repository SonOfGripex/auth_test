import jwt
from datetime import datetime, timedelta, UTC
from typing import List
from app.config import settings
import hashlib

def create_access_token(user_uuid: str, roles: List[str], permissions: List[str], user_email: str, exchanger_uuid: str = None):
    payload = {
        "uuid": user_uuid,
        "roles": roles,
        "email": user_email,
        "permissions": permissions,
        "exp": datetime.now(UTC) + timedelta(seconds=settings.JWT_EXPIRE_SECONDS),
        "type": "access"
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(user_uuid: str):
    payload = {
        "uuid": user_uuid,
        "exp": datetime.utcnow() + timedelta(days=30),
        "type": "refresh"
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def encode_token(payload: dict):
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str):
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()