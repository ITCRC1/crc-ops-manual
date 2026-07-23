import base64, hashlib, hmac, json, os, time
from urllib.parse import quote
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

SSO_SECRET = os.environ["SSO_SECRET"].encode()   # MISMO valor que en la intranet
BASE = "https://apps.thecostaricacollection.com"
PORTAL_REFRESH = f"{BASE}/api/sso/refresh"
PORTAL_LOGIN = f"{BASE}/login"
COOKIE_NAME = "crc_sso"
PUBLIC_PREFIXES = ("/api/salud", "/docs", "/redoc", "/openapi.json")

def _b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def verify_sso_token(token):
    if not token or token.count(".") != 2:
        return None
    h, p, sig = token.split(".")
    expected = hmac.new(SSO_SECRET, f"{h}.{p}".encode(), hashlib.sha256).digest()
    try:
        got = _b64url_decode(sig)
    except Exception:
        return None
    if not hmac.compare_digest(expected, got):
        return None
    try:
        payload = json.loads(_b64url_decode(p))
    except Exception:
        return None
    if not isinstance(payload.get("exp"), (int, float)) or payload["exp"] < time.time():
        return None
    return payload

class SsoGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(pre) for pre in PUBLIC_PREFIXES):
            return await call_next(request)
        claims = verify_sso_token(request.cookies.get(COOKIE_NAME))
        if claims is None:
            if "text/html" in request.headers.get("accept", ""):
                if request.query_params.get("_sso") == "1":
                    return RedirectResponse(f"{PORTAL_LOGIN}?next={quote(str(request.url), safe='')}", status_code=307)
                sep = "&" if request.url.query else "?"
                back = quote(f"{request.url}{sep}_sso=1", safe="")
                return RedirectResponse(f"{PORTAL_REFRESH}?next={back}", status_code=307)
            return JSONResponse({"detail": "No autenticado"}, status_code=401)
        request.state.user = {"id": claims["sub"], "email": claims["email"], "role": claims.get("role", "")}
        return await call_next(request)
