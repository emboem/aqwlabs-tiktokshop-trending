"""Konfigurasi aplikasi. Semua bisa diubah lewat environment variable (atau file ``.env``)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


# Folder cookie FastMoss. SATU file = SATU akun: config/cookies_akun_1.txt, cookies_akun_2.txt, dst.
# Ganti cookie = edit file akun itu (atau lewat halaman Pengaturan). Tiap pengguna memilih akunnya sendiri.
COOKIE_DIR = Path(os.environ.get("FM_COOKIE_DIR", ROOT / "config"))
# Akun bawaan bagi pengguna yang belum memilih (nomor akun, mis. "1"). Kosong = akun nomor terkecil.
DEFAULT_ACCOUNT = os.environ.get("FM_DEFAULT_ACCOUNT", "").strip()

# Kata sandi tim untuk masuk ke aplikasi. Kosong = tanpa login (hanya untuk pemakaian lokal!).
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
# Kata sandi admin untuk mengganti cookie. Kosong = sama dengan APP_PASSWORD.
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "") or APP_PASSWORD
# Kunci rahasia untuk menandatangani sesi login. Wajib diisi saat disebar ke tim.
SECRET_KEY = os.environ.get("SECRET_KEY", "") or "ganti-kunci-rahasia-ini"
SESSION_DAYS = _int("SESSION_DAYS", 14)

# Jeda minimum antar-request ke FastMoss (detik) — satu akun dipakai bersama, jangan terlalu rapat.
MIN_INTERVAL = _float("FM_MIN_INTERVAL", 1.0)
# Lama cache hasil (detik). Data FastMoss diperbarui harian, jadi cache 10 menit aman.
CACHE_TTL = _int("FM_CACHE_TTL", 600)
REQUEST_TIMEOUT = _float("FM_TIMEOUT", 25.0)
RETRIES = _int("FM_RETRIES", 3)

# Akun gratis FastMoss hanya menampilkan N baris teratas (sisanya diburamkan).
# Aplikasi mengikuti aturan yang sama. 0 = tidak dibatasi (jangan, kecuali akun berlangganan).
FREE_ROW_LIMIT = _int("FM_FREE_ROW_LIMIT", 5)

# Batas baris ekspor sekali jalan (melindungi akun dari request beruntun).
EXPORT_MAX_ROWS = _int("FM_EXPORT_MAX_ROWS", 500)

DEFAULT_REGION = os.environ.get("FM_REGION", "ID")
LANG = os.environ.get("FM_LANG", "ID_ID")
USER_AGENT = os.environ.get(
    "FM_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/155.0.0.0 Safari/537.36",
)
BASE_URL = "https://www.fastmoss.com"
