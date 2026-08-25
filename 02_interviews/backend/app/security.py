import hashlib, secrets, json, urllib.parse, urllib.request
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
def session_digest(value): return digest(value)
def csrf_token(): return secrets.token_urlsafe(32)
_used_recaptcha=set()
def verify_recaptcha(value,action,settings,remote_ip=None):
    if settings.recaptcha_mode=="mock":
        if not value:return {"decision":"allow","action":action,"mock":True}
        if not value.startswith("mock:") or digest(value) in _used_recaptcha:return {"decision":"deny","reason":"invalid_or_replayed"}
        _used_recaptcha.add(digest(value)); band=value.split(":",2)[1] if len(value.split(":",2))>1 else "deny"
        return {"decision":band if band in {"allow","step_up","deny"} else "deny","action":action,"mock":True}
    if settings.recaptcha_mode!="real" or not settings.recaptcha_secret or not value:return {"decision":"unavailable","reason":"provider_not_configured"}
    try:
        payload=urllib.parse.urlencode({"secret":settings.recaptcha_secret,"response":value,**({"remoteip":remote_ip} if remote_ip else {})}).encode()
        with urllib.request.urlopen(urllib.request.Request("https://www.google.com/recaptcha/api/siteverify",data=payload),timeout=3) as response: result=json.loads(response.read())
    except Exception:return {"decision":"unavailable","reason":"provider_unavailable"}
    if not result.get("success") or result.get("action")!=action or digest(value) in _used_recaptcha:return {"decision":"deny","reason":"invalid_or_replayed"}
    hostnames={x.strip().lower() for x in settings.recaptcha_allowed_hostnames.split(",") if x.strip()}
    if hostnames and str(result.get("hostname","")).lower() not in hostnames:return {"decision":"deny","reason":"hostname_mismatch"}
    try:
        challenge=datetime.fromisoformat(str(result.get("challenge_ts")).replace("Z","+00:00")); age=(datetime.now(timezone.utc)-challenge).total_seconds()
        if age<0 or age>settings.recaptcha_max_age_seconds:return {"decision":"deny","reason":"stale"}
    except Exception:return {"decision":"deny","reason":"missing_timestamp"}
    _used_recaptcha.add(digest(value)); score=float(result.get("score",0)); decision="allow" if score>=settings.recaptcha_allow_score else "step_up" if score>=settings.recaptcha_stepup_score else "deny"
    return {"decision":decision,"action":action,"score_band":decision}
def verify_google_credential(credential,settings):
    if not credential or not isinstance(credential,str): raise ValueError("invalid provider credential")
    if settings.google_provider_mode=="mock":
        parts=credential.split(":",3)
        if len(parts)!=4 or parts[0]!="mock" or not parts[1] or "@" not in parts[2] or parts[3]!="verified": raise ValueError("invalid provider credential")
        return {"sub":parts[1],"email":parts[2].lower(),"email_verified":True}
    if settings.google_provider_mode!="real" or not settings.google_public_key or not settings.google_client_id: raise ValueError("provider unavailable")
    claims=jwt.decode(credential,settings.google_public_key,algorithms=["RS256"],audience=settings.google_client_id,issuer=[settings.google_issuer,"accounts.google.com"])
    if not claims.get("sub") or not claims.get("email") or claims.get("email_verified") is not True: raise ValueError("invalid provider claims")
    return claims
