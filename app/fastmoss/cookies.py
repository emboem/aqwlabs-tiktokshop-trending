"""Penyimpanan cookie FastMoss di SATU file khusus (default ``config/cookies.txt``).

Isi file boleh berupa salah satu dari:
  * string cookie biasa      : ``fd_tk=...; region=ID; ...``
  * baris header             : ``Cookie: fd_tk=...``
  * perintah cURL utuh       : hasil "Copy as cURL" dari DevTools (bash maupun cmd/Windows)
Baris yang diawali ``#`` dianggap komentar.

Nilai cookie TIDAK PERNAH dikirim balik ke browser; halaman Pengaturan hanya melihat statusnya.
"""
from __future__ import annotations

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
#  Bisa juga lewat menu "Pengaturan Cookie" di aplikasi.
#  JANGAN bagikan / commit file ini — isinya kunci akun FastMoss.
# ----------------------------------------------------------------
"""

SESSION_KEY = "fd_tk"


@dataclass
class CookieStatus:
    exists: bool
    has_session: bool
    length: int
    updated_at: str | None
    path: str

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def _unescape_cmd(s: str) -> str:
    # "Copy as cURL (cmd)" di Windows memakai ^ sebagai escape.
    return re.sub(r"\^(.)", r"\1", s)


def parse_cookie_text(text: str) -> str:
    """Ambil string cookie dari teks bebas (cookie mentah / header / cURL)."""
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("#")]
    body = "\n".join(lines).strip()
    if not body:
        return ""
    if re.search(r"\bcurl\b", body, re.I):
        flat = body.replace("\\\n", " ").replace("^\n", " ")
        patterns = [
            r"""(?:-b|--cookie)\s+\^?(["'])(.*?)\^?\1""",
            r"""-H\s+\^?(["'])\^?cookie:\s*(.*?)\^?\1""",
        ]
        for pat in patterns:
            m = re.search(pat, flat, re.I | re.S)
            if m:
                return _normalize(_unescape_cmd(m.group(2)))
        return ""
    body = re.sub(r"^\s*cookie\s*:\s*", "", body, flags=re.I)
    return _normalize(body)


def _normalize(cookie: str) -> str:
    parts = []
    for chunk in re.split(r";\s*|\n+", cookie):
        chunk = chunk.strip()
        if "=" in chunk:
            parts.append(chunk)
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

    def get(self) -> str:
        try:
            mtime = self.path.stat().st_mtime
        except FileNotFoundError:
            self._mtime, self._cookie = None, ""
            return ""
        if mtime != self._mtime:
            self._cookie = parse_cookie_text(self.path.read_text(encoding="utf-8", errors="replace"))
            self._mtime = mtime
        return self._cookie

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
        )

    def save(self, text: str) -> str:
        """Simpan cookie baru (atomik: tulis file sementara lalu ganti). Kembalikan cookie hasil parse."""
        cookie = parse_cookie_text(text)
        if not cookie:
            raise ValueError("Cookie tidak terbaca. Tempel string cookie, header 'Cookie:', atau perintah cURL.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".cookies-", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(TEMPLATE_HEADER)
                fh.write(cookie + "\n")
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        self._mtime = None
        return cookie
