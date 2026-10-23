"""Penanda tangan request FastMoss (header ``fm-sign`` + ``fm-sig``).

Port Python dari JavaScript resmi FastMoss (interceptor axios + ``__SIG__.gen``).
Diverifikasi terhadap vektor nyata dari browser dan 40 URL acak (40/40 cocok).

Setiap request FastMoss wajib membawa:
  * query ``_time`` (detik unix) dan ``cnonce`` (angka acak 8 digit),
  * header ``fm-sign``  = md5(param terurut + garam) yang dilipat XOR,
  * header ``fm-sig``   = sidik 64 karakter base36 dari ``path?query-terurut``.
"""
from __future__ import annotations

import hashlib
import random
import time

SALT = "LAA6edGHBkcc3eTiOIRfg89bu9ODA6PB"
_SIG_SEED = "asjdajgo3it4398t98a"
_M32 = 0xFFFFFFFF


# --- aritmetika integer 32-bit ala JavaScript ---------------------------------
def _i32(x: int) -> int:
    x = int(x) & _M32
    return x - 0x100000000 if x & 0x80000000 else x


def _u32(x: int) -> int:
    return int(x) & _M32


def _imul(a: int, b: int) -> int:
    return _i32((a * b) & _M32)


def _shl(a: int, n: int) -> int:
    return _i32(_u32(a) << (n & 31))


def _sar(a: int, n: int) -> int:
    return _i32(a) >> (n & 31)


def _shr(a: int, n: int) -> int:
    return _u32(a) >> (n & 31)


def _js_str(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


# --- fm-sign -------------------------------------------------------------------
def fm_sign(params: dict, body: str = "") -> str:
    """Header ``fm-sign``: md5 dari ``key+value+SALT`` (kunci terurut) + body, lalu dilipat XOR."""
    raw = "".join(f"{k}{_js_str(params[k])}{SALT}" for k in sorted(params))
    digest = hashlib.md5((raw + body).encode("utf-8")).hexdigest()
    out, lo, hi = [], 0, len(digest) - 1
    while lo < hi:
        out.append(format(int(digest[lo], 16) ^ int(digest[hi], 16), "x"))
        lo += 1
        hi -= 1
    return "".join(out) + digest[lo:]


# --- fm-sig --------------------------------------------------------------------
def _mix(e: int) -> int:
    return (_i32(73 * e) ^ _shl(e, 1) ^ _shr(e, 3) ^ 90) & 255


def _str_hash(s: str) -> int:
    t = 0
    for ch in s:
        t = _i32(_imul(31, t) + ord(ch))
    return t


def _sig_inner(url: str, extra: str) -> str:
    state = {"entropy": 12648430, "seq": 1}
    seed = _str_hash(_SIG_SEED)

    def rnd(n: int) -> int:
        a = _u32(n)
        for _ in range(3):
            a = _i32(_u32(1664525 * a + 1013904223)) ^ _shr(a, 7)
        state["seq"] ^= 255 & a
        return a

    def bump(n: int) -> None:
        state["seq"] += n or 1
        if (7 & state["seq"]) == 3:
            state["entropy"] = _shl(state["entropy"], 1) ^ 4660

    length = max(len(url), len(extra)) or 1
    u: list[int] = []
    for idx in range(length):
        c2 = ord(url[idx % len(url)]) if url else 0
        c3 = ord(extra[idx % len(extra)]) if extra else 0
        c4 = (_i32(31 * c2) ^ _i32(17 * c3) ^ (_sar(seed, idx % 5 + 1) & 255)) & 255
        c4 = (_shl(c4, 3) | _shr(c4, 5)) ^ (_i32(7 * idx) & 255)
        c4 = (c4 + ((_mix(idx) ^ rnd(seed + idx)) & 255)) & 255
        if idx % 6 == 0:
            bump(idx)
        u.append(c4)

    n = len(u)
    p = s = 0
    for b in range(0, n, 2):
        p = _shl(p, 5) ^ u[b]
        s = _shl(s, 3) ^ (u[b + 1] if b + 1 < n else 0)

    def fold(e: int) -> int:
        t = e
        for k in range(3):
            t = _i32(_shl(t, 5) | _shr(t, 3)) ^ (97 * k)
        return _i32(t)

    y = _i32(p ^ s ^ fold(p))
    d = [0] * 64
    for e in range(64):
        m = (_shr(y, e % 32) & 255) ^ (u[e % n] if n else 0) ^ _mix((e + seed) & 255)
        k = e % 5 + 1
        m = (_shl(m, k) | _shr(m, 8 - k)) & 255
        t = 0
        for j, v in enumerate((m, e, 255 & seed)):
            t = ((t ^ v) + 7 * j) & 255
        d[e] = (m + t) & 255
    for g in range(64):
        d[g] ^= _shr(state["entropy"], g % 8) & 255
        d[g] = (d[g] + ((131 * g) & 255)) & 255
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    return "".join(alphabet[x % 36] for x in d)


def js_encode(value) -> str:
    """``encodeURIComponent`` versi FastMoss: hanya alfanumerik dan ``-_.`` yang lolos, spasi jadi ``+``."""
    out = []
    for b in _js_str(value).encode("utf-8"):
        ch = chr(b)
        if ch.isascii() and (ch.isalnum() or ch in "-_."):
            out.append(ch)
        elif ch == " ":
            out.append("+")
        else:
            out.append("%%%02X" % b)
    return "".join(out)


def signed_query(params: dict) -> str:
    return "&".join(f"{k}={js_encode(params[k])}" for k in sorted(params))


def fm_sig(path: str, params: dict, source: str = "pc") -> str:
    q = signed_query(params)
    return _sig_inner(f"{path}?{q}" if q else path, f"source={source}")


def clean_params(params: dict | None) -> dict:
    """Buang nilai kosong (``None`` / ``""``) seperti interceptor FastMoss."""
    return {k: v for k, v in (params or {}).items() if v is not None and v != ""}


def prepare(path: str, params: dict | None, body: str = "") -> tuple[str, dict]:
    """Tambah ``_time`` + ``cnonce``, lalu kembalikan (query-string, header tanda tangan).

    Untuk POST, ``body`` = JSON ringkas yang dikirim; isinya ikut masuk ``fm-sign``.
    """
    p = clean_params(params)
    p["_time"] = int(time.time())
    p["cnonce"] = random.randint(10**7, 10**8 - 1)
    headers = {"fm-sign": fm_sign(p, body), "fm-sig": fm_sig(path, p), "source": "pc"}
    return signed_query(p), headers
