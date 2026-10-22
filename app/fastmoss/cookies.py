"""Penyimpanan cookie FastMoss: SATU file khusus per akun (``config/cookies_akun_<N>.txt``).

Isi file boleh ditempel apa adanya — formatnya dikenali otomatis (``detect_cookie``):
  * string cookie biasa      : ``fd_tk=...; region=ID; ...``
  * baris header             : ``Cookie: fd_tk=...`` (boleh di tengah blok header lengkap)
  * perintah cURL utuh       : "Copy as cURL" bash maupun Windows cmd (yang penuh tanda ``^``)
  * PowerShell, fetch/Node.js, ekspor JSON ekstensi cookie, tabel cookie DevTools
Baris yang diawali ``#`` dianggap komentar, kecuali ``# nama: ...`` = nama akun yang tampil di aplikasi.

Nilai cookie TIDAK PERNAH dikirim balik ke browser; halaman Pengaturan hanya melihat statusnya.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

TEMPLATE_HEADER = """\
# ================================================================
#  COOKIE FASTMOSS — tempat khusus untuk mengganti cookie
# ================================================================
#  Cara ganti cookie:
#   1. Login FastMoss di Chrome, buka DevTools (F12) > tab Network.
#   2. Klik salah satu request ke www.fastmoss.com/api/...
#   3. Salin nilai header "cookie" (atau klik kanan > Copy as cURL).
#   4. Tempel di bawah garis ini (menggantikan isi lama), lalu simpan.
#  Perubahan langsung terbaca tanpa restart aplikasi.
#  Bisa juga lewat menu "Pengaturan & Cookie" di aplikasi.
#  Baris "# nama:" = nama akun yang tampil di pilihan akun aplikasi.
#  JANGAN bagikan / commit file ini — isinya kunci akun FastMoss.
# ----------------------------------------------------------------
"""

SESSION_KEY = "fd_tk"
LABEL_RE = re.compile(r"^[ \t]*#[ \t]*nama[ \t]*:[ \t]*(.*?)[ \t]*$", re.I | re.M)


@dataclass
class CookieStatus:
    exists: bool
    has_session: bool
    length: int
    updated_at: str | None
    path: str
    label: str = ""

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def _unescape_cmd(s: str) -> str:
    # "Copy as cURL (cmd)" di Windows: tiap karakter khusus diberi ^ (mis. ^%^2, ^|), kutip jadi \^".
    s = re.sub(r"\^(.)", r"\1", s, flags=re.S)
    return s.replace('\\"', '"').replace("\\\\", "\\")


def _unescape_bash(s: str) -> str:
    # bash: 'a'\''b' (kutip tunggal di dalam nilai) dan $'...' (escape gaya C).
    return s.replace("'\\''", "'").replace("\\'", "'").replace("\\\\", "\\")


def _unescape_dq(s: str) -> str:
    return re.sub(r"\\(.)", r"\1", s)


def parse_label(text: str) -> str:
    """Nama akun dari baris ``# nama: ...`` (kosong bila tidak ada)."""
    m = LABEL_RE.search(text or "")
    return m.group(1).strip()[:60] if m else ""


# (nama format, pola, fungsi unescape) — urutan = prioritas. Pola menangkap ISI cookie saja.
_CURL_PATTERNS = [
    ("cURL Windows (cmd)", r"""(?:\s-b|--cookie)\s+\^"(.*?)\^"(?=\s|$)""", _unescape_cmd),
    ("cURL Windows (cmd)", r"""\s-H\s+\^"cookie:\s*(.*?)\^"(?=\s|$)""", _unescape_cmd),
    ("cURL bash", r"""(?:\s-b|--cookie)\s+\$?'(.*?)'(?=\s|$)""", _unescape_bash),
    ("cURL bash", r"""\s-H\s+\$?'cookie:\s*(.*?)'(?=\s|$)""", _unescape_bash),
    ("cURL", r"""(?:\s-b|--cookie)\s+"((?:[^"\\]|\\.)*)\"""", _unescape_dq),
    ("cURL", r"""\s-H\s+"cookie:\s*((?:[^"\\]|\\.)*)\"""", _unescape_dq),
]


def _from_json(body: str) -> str:
    """Ekspor ekstensi (Cookie-Editor / EditThisCookie): daftar {name, value, domain}."""
    try:
        data = json.loads(body)
    except ValueError:
        return ""
    if isinstance(data, dict):
        data = data.get("cookies") or data.get("cookie") or []
        if isinstance(data, str):
            return _normalize(data)
    if not isinstance(data, list):
        return ""
    items = [d for d in data if isinstance(d, dict) and d.get("name")]
    own = [d for d in items if "fastmoss" in str(d.get("domain", "")).lower()]
    return "; ".join(f"{d['name']}={d.get('value', '')}" for d in (own or items))


