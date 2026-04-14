from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import secrets
from typing import Any

from backend.config import (
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE,
    SESSION_TTL_HOURS,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True)
class SessionCookieSettings:
    cookie_name: str
    same_site: str
    http_only: bool
    secure: bool

    @classmethod
    def from_config(cls) -> "SessionCookieSettings":
        return cls(
            cookie_name=SESSION_COOKIE_NAME,
            same_site=SESSION_COOKIE_SAMESITE,
            http_only=True,
            secure=SESSION_COOKIE_SECURE,
        )


class SessionService:
    def __init__(self, supabase, ttl_hours: int = SESSION_TTL_HOURS):
        self.supabase = supabase
        self.ttl_hours = ttl_hours

    def issue_session(
        self,
        user_id: str,
        ip: str | None,
        user_agent: str | None,
        email: str | None = None,
    ) -> tuple[dict[str, Any], str]:
        session_id = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(24)
        now = _utc_now()
        payload = {
            "id": session_id,
            "user_id": user_id,
            "email_snapshot": email,
            "csrf_token_hash": self._sha256(csrf_token),
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=self.ttl_hours)).isoformat(),
            "rotated_at": None,
            "revoked_at": None,
            "last_seen_at": now.isoformat(),
            "ip_hash": self._sha256(ip) if ip else None,
            "user_agent_hash": self._sha256(user_agent) if user_agent else None,
        }
        self.supabase.table("app_sessions").insert(payload).execute()
        return payload, csrf_token

    def get_active_session(self, session_id: str) -> dict[str, Any] | None:
        result = (
            self.supabase.table("app_sessions")
            .select("*")
            .eq("id", session_id)
            .execute()
        )
        if not result.data:
            return None

        session = result.data[0]
        if session.get("revoked_at"):
            return None

        expires_at = _parse_datetime(session.get("expires_at"))
        if not expires_at or expires_at <= _utc_now():
            return None

        return session

    def revoke_session(self, session_id: str) -> None:
        self.supabase.table("app_sessions").update(
            {
                "revoked_at": _utc_now().isoformat(),
            }
        ).eq("id", session_id).execute()

    def rotate_csrf_token(self, session_id: str) -> str:
        csrf_token = secrets.token_urlsafe(24)
        self.supabase.table("app_sessions").update(
            {
                "csrf_token_hash": self._sha256(csrf_token),
                "last_seen_at": _utc_now().isoformat(),
            }
        ).eq("id", session_id).execute()
        return csrf_token

    def validate_csrf(self, session: dict[str, Any], token: str | None) -> bool:
        if not token:
            return False
        return session.get("csrf_token_hash") == self._sha256(token)

    @staticmethod
    def _sha256(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()
