"""Account authentication without storing plaintext passwords or session tokens."""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import PUBLIC_REGISTRATION_ENABLED, SESSION_DAYS
from app.product.store import platform_store, utc_now


EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PBKDF2_ITERATIONS = 600_000


def _password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def _password_valid(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.urlsafe_b64decode(salt), int(iterations))
        return hmac.compare_digest(base64.urlsafe_b64encode(digest).decode(), expected)
    except (ValueError, TypeError):
        return False


class AuthService:
    def register(self, email: str, password: str, display_name: str) -> dict[str, str]:
        if not PUBLIC_REGISTRATION_ENABLED:
            raise PermissionError("Registration is currently invitation-only.")
        email = email.strip().casefold()
        display_name = display_name.strip()
        if not EMAIL.fullmatch(email):
            raise ValueError("Enter a valid email address.")
        if len(password) < 10 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            raise ValueError("Password must be at least 10 characters and include a letter and number.")
        if not 2 <= len(display_name) <= 80:
            raise ValueError("Display name must be 2 to 80 characters.")
        try:
            user_id = platform_store.insert("users", {"email": email, "display_name": display_name,
                "password_hash": _password_hash(password), "role": "customer", "disabled_at": None})
        except Exception as error:
            if "UNIQUE" in str(error).upper():
                raise ValueError("An account with this email already exists.") from error
            raise
        token = self._session(user_id)
        return {"token": token, "user_id": user_id, "display_name": display_name}

    def login(self, email: str, password: str) -> dict[str, str]:
        with platform_store.connection() as connection:
            row = connection.execute("SELECT * FROM users WHERE email=? AND disabled_at IS NULL",
                                     (email.strip().casefold(),)).fetchone()
        if row is None or not _password_valid(password, str(row["password_hash"])):
            raise PermissionError("Invalid email or password.")
        return {"token": self._session(str(row["id"])), "user_id": str(row["id"]),
                "display_name": str(row["display_name"])}

    def _session(self, user_id: str) -> str:
        token = secrets.token_urlsafe(32)
        expires = (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).isoformat()
        platform_store.insert("sessions", {"user_id": user_id,
            "token_hash": hashlib.sha256(token.encode()).hexdigest(), "expires_at": expires,
            "revoked_at": None})
        return token

    def authenticate(self, token: str) -> dict[str, object]:
        digest = hashlib.sha256(token.encode()).hexdigest()
        with platform_store.connection() as connection:
            row = connection.execute(
                "SELECT u.id,u.email,u.display_name,u.role FROM sessions s JOIN users u ON u.id=s.user_id "
                "WHERE s.token_hash=? AND s.revoked_at IS NULL AND s.expires_at>? AND u.disabled_at IS NULL",
                (digest, utc_now())).fetchone()
        if row is None:
            raise PermissionError("Sign in is required.")
        return dict(row)

    def logout(self, token: str) -> None:
        digest = hashlib.sha256(token.encode()).hexdigest()
        with platform_store.connection() as connection:
            connection.execute("UPDATE sessions SET revoked_at=? WHERE token_hash=?", (utc_now(), digest))


auth_service = AuthService()
