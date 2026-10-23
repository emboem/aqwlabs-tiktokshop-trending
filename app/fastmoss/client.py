"""Klien API FastMoss: tanda tangan otomatis, jeda antar-request, retry, cache, dan klasifikasi error.

Aturan penting (sesuai paket akun, TIDAK menembus paywall):
  * ``code == 200``            -> data asli, dipakai.
  * ``code = MAG_AUTH_xxxx``   -> fitur terkunci paket. FastMoss tetap mengirim DATA CONTOH palsu
                                  (mis. produk Amerika/2024), jadi datanya DIBUANG dan hanya status
                                  "terkunci" yang diteruskan ke tampilan.
  * ``data.is_mock == 1``       -> sama dengan terkunci: data contoh, DIBUANG.
  * ``code = MSG_30001``        -> belum login / cookie kedaluwarsa.
"""
from __future__ import annotations

import asyncio
import html
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from .. import settings
from .cookies import CookieStore, cookie_get
from .signer import clean_params, prepare

log = logging.getLogger("fastmoss")

OK, LOCKED, AUTH, ERROR = "ok", "locked", "auth", "error"


@dataclass
class FMResult:
    status: str
    code: Any = None
    message: str = ""
    data: Any = None
    cached: bool = False
    meta: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == OK

    def as_dict(self) -> dict:
        return {"status": self.status, "code": self.code, "message": self.message,
                "data": self.data, "cached": self.cached, "meta": self.meta}


# FastMoss menyorot kata kunci pencarian dengan tag HTML di dalam teks
# (mis. "Alquran <span style='color:red'>Al</span>-Qur'an") → buang tagnya, simpan teksnya.
_MARKUP = re.compile(r"</?(?:span|em|b|i|u|strong|font|mark|a|sup|sub|p|div|br)\b[^<>]*>", re.I)
_ENTITY = re.compile(r"&(?:#\d+|#x[0-9a-f]+|[a-z]+);", re.I)


def strip_markup(obj: Any) -> Any:
    """Bersihkan tag HTML sorotan dari semua teks di dalam data (rekursif)."""
    if isinstance(obj, str):
        if "<" in obj and _MARKUP.search(obj):
            obj = _MARKUP.sub("", obj)
            if _ENTITY.search(obj):
                obj = html.unescape(obj)
        return obj
    if isinstance(obj, list):
        return [strip_markup(x) for x in obj]
    if isinstance(obj, dict):
        return {k: strip_markup(v) for k, v in obj.items()}
    return obj


def classify(payload: dict) -> FMResult:
    code = payload.get("code")
    msg = str(payload.get("msg") or "")
    if code == 200 or code == "200":
        data = payload.get("data")
        if isinstance(data, dict) and str(data.get("is_mock", "0")) in ("1", "True", "true"):
            # code 200 tapi ditandai is_mock: FastMoss mengirim data CONTOH (bukan milik item ini)
            return FMResult(LOCKED, "IS_MOCK", "FastMoss hanya mengirim data contoh untuk bagian ini "
                                               "(terkunci paket akun yang dipakai).")
        return FMResult(OK, code, msg, strip_markup(data))
    scode = str(code)
    low = msg.lower()
    if scode == "MSG_30001" or "login" in low or "masuk" in low or "登录" in msg:
        return FMResult(AUTH, code, "Cookie FastMoss belum login atau sudah kedaluwarsa. Perbarui cookie di menu Pengaturan.")
    if scode.startswith("MAG_AUTH"):
        return FMResult(LOCKED, code, "Data ini terkunci untuk paket akun FastMoss yang dipakai. "
                                      "Upgrade paket FastMoss untuk membukanya.")
    return FMResult(ERROR, code, f"FastMoss menolak permintaan: {msg or scode}")


