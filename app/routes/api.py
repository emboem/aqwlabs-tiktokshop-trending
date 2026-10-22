"""Endpoint JSON untuk tampilan web."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from .. import auth, settings
from ..catalog import GROUP_ORDER, MENU_BY_KEY, MENUS
from ..details import DETAILS, fetch_section
from ..market import MARKET_PAGES, fetch_market
from ..services import client, fetch_list, fetch_options

router = APIRouter(prefix="/api")


class LoginBody(BaseModel):
    password: str


class CookieBody(BaseModel):
    text: str


def _region(request: Request) -> str:
    r = (request.query_params.get("region") or settings.DEFAULT_REGION).upper()
    return r if r.isalpha() and len(r) <= 3 else settings.DEFAULT_REGION


def _query(request: Request) -> dict:
    return {k: v for k, v in request.query_params.items() if k != "region"}


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
    acc = await client.account(force=request.query_params.get("refresh") == "1")
    acc = dict(acc)
    acc["cookie"] = {k: v for k, v in acc["cookie"].items() if k != "path"}
    return acc


@router.get("/cookie")
async def cookie_status(_: str = Depends(auth.require_admin)):
    return client.cookies.status().as_dict()


@router.post("/cookie")
async def cookie_save(body: CookieBody, _: str = Depends(auth.require_admin)):
    try:
        client.cookies.save(body.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    client.clear_cache()
    acc = dict(await client.account(force=True))
    acc["cookie"] = {k: v for k, v in acc["cookie"].items() if k != "path"}
    return acc


@router.post("/cache/clear")
async def cache_clear(_: str = Depends(auth.require_admin)):
    client.clear_cache()
    return {"ok": True}
