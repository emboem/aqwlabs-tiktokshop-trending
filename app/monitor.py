"""Monitor video FastMoss (``/monitor/videoMonitor``): kuota, riwayat, cari video, tambah monitor.

Semua data di sini milik akun FastMoss yang dipakai. Menambah monitor **memakai kuota bulanan**
akun berlangganan, jadi:

* hanya admin Lite yang boleh menambah,
* request wajib membawa ``confirm=true`` (tampilan web meminta konfirmasi eksplisit dulu),
* request tambah tidak pernah diulang otomatis (kuota tak terpakai dua kali).

Payload mengikuti halaman FastMoss asli (Okt 2026): ``{type, duration, notify_video_count,
notify_digg_count, notify_play_count, obj_id}``; ``duration`` dalam detik (24/48/72/168 jam).
"""
from __future__ import annotations

from . import settings
from .services import client

REFERER = "/id/monitor/videoMonitor"
DURATIONS = {24: 86400, 48: 172800, 72: 259200, 168: 604800}
STATUS = {0: "Menunggu", 1: "Sedang dipantau", 2: "Selesai"}
ADD_STATUS = {2: "Kuota monitor akun FastMoss habis atau paket tidak mencukupi.",
              6: "Kuota monitor akun FastMoss habis atau paket tidak mencukupi.",
              3: "Video ini sudah sedang dipantau.",
              7: "Waktu monitor tidak valid."}


CONSUME_TYPES = {1: "Monitor video", 2: "Monitor akun kreator", 3: "Monitor LIVE"}


def _consume_text(x) -> str:
    """{"hour": 24, "consume": 1} → "24 jam = 1 kuota"."""
    if isinstance(x, dict) and "hour" in x:
        return f"{x.get('hour')} jam = {x.get('consume')} kuota"
    return str(x)


def _ref() -> str:
    return settings.BASE_URL + REFERER


def _out(res) -> dict:
    return {"status": res.status, "message": res.message, "code": res.code}


async def quota(region: str) -> dict:
    """Sisa kuota monitor + rincian pemakaian (``/api/monitor/info``)."""
    res = await client.post("/api/monitor/info", {"region": region}, {}, region=region, referer=_ref())
    out = _out(res)
    if res.ok and isinstance(res.data, dict):
        d = res.data
        info = d.get("consume_info") if isinstance(d.get("consume_info"), list) else []
        out.update(remain=d.get("remain") or 0,
                   consume=[{"title": CONSUME_TYPES.get(int((c or {}).get("type") or 0), "Pemakaian kuota"),
                             "info": [_consume_text(x) for x in (c or {}).get("info") or []]} for c in info])
    return out


async def history(query: dict, region: str) -> dict:
    """Riwayat monitor akun (bukan data contoh: ``is_demo=1`` dibuang)."""
    params = {"region": region, "page": int(query.get("page") or 1), "pagesize": 10,
              "type": query.get("type") or "", "status": query.get("status") or ""}
    res = await client.get("/api/monitor/list", params, region=region, referer=_ref(), use_cache=False)
    out = _out(res) | {"rows": [], "total": 0, "page": params["page"]}
    if not res.ok or not isinstance(res.data, dict):
        return out
    d = res.data
    if str(d.get("is_demo") or "0") == "1":
        out["message"] = "Akun FastMoss ini belum punya riwayat monitor (FastMoss hanya menampilkan contoh)."
        return out
    rows = d.get("list") if isinstance(d.get("list"), list) else []
    for r in rows:
        r["status_text"] = STATUS.get(int(r.get("status") or 0), str(r.get("status")))
        idx = (r.get("content") or {}).get("index_list") if isinstance(r.get("content"), dict) else None
        for it in idx or []:
            r[f"notify_{it.get('field')}"] = it.get("count")
    out.update(rows=rows, total=int(d.get("total") or 0))
    return out


async def search(content: str, region: str) -> dict:
    """Cari video lewat tautan / ID video TikTok."""
    content = (content or "").strip()
    if not content:
        return {"status": "error", "message": "Tempel tautan atau ID video TikTok dulu.", "rows": []}
    if content.isdigit():
        content = f"https://www.tiktok.com/@x/video/{content}"
    res = await client.get("/api/monitor/search", {"region": region, "type": 1, "content": content},
                           region=region, referer=_ref(), use_cache=False)
    rows = res.data.get("list") if res.ok and isinstance(res.data, dict) else None
    return _out(res) | {"rows": rows if isinstance(rows, list) else []}


async def add(body: dict, region: str) -> dict:
    """Tambah monitor video. Memakai kuota — wajib ``confirm``."""
    if body.get("confirm") is not True:
        return {"status": "error", "message": "Konfirmasi pemakaian kuota monitor dulu."}
    vid = str(body.get("video_id") or "").strip()
    if not vid.isdigit():
        return {"status": "error", "message": "ID video tidak valid."}
    try:
        hours = int(body.get("hours") or 24)
    except (TypeError, ValueError):
        hours = 0
    if hours not in DURATIONS:
        return {"status": "error", "message": "Durasi monitor harus 24, 48, 72, atau 168 jam."}

    def num(k):
        v = str(body.get(k) or "").strip()
        return v if v.isdigit() else ""

    payload = {"type": "1", "duration": DURATIONS[hours], "notify_video_count": "",
               "notify_digg_count": num("notify_digg_count"), "notify_play_count": num("notify_play_count"),
               "obj_id": vid}
    res = await client.post("/api/monitor/add", {"region": region}, payload, region=region, referer=_ref(), retries=1)
    out = _out(res)
    if res.ok and isinstance(res.data, dict):
        if int(res.data.get("is_success") or 0) == 1:
            out["message"] = "Monitor ditambahkan. Data dipantau FastMoss sesuai durasi yang dipilih."
        else:
            st = int(res.data.get("status") or 0)
            out.update(status="error", message=ADD_STATUS.get(st, res.message or "FastMoss menolak permintaan."))
    return out