class FastMossClient:
    def __init__(self, cookie_store: CookieStore):
        self.cookies = cookie_store
        self._http: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()
        self._last_call = 0.0
        self._cache: dict[str, tuple[float, FMResult]] = {}
        self._inflight: dict[str, asyncio.Future] = {}
        self._account: tuple[float, dict] | None = None

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(base_url=settings.BASE_URL, timeout=settings.REQUEST_TIMEOUT,
                                           http2=False, follow_redirects=True)
        return self._http

    async def close(self) -> None:
        if self._http is not None:
            await self._http.aclose()

    def clear_cache(self) -> None:
        self._cache.clear()
        self._account = None

    @staticmethod
    def _cache_key(path: str, params: dict, region: str) -> str:
        return path + "|" + region + "|" + json.dumps(params, sort_keys=True, ensure_ascii=False, default=str)

    def _headers(self, region: str, referer: str | None) -> dict:
        cookie = self.cookies.get()
        h = {
            "accept": "application/json, text/plain, */*",
            "lang": settings.LANG,
            "region": region or cookie_get(cookie, "region") or settings.DEFAULT_REGION,
            "user-agent": settings.USER_AGENT,
            "referer": referer or f"{settings.BASE_URL}/id/",
            "origin": settings.BASE_URL,
        }
        if cookie:
            h["cookie"] = cookie
        return h

    async def get(self, path: str, params: dict | None = None, *, region: str | None = None,
                  referer: str | None = None, use_cache: bool = True) -> FMResult:
        region = region or settings.DEFAULT_REGION
        params = clean_params(params)
        key = self._cache_key(path, params, region)
        now = time.time()
        hit = self._cache.get(key)
        if use_cache and hit and hit[0] > now:
            res = hit[1]
            return FMResult(res.status, res.code, res.message, res.data, True, dict(res.meta))

        if use_cache and key in self._inflight:
            # beberapa bagian halaman memakai endpoint + parameter yang sama -> cukup satu request
            res = await asyncio.shield(self._inflight[key])
            return FMResult(res.status, res.code, res.message, res.data, True, dict(res.meta))
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        if use_cache:
            self._inflight[key] = fut
        try:
            res = await self._request(path, params, region, referer)
        except BaseException as exc:
            res = FMResult(ERROR, None, f"Permintaan gagal: {exc}")
            fut.set_result(res)
            raise
        finally:
            self._inflight.pop(key, None)
        if not fut.done():
            fut.set_result(res)
        ttl = settings.CACHE_TTL if res.status == OK else (60 if res.status == LOCKED else 0)
        if ttl and use_cache:
            self._cache[key] = (now + ttl, res)
            if len(self._cache) > 2000:
                for k in sorted(self._cache, key=lambda k: self._cache[k][0])[:500]:
                    self._cache.pop(k, None)
        return res

    async def post(self, path: str, params: dict | None = None, body: dict | None = None, *,
                   region: str | None = None, referer: str | None = None) -> FMResult:
        """POST JSON bertanda tangan (dipakai Monitor). Tidak pernah di-cache."""
        region = region or settings.DEFAULT_REGION
        return await self._request(path, clean_params(params), region, referer, body=body or {})

    async def _request(self, path: str, params: dict, region: str, referer: str | None,
                       body: dict | None = None) -> FMResult:
        http = await self._client()
        last_err = ""
        for attempt in range(1, settings.RETRIES + 1):
            async with self._lock:  # satu akun dipakai bersama: request diantrikan + diberi jeda
                wait = settings.MIN_INTERVAL - (time.monotonic() - self._last_call)
                if wait > 0:
                    await asyncio.sleep(wait)
                raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False) if body is not None else ""
                query, sig = prepare(path, params, raw)
                headers = self._headers(region, referer) | sig
                try:
                    if body is None:
                        resp = await http.get(f"{path}?{query}", headers=headers)
                    else:
                        resp = await http.post(f"{path}?{query}", headers=headers | {"content-type": "application/json"},
                                               content=raw.encode("utf-8"))
                except httpx.HTTPError as exc:
                    last_err = f"{type(exc).__name__}: {exc}"
                    resp = None
                finally:
                    self._last_call = time.monotonic()
            if resp is not None:
                if resp.status_code >= 500 or resp.status_code == 429:
                    last_err = f"HTTP {resp.status_code}"
                else:
                    try:
                        payload = resp.json()
                    except ValueError:
                        return FMResult(ERROR, resp.status_code, f"Respons FastMoss bukan JSON (HTTP {resp.status_code}).")
                    res = classify(payload)
                    if res.status == LOCKED:
                        res.data = None  # data contoh palsu — jangan pernah ditampilkan
                    log.info("FM %s %s -> %s %s", path, params.get("page", ""), res.status, res.code)
                    return res
            log.warning("FM %s gagal (percobaan %d/%d): %s", path, attempt, settings.RETRIES, last_err)
            await asyncio.sleep(1.5 * attempt)
        return FMResult(ERROR, None, f"Gagal terhubung ke FastMoss setelah {settings.RETRIES}x percobaan ({last_err}).")

    # --- akun -------------------------------------------------------------------
    async def account(self, force: bool = False) -> dict:
        """Status akun dari ``/api/user/index/userInfo`` (di-cache 10 menit)."""
        now = time.time()
        if not force and self._account and self._account[0] > now:
            return self._account[1]
        st = self.cookies.status()
        info: dict = {"cookie": st.as_dict(), "logged_in": False, "level": 0, "plan": "Belum login",
                      "is_free": True, "expire_at": None, "nickname": None, "message": ""}
        if not st.exists:
            info["message"] = "File cookie masih kosong. Isi cookie di menu Pengaturan."
        else:
            res = await self.get("/api/user/index/userInfo", {}, use_cache=False)
            if res.ok and isinstance(res.data, dict) and res.data.get("uid"):
                d = res.data
                level = int(d.get("level") or 1)
                expire = int(d.get("expire_at") or 0)
                active = level > 1 and (expire == 0 or expire > now)
                info.update(
                    logged_in=True, level=level, expire_at=expire or None,
                    is_free=not active, nickname=d.get("nickname") or d.get("username"),
                    plan="Gratis (Anggota Biasa)" if not active else f"Berlangganan (level {level})",
                    message="Cookie aktif.",
                )
            else:
                info["message"] = res.message or "Cookie tidak valid."
        self._account = (now + 600, info)
        return info

    async def row_limit(self) -> int:
        """Batas baris yang boleh ditampilkan sesuai paket (0 = tanpa batas)."""
        acc = await self.account()
        return settings.FREE_ROW_LIMIT if acc["is_free"] else 0
