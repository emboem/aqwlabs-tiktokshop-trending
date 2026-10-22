"""Endpoint JSON untuk tampilan web."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from .. import auth, settings
from ..accounts import current_id, registry
from ..catalog import GROUP_ORDER, MENU_BY_KEY, MENUS
from ..details import DETAILS, fetch_section
from ..fastmoss.cookies import SESSION_KEY, cookie_get, detect_cookie
from ..market import MARKET_PAGES, fetch_market
from ..services import fetch_list, fetch_options

router = APIRouter(prefix="/api")


class LoginBody(BaseModel):
    password: str


class CookieBody(BaseModel):
    account: str | None = None      # kosong = akun yang sedang dipakai
    text: str = ""                  # kosong = hanya ganti nama
    label: str | None = None


class NewAccountBody(BaseModel):
    label: str = ""


def _region(request: Request) -> str:
    r = (request.query_params.get("region") or settings.DEFAULT_REGION).upper()
    return r if r.isalpha() and len(r) <= 3 else settings.DEFAULT_REGION


def _query(request: Request) -> dict:
    return {k: v for k, v in request.query_params.items() if k not in ("region", "acc")}


# --- sesi -------------------------------------------------------------------------
@router.get("/me")
async def me(request: Request):
    return {"role": auth.current_role(request), "auth_required": bool(settings.APP_PASSWORD)}


@router.post("/login")
async def login(body: LoginBody, response: Response, request: Request):
    role = auth.check_password(body.password)
    if not role:
        raise HTTPException(status_code=401, detail="Kata sandi salah.")
    response.set_cookie(auth.SESSION_COOKIE, auth.make_token(role), max_age=settings.SESSION_DAYS * 86400,
                        httponly=True, samesite="lax", secure=request.url.scheme == "https")
    return {"role": role}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(auth.SESSION_COOKIE)
    return {"ok": True}


# --- katalog & data ----------------------------------------------------------------
@router.get("/catalog")
async def catalog(_: str = Depends(auth.require_team)):
    return {
        "groups": GROUP_ORDER,
        "menus": [m.public() for m in MENUS],
        "market": MARKET_PAGES,
        "details": {k: v.public() for k, v in DETAILS.items()},
        "free_row_limit": settings.FREE_ROW_LIMIT,
    }


@router.get("/list/{key}")
async def list_menu(key: str, request: Request, _: str = Depends(auth.require_team)):
    menu = MENU_BY_KEY.get(key)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu tidak ditemukan.")
    return await fetch_list(menu, _query(request), _region(request))


@router.get("/options/{source}")
async def options(source: str, request: Request, _: str = Depends(auth.require_team)):
    return await fetch_options(source, _region(request))


@router.get("/detail/{kind}/{item_id}/{section}")
async def detail(kind: str, item_id: str, section: str, request: Request, _: str = Depends(auth.require_team)):
    if not item_id.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="ID tidak valid.")
    return await fetch_section(kind, item_id, section, _query(request), _region(request))


@router.get("/market/{page}/{section}")
async def market(page: str, section: str, request: Request, _: str = Depends(auth.require_team)):
    return await fetch_market(page, section, _query(request), _region(request))


# --- akun & cookie ------------------------------------------------------------------
@router.get("/account")
async def account(request: Request, _: str = Depends(auth.require_team)):
    """Status akun yang sedang dipakai pengguna ini (dipilih lewat header X-FM-Account)."""
    acc_id = current_id()
    if request.query_params.get("refresh") == "1":
        await registry.client(acc_id).account(force=True)
    return await registry.summary(acc_id)


@router.get("/accounts")
async def accounts(request: Request, _: str = Depends(auth.require_team)):
    """Semua akun FastMoss yang tersedia (untuk pilihan akun). Nilai cookie tidak pernah dikirim."""
    if request.query_params.get("refresh") == "1":
        for i in registry.ids():
            await registry.client(i).account(force=True)
    return {"current": current_id(), "default": registry.default_id(),
            "accounts": [await registry.summary(i) for i in registry.ids()]}


@router.post("/accounts")
async def account_create(body: NewAccountBody, _: str = Depends(auth.require_admin)):
    """Tambah slot akun kosong baru (config/cookies_akun_<N>.txt)."""
    acc_id = registry.create(body.label.strip())
    return await registry.summary(acc_id)


@router.post("/cookie")
async def cookie_save(body: CookieBody, _: str = Depends(auth.require_admin)):
    """Simpan cookie dan/atau nama untuk satu akun, lalu uji ke FastMoss."""
    acc_id = (body.account or "").strip() or current_id()
    if acc_id not in registry.ids():
        raise HTTPException(status_code=404, detail=f"Akun {acc_id} tidak ditemukan.")
    cl = registry.client(acc_id)
    label = body.label.strip() if body.label is not None else None
    try:
        if body.text.strip():
            cl.cookies.save(body.text, label)
        elif label is not None:
            cl.cookies.set_label(label)
        else:
            raise ValueError("Tempel cookie atau isi nama akun dulu.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    cl.clear_cache()
    await cl.account(force=True)
    return await registry.summary(acc_id)


@router.post("/cookie/preview")
async def cookie_preview(body: CookieBody, _: str = Depends(auth.require_admin)):
    """Kenali format tempelan TANPA menyimpan. Yang dibalas hanya ringkasan, bukan nilai cookie."""
    cookie, fmt = detect_cookie(body.text)
    names = [c.split("=", 1)[0] for c in cookie.split("; ")] if cookie else []
    return {"ok": bool(cookie), "format": fmt, "count": len(names),
            "has_session": bool(cookie_get(cookie, SESSION_KEY))}


@router.post("/cache/clear")
async def cache_clear(_: str = Depends(auth.require_admin)):
    registry.clear_cache()
    return {"ok": True}