def detect_cookie(text: str) -> tuple[str, str]:
    """Kenali format teks tempelan secara otomatis. Kembalikan ``(cookie, nama_format)``.

    Dikenali: cookie mentah, baris ``Cookie:`` (boleh di tengah blok header lengkap), cURL bash maupun
    Windows cmd (dengan ``^``), PowerShell, fetch/Node.js, ekspor JSON ekstensi cookie, dan tabel
    cookie DevTools (kolom dipisah tab). Bila ada beberapa request sekaligus, diambil yang pertama.
    """
    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip().lstrip("﻿")
    if raw[:1] in "[{":
        cookie = _from_json(raw)
        if cookie:
            return cookie, "JSON ekstensi cookie"
    body = "\n".join(ln for ln in raw.splitlines() if not ln.strip().startswith("#")).strip()
    if not body:
        return "", ""

    if re.search(r"\bcurl(\.exe)?\b", body, re.I):
        flat = re.sub(r"(\\|\^|`)\n", " ", body)
        for block in re.split(r"(?=\bcurl(?:\.exe)?\s)", flat, flags=re.I):   # "Copy all as cURL" -> per request
            for name, pat, unescape in _CURL_PATTERNS:
                m = re.search(pat, " " + block, re.I | re.S)
                if m:
                    return _normalize(unescape(m.group(1))), name
        return "", "cURL"

    if re.search(r"System\.Net\.Cookie\(", body):          # "Copy as PowerShell"
        pairs = re.findall(r'System\.Net\.Cookie\(\s*"((?:[^"`]|`.)*)"\s*,\s*"((?:[^"`]|`.)*)"', body)
        unq = lambda s: re.sub(r"`(.)", r"\1", s)              # noqa: E731
        return "; ".join(f"{unq(k)}={unq(v)}" for k, v in pairs), "PowerShell"

    m = re.search(r"""["']cookie["']\s*[:=]\s*("(?:[^"\\]|\\.)*")""", body, re.I)  # fetch / Node.js / PS -Headers
    if m:
        try:
            return _normalize(json.loads(m.group(1))), "fetch / Node.js"
        except ValueError:
            pass

    lines = [ln for ln in body.splitlines() if ln.strip()]
    m = re.search(r"^\s*cookie\s*:\s*(.+)$", body, re.I | re.M)
    if m and (len(lines) > 1 or not body.lower().startswith("cookie")):
        return _normalize(m.group(1)), "blok header"
    for i, ln in enumerate(lines[:-1]):                      # panel Headers DevTools: "cookie" lalu nilainya
        if ln.strip().lower() == "cookie":
            return _normalize(lines[i + 1]), "blok header"

    if sum("\t" in ln for ln in lines) >= max(1, len(lines) // 2):   # tabel Application > Cookies
        rows = [ln.split("\t") for ln in lines if "\t" in ln]
        rows = [r for r in rows if r[0].strip() and r[0].strip().lower() != "name"]
        return "; ".join(f"{r[0].strip()}={r[1].strip() if len(r) > 1 else ''}" for r in rows), "tabel DevTools"

    body = re.sub(r"^\s*cookie\s*:\s*", "", body, flags=re.I)
    return _normalize(body), "cookie mentah"


def parse_cookie_text(text: str) -> str:
    """Ambil string cookie dari teks bebas (format dikenali otomatis — lihat ``detect_cookie``)."""
    return detect_cookie(text)[0]


def _normalize(cookie: str) -> str:
    parts, seen = [], set()
    for chunk in re.split(r";\s*|\n+", cookie):
        name, eq, value = chunk.strip().partition("=")
        name = name.strip()
        if not eq or not name or re.search(r"[\s\"';,]", name) or name in seen:
            continue
        seen.add(name)
        parts.append(f"{name}={value.strip()}")
    return "; ".join(parts)


def cookie_get(cookie: str, name: str) -> str | None:
    for chunk in cookie.split(";"):
        k, _, v = chunk.strip().partition("=")
        if k == name:
            return v
    return None


class CookieStore:
    """Membaca file cookie dengan cache berbasis mtime, jadi edit file langsung berlaku."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._mtime: float | None = None
        self._cookie = ""
        self._label = ""

    def get(self) -> str:
        try:
            mtime = self.path.stat().st_mtime
        except FileNotFoundError:
            self._mtime, self._cookie, self._label = None, "", ""
            return ""
        if mtime != self._mtime:
            text = self.path.read_text(encoding="utf-8", errors="replace")
            self._cookie, self._label = parse_cookie_text(text), parse_label(text)
            self._mtime = mtime
        return self._cookie

    def label(self) -> str:
        self.get()
        return self._label

    def status(self) -> CookieStatus:
        cookie = self.get()
        updated = None
        if self._mtime:
            updated = datetime.fromtimestamp(self._mtime).isoformat(timespec="seconds")
        return CookieStatus(
            exists=bool(cookie),
            has_session=bool(cookie_get(cookie, SESSION_KEY)),
            length=len(cookie),
            updated_at=updated,
            path=str(self.path),
            label=self._label,
        )

    def save(self, text: str, label: str | None = None) -> str:
        """Simpan cookie baru (atomik: tulis file sementara lalu ganti). Kembalikan cookie hasil parse.

        Nama akun lama dipertahankan kecuali ``label`` diisi."""
        cookie, fmt = detect_cookie(text)
        if not cookie and fmt.startswith("cURL"):
            raise ValueError("cURL terbaca, tapi tidak berisi cookie. Pastikan sudah login di FastMoss dan salin "
                             "dari request www.fastmoss.com/api/… (bukan request gambar/analitik).")
        if not cookie:
            raise ValueError("Cookie tidak terbaca. Tempel cURL, header 'Cookie:', isi cookie, "
                             "atau ekspor JSON ekstensi cookie.")
        self.write(self.label() if label is None else label, cookie)
        return cookie

    def set_label(self, label: str) -> None:
        """Ganti nama akun tanpa menyentuh cookie-nya."""
        self.write(label, self.get())

    def write(self, label: str, cookie: str = "") -> None:
        """Tulis file akun (template + ``# nama:`` + cookie) secara atomik."""
        label = " ".join((label or "").split())[:60]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".cookies-", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(TEMPLATE_HEADER)
                fh.write(f"# nama: {label}\n")
                if cookie:
                    fh.write(cookie + "\n")
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        self._mtime = None
