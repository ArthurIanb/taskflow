from pwdlib import PasswordHash
from app.config import settings
from datetime import datetime, timedelta, timezone
import jwt

password_hash = PasswordHash.recommended()

def hash_password(pwd: str) -> str:
    return password_hash.hash(pwd)

def verify_password(pwd: str, hashed_pwd: str) -> bool:
    return password_hash.verify(pwd, hashed_pwd)

def create_access_token(data: dict, expire: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)) -> str:
    payload = data.copy()
    payload.update({"exp": datetime.now(timezone.utc) + expire})
    return jwt.encode(
        payload=payload, 
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )