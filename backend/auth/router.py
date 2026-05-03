import base64
import hashlib
import secrets
from typing import Any
from urllib.parse import quote, unquote, urlencode

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.config import CORS_ORIGINS, SUPABASE_URL
from backend.auth.session_service import SessionCookieSettings

router = APIRouter()

OAUTH_STATE_COOKIE = "helios_oauth_state"
OAUTH_VERIFIER_COOKIE = "helios_oauth_verifier"
OAUTH_REDIRECT_COOKIE = "helios_oauth_redirect"
OAUTH_ORIGIN_COOKIE = "helios_oauth_origin"
OAUTH_COOKIE_MAX_AGE_SECONDS = 600
OAUTH_PROVIDERS = {"google"}


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3)
    password: str = Field(min_length=8)


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3)
    password: str = Field(min_length=8)


def _set_session_cookie(response: Response, session_id: str) -> None:
    settings = SessionCookieSettings.from_config()
    response.set_cookie(
        key=settings.cookie_name,
        value=session_id,
        httponly=settings.http_only,
        secure=settings.secure,
        samesite=settings.same_site,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    settings = SessionCookieSettings.from_config()
    response.delete_cookie(
        key=settings.cookie_name,
        path="/",
        samesite=settings.same_site,
    )


def _set_oauth_cookie(response: Response, key: str, value: str) -> None:
    settings = SessionCookieSettings.from_config()
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=settings.secure,
        samesite=settings.same_site,
        path="/",
        max_age=OAUTH_COOKIE_MAX_AGE_SECONDS,
    )


def _clear_oauth_cookies(response: Response) -> None:
    settings = SessionCookieSettings.from_config()
    for key in (
        OAUTH_STATE_COOKIE,
        OAUTH_VERIFIER_COOKIE,
        OAUTH_REDIRECT_COOKIE,
        OAUTH_ORIGIN_COOKIE,
    ):
        response.delete_cookie(key=key, path="/", samesite=settings.same_site)


def _serialize_user(session_or_user: dict[str, Any] | Any) -> dict[str, Any]:
    if isinstance(session_or_user, dict):
        return {
            "id": session_or_user["user_id"],
            "email": session_or_user.get("email_snapshot"),
        }
    return {
        "id": session_or_user.id,
        "email": getattr(session_or_user, "email", None),
    }


def _ensure_public_user_row(supabase, user_id: str) -> None:
    supabase.table("users").upsert({"id": user_id}, on_conflict="id").execute()


def _safe_app_path(path: str | None) -> str:
    if not path or not path.startswith("/") or path.startswith("//"):
        return "/"
    return path


def _encode_cookie_value(value: str) -> str:
    return quote(value, safe="")


def _decode_cookie_value(value: str | None) -> str | None:
    return unquote(value) if value else None


def _safe_return_origin(origin: str | None) -> str:
    allowed = {item.strip().rstrip("/") for item in CORS_ORIGINS if item.strip()}
    candidate = (origin or "").strip().rstrip("/")
    if candidate in allowed:
        return candidate
    return next(iter(allowed), "http://localhost:5173")


def _generate_oauth_state() -> str:
    return secrets.token_urlsafe(32)


def _generate_pkce_verifier() -> str:
    return secrets.token_urlsafe(64)


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def _oauth_callback_url(request: Request) -> str:
    return str(request.url_for("oauth_callback"))


def _build_supabase_oauth_url(provider: str, redirect_to: str, challenge: str, state: str) -> str:
    if not SUPABASE_URL:
        raise HTTPException(status_code=500, detail="SUPABASE_URL is not configured.")

    query = urlencode(
        {
            "provider": provider,
            "redirect_to": redirect_to,
            "code_challenge": challenge,
            "code_challenge_method": "s256",
            "state": state,
        }
    )
    return f"{SUPABASE_URL.rstrip('/')}/auth/v1/authorize?{query}"


