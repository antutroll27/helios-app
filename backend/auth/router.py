from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from backend.auth.session_service import SessionCookieSettings

router = APIRouter()


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
    try:
        supabase.table("users").insert({"id": user_id}).execute()
    except Exception:
        pass


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


@router.post("/logout")
async def logout(request: Request, response: Response):
    cookie_name = SessionCookieSettings.from_config().cookie_name
    session_id = request.cookies.get(cookie_name)
    if session_id:
        request.app.state.session_service.revoke_session(session_id)
    _clear_session_cookie(response)
    return {"ok": True}
