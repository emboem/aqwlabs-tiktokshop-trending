"""Login tim sederhana: satu kata sandi bersama + sesi bertanda tangan HMAC (cookie httpOnly).

* ``APP_PASSWORD`` kosong  -> aplikasi terbuka tanpa login (hanya untuk pemakaian lokal).
* ``ADMIN_PASSWORD``       -> wajib untuk mengganti cookie FastMoss (default = APP_PASSWORD).
"""
from __future__ import annotations

import hashlib
import hmac
import time

from fastapi import HTTPException, Request

from . import settings

SESSION_COOKIE = "fml_session"


def _sign(payload: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_token(role: str) -> str:
    exp = int(time.time()) + settings.SESSION_DAYS * 86400
    payload = f"{role}.{exp}"
    return f"{payload}.{_sign(payload)}"


def read_token(token: str | None) -> str | None:
    if not token:
        return None
    try:
        role, exp, sig = token.split(".")
    except ValueError:
        return None
    payload = f"{role}.{exp}"
    if not hmac.compare_digest(sig, _sign(payload)) or int(exp) < time.time():
        return None
    return role


def check_password(password: str) -> str | None:
    """Kembalikan peran ('admin' / 'team') bila kata sandi cocok."""
    if settings.ADMIN_PASSWORD and hmac.compare_digest(password, settings.ADMIN_PASSWORD):
        return "admin"
    if settings.APP_PASSWORD and hmac.compare_digest(password, settings.APP_PASSWORD):
        return "team"
    return None


def current_role(request: Request) -> str | None:
    if not settings.APP_PASSWORD:
        return "admin"
    return read_token(request.cookies.get(SESSION_COOKIE))


def require_team(request: Request) -> str:
    role = current_role(request)
    if not role:
        raise HTTPException(status_code=401, detail="Silakan masuk dulu.")
    return role


def require_admin(request: Request) -> str:
    role = require_team(request)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang boleh mengganti cookie.")
    return role
