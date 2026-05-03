"""
HELIOS Backend — Supabase JWT Authentication
Validates Bearer tokens issued by Supabase Auth.
"""

from typing import Optional

from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from cryptography.fernet import Fernet

from backend.config import SUPABASE_JWT_SECRET, SUPABASE_URL, ENCRYPTION_KEY, SESSION_COOKIE_NAME

security = HTTPBearer(auto_error=False)

# ─── Fernet cipher for API key encryption ────────────────────────────────────

_fernet = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None
_SUPABASE_JWT_AUDIENCE = "authenticated"


def _expected_issuer() -> Optional[str]:
    if not SUPABASE_URL:
        return None
    return f"{SUPABASE_URL.rstrip('/')}/auth/v1"


def encrypt_api_key(plaintext: str) -> str:
    """Encrypt an API key for storage in Supabase."""
    if not _fernet:
        raise RuntimeError("ENCRYPTION_KEY not configured")
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_api_key(ciphertext: str) -> str:
    """Decrypt an API key retrieved from Supabase."""
    if not _fernet:
        raise RuntimeError("ENCRYPTION_KEY not configured")
    return _fernet.decrypt(ciphertext.encode()).decode()


# ─── JWT Verification ────────────────────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    FastAPI dependency that extracts and validates the Supabase JWT.
    Returns the user_id (sub claim).
    """
    if not credentials or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = credentials.credentials
    issuer = _expected_issuer()

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=_SUPABASE_JWT_AUDIENCE if issuer else None,
            issuer=issuer,
            options={
                "verify_aud": bool(issuer),
                "verify_iss": bool(issuer),
            },
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not isinstance(payload, dict) or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return payload["sub"]


async def get_current_user_from_session(
    request: Request,
) -> str:
    """
    Require a backend-issued session cookie for normal app routes.

    Bearer tokens are intentionally ignored here so browser routes cannot bypass
    the httpOnly session + CSRF architecture.
    """
    session_service = getattr(request.app.state, "session_service", None)
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if session_service and session_id:
        session = session_service.get_active_session(session_id)
        if session:
            request.state.auth_session = session
            return session["user_id"]

    raise HTTPException(status_code=401, detail="Unauthorized")
