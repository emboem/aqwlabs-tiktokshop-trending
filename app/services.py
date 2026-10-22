"""Logika bersama: ambil daftar menu, terapkan batas paket, normalisasi opsi filter."""
from __future__ import annotations

import datetime as _dt
from typing import Any

from . import settings
from .catalog import OPTION_SOURCES, Menu, build_params
from .fastmoss.client import FastMossClient, FMResult

client = FastMossClient()


def dig(obj: Any, path: str) -> Any:
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _total(data: dict) -> int | None:
    for k in ("total", "total_count", "total_cnt", "result_cnt"):
        v = data.get(k)
        if isinstance(v, (int, float)) or (isinstance(v, str) and v.isdigit()):
            return int(v)
    return None


async def fetch_list(menu: Menu, query: dict, region: str) -> dict:
    """Ambil satu halaman data menu. Akun gratis: hanya halaman 1 & N baris teratas (seperti FastMoss)."""
    params = build_params(menu, query)
    params["region"] = region
    limit = await client.row_limit()
    page = int(params.get("page") or 1)
    if limit and page > 1:
        return {"status": "locked", "message": f"Akun gratis hanya bisa melihat {limit} baris teratas di halaman 1. "
                                                "Halaman berikutnya terkunci paket FastMoss.",
                "rows": [], "params": params, "limit": limit}
    referer = settings.BASE_URL + menu.referer if menu.referer else None
    res: FMResult = await client.get(menu.path, params, region=region, referer=referer)
    out = {"status": res.status, "message": res.message, "code": res.code, "cached": res.cached,
           "params": params, "rows": [], "total": None, "limit": limit, "hidden": 0}
    if not res.ok:
        return out
    data = res.data if isinstance(res.data, dict) else {}
    rows = data.get(menu.list_key) or []
    if not isinstance(rows, list):
        rows = []
    if not rows and not query.get("date_value") and str(params.get("date_type")) == "1"             and any(c.kind == "period" for c in menu.controls):
        # Peringkat harian FastMoss diperbarui siang hari; sebelum itu data "kemarin" masih kosong.
        older = (_dt.date.today() - _dt.timedelta(days=2)).isoformat()
        retry = await client.get(menu.path, {**params, "date_value": older}, region=region, referer=referer)
        rdata = retry.data if retry.ok and isinstance(retry.data, dict) else {}
        if isinstance(rdata.get(menu.list_key), list) and rdata[menu.list_key]:
            data, rows = rdata, rdata[menu.list_key]
            params["date_value"] = older
            out["message"] = f"Data kemarin belum diperbarui FastMoss — menampilkan data {older}."
            out["fallback"] = True
    out["total"] = _total(data)
    out["update_at"] = data.get("update_at") or data.get("update_time")
    if limit and len(rows) > limit:
        out["hidden"] = len(rows) - limit
        rows = rows[:limit]
    out["rows"] = rows
    return out


def _norm_option(item: Any) -> dict | None:
    if not isinstance(item, dict):
        return None
    val = next((item[k] for k in ("code", "c_code", "a_code", "region_code", "id") if k in item), None)
    lab = next((item[k] for k in ("name", "c_name", "a_name", "region_name", "value", "label") if item.get(k)), None)
    if val is None:
        return None
    opt = {"v": val, "l": str(lab if lab is not None else val)}
    if isinstance(item.get("sub"), list) and item["sub"]:
        opt["sub"] = [o for o in (_norm_option(s) for s in item["sub"]) if o]
    return opt


async def fetch_options(source: str, region: str) -> dict:
    path = OPTION_SOURCES.get(source)
    if not path:
        return {"status": "error", "message": "Sumber opsi tidak dikenal.", "options": {}}
    params = {"region": region} if source not in ("country",) else {}
    res = await client.get(path, params, region=region)
    if not res.ok:
        return {"status": res.status, "message": res.message, "options": {}}
    data = res.data
    if isinstance(data, list):
        data = {"list": data}
    options = {}
    for k, v in (data or {}).items():
        if isinstance(v, list):
            options[k] = [o for o in (_norm_option(i) for i in v) if o]
    return {"status": "ok", "options": options}
