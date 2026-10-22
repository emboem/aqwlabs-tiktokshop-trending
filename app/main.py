"""FastMoss Lite v2 — aplikasi web (FastAPI) untuk analisis TikTok Shop via FastMoss.

Jalankan:  uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import settings
from .accounts import AccountMiddleware, registry
from .routes import api, export

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
WEB = settings.ROOT / "web"


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.APP_PASSWORD and settings.SECRET_KEY == "ganti-kunci-rahasia-ini":
        logging.getLogger("app").warning("SECRET_KEY masih bawaan — isi SECRET_KEY di .env sebelum disebar ke tim!")
    registry.migrate_legacy()
    if not registry.ids():
        logging.getLogger("app").warning("Belum ada file akun di %s (cookies_akun_1.txt, ...).", settings.COOKIE_DIR)
    yield
    await registry.close()


app = FastAPI(title="FastMoss Lite", version="2.0.0", lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(AccountMiddleware)
app.include_router(api.router)
app.include_router(export.router)
app.mount("/assets", StaticFiles(directory=WEB / "assets"), name="assets")


@app.exception_handler(Exception)
async def _unhandled(_: Request, exc: Exception):
    logging.getLogger("app").exception("Kesalahan tak terduga")
    return JSONResponse({"detail": f"Terjadi kesalahan di server: {type(exc).__name__}"}, status_code=500)


@app.get("/healthz", include_in_schema=False)
async def healthz():
    return {"ok": True}


def _index_html() -> str:
    """index.html dengan ?v=<mtime> pada aset, supaya browser tim langsung memuat versi terbaru."""
    html = (WEB / "index.html").read_text(encoding="utf-8")
    for name in ("app.css", "app.js"):
        ver = int((WEB / "assets" / name).stat().st_mtime)
        html = html.replace(f"/assets/{name}\"", f"/assets/{name}?v={ver}\"")
    return html


@app.get("/{path:path}", include_in_schema=False)
async def spa(path: str):
    return HTMLResponse(_index_html(), headers={"Cache-Control": "no-cache"})