@router.post("/login")
async def login(payload: LoginRequest, request: Request, response: Response):
    auth_response = request.app.state.supabase.auth.sign_in_with_password(
        {"email": payload.email, "password": payload.password}
    )
    user = getattr(auth_response, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    session_row, csrf_token = request.app.state.session_service.issue_session(
        user_id=user.id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        email=getattr(user, "email", None),
    )
    _set_session_cookie(response, session_row["id"])
    return {"user": _serialize_user(user), "csrfToken": csrf_token}


@router.post("/signup")
async def signup(payload: SignupRequest, request: Request, response: Response):
    auth_response = request.app.state.supabase.auth.sign_up(
        {"email": payload.email, "password": payload.password}
    )
    user = getattr(auth_response, "user", None)
    if not user:
        raise HTTPException(status_code=400, detail="Unable to create account.")

    _ensure_public_user_row(request.app.state.supabase, user.id)

    auth_session = getattr(auth_response, "session", None)
    if not auth_session:
        return {
            "user": _serialize_user(user),
            "requiresConfirmation": True,
        }

    session_row, csrf_token = request.app.state.session_service.issue_session(
        user_id=user.id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        email=getattr(user, "email", None),
    )
    _set_session_cookie(response, session_row["id"])
    return {
        "user": _serialize_user(user),
        "csrfToken": csrf_token,
        "requiresConfirmation": False,
    }


@router.get("/me")
async def me(request: Request):
    cookie_name = SessionCookieSettings.from_config().cookie_name
    session_id = request.cookies.get(cookie_name)
    if not session_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    session = request.app.state.session_service.get_active_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")

    csrf_token = request.app.state.session_service.rotate_csrf_token(session_id)

    return {
        "user": _serialize_user(session),
        "csrfToken": csrf_token,
    }


async def oauth_exchange_disabled(payload: Any, request: Request, response: Response):
    """
    Exchange a Supabase OAuth access token (from Google/Apple PKCE flow) for a
    HELIOS session cookie. Called by AuthCallbackPage after exchangeCodeForSession.
    No CSRF required — this endpoint establishes the initial session.
    """
    try:
        user_response = request.app.state.supabase.auth.get_user(payload.access_token)
        user = getattr(user_response, "user", None)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid OAuth token.")

    if not user:
        raise HTTPException(status_code=401, detail="Invalid OAuth token.")

    _ensure_public_user_row(request.app.state.supabase, user.id)

    session_row, csrf_token = request.app.state.session_service.issue_session(
        user_id=user.id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        email=getattr(user, "email", None),
    )
    _set_session_cookie(response, session_row["id"])
    return {"user": _serialize_user(user), "csrfToken": csrf_token}


@router.get("/oauth/start")
async def oauth_start(
    request: Request,
    provider: str = Query(default="google"),
    redirect: str = Query(default="/"),
    return_origin: str | None = Query(default=None),
):
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(status_code=422, detail="Unsupported OAuth provider.")

    verifier = _generate_pkce_verifier()
    state = _generate_oauth_state()
    redirect_path = _safe_app_path(redirect)
    frontend_origin = _safe_return_origin(return_origin)
    callback_url = _oauth_callback_url(request)
    supabase_url = _build_supabase_oauth_url(
        provider=provider,
        redirect_to=callback_url,
        challenge=_pkce_challenge(verifier),
        state=state,
    )

    response = RedirectResponse(supabase_url)
    _set_oauth_cookie(response, OAUTH_STATE_COOKIE, state)
    _set_oauth_cookie(response, OAUTH_VERIFIER_COOKIE, verifier)
    _set_oauth_cookie(response, OAUTH_REDIRECT_COOKIE, _encode_cookie_value(redirect_path))
    _set_oauth_cookie(response, OAUTH_ORIGIN_COOKIE, _encode_cookie_value(frontend_origin))
    return response


@router.get("/oauth/callback", name="oauth_callback")
async def oauth_callback(
    request: Request,
    response: Response,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
):
    frontend_origin = _safe_return_origin(_decode_cookie_value(request.cookies.get(OAUTH_ORIGIN_COOKIE)))
    redirect_path = _safe_app_path(_decode_cookie_value(request.cookies.get(OAUTH_REDIRECT_COOKIE)))
    failure_url = f"{frontend_origin}/auth?oauth_error=1"

    state_cookie = request.cookies.get(OAUTH_STATE_COOKIE)
    verifier = request.cookies.get(OAUTH_VERIFIER_COOKIE)
    if error or not code or not state or not state_cookie or state != state_cookie or not verifier:
        failure = RedirectResponse(failure_url)
        _clear_oauth_cookies(failure)
        return failure

    callback_url = _oauth_callback_url(request)
    try:
        auth_response = request.app.state.supabase.auth.exchange_code_for_session(
            {
                "auth_code": code,
                "code_verifier": verifier,
                "redirect_to": callback_url,
            }
        )
        user = getattr(auth_response, "user", None)
        if not user and getattr(auth_response, "session", None):
            user = getattr(auth_response.session, "user", None)
    except Exception:
        failure = RedirectResponse(failure_url)
        _clear_oauth_cookies(failure)
        return failure

    if not user:
        failure = RedirectResponse(failure_url)
        _clear_oauth_cookies(failure)
        return failure

    _ensure_public_user_row(request.app.state.supabase, user.id)
    session_row, csrf_token = request.app.state.session_service.issue_session(
        user_id=user.id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        email=getattr(user, "email", None),
    )
    success = RedirectResponse(f"{frontend_origin}{redirect_path}")
    _set_session_cookie(success, session_row["id"])
    _clear_oauth_cookies(success)
    return success


@router.post("/logout")
async def logout(request: Request, response: Response):
    cookie_name = SessionCookieSettings.from_config().cookie_name
    session_id = request.cookies.get(cookie_name)
    if session_id:
        request.app.state.session_service.revoke_session(session_id)
    _clear_session_cookie(response)
    return {"ok": True}
