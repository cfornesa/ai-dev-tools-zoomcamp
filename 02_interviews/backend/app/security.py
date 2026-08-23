import hashlib, secrets
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
def hash_password(value): return pwd.hash(value)
def verify_password(value, hashed): return pwd.verify(value, hashed)
def digest(value): return hashlib.sha256(value.encode()).hexdigest()
def token(kind, claims, minutes, secret): return jwt.encode({**claims,"kind":kind,"exp":datetime.now(timezone.utc)+timedelta(minutes=minutes)},secret,algorithm="HS256")
def decode(value, kind, secret):
    data=jwt.decode(value,secret,algorithms=["HS256"])
    if data.get("kind")!=kind: raise ValueError("invalid token")
    return data
def random_token(): return secrets.token_urlsafe(48)
