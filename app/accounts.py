"""Multi-akun FastMoss: SATU file ``config/cookies_akun_<N>.txt`` = SATU akun.

* Tiap akun punya klien sendiri (cache, jeda, dan status paket terpisah), jadi data akun gratis
  dan akun berlangganan tidak tercampur.
* Tiap pengguna memilih akunnya sendiri di aplikasi; browser mengirim pilihannya lewat header
  ``X-FM-Account``. Tanpa pilihan -> ``FM_DEFAULT_ACCOUNT`` atau akun bernomor terkecil.
* Kode lain cukup memakai ``client`` (proxy) — otomatis mengarah ke akun milik request yang sedang jalan.
"""
from __future__ import annotations

import contextvars
import logging
import os
import re
from pathlib import Path

from . import settings
from .fastmoss.client import FastMossClient
from .fastmoss.cookies import CookieStore, parse_label

log = logging.getLogger("app")

FILE_RE = re.compile(r"^cookies_akun_(\d+)\.txt$", re.I)
HEADER = "x-fm-account"
LEGACY_FILE = "cookies.txt"          # file tunggal versi sebelumnya -> dipindah jadi akun 1

_current: contextvars.ContextVar[str | None] = contextvars.ContextVar("fm_account", default=None)


class AccountRegistry:
    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self._clients: dict[str, FastMossClient] = {}

    # --- daftar akun ---------------------------------------------------------------
    def path(self, acc_id: str) -> Path:
        return self.folder / f"cookies_akun_{acc_id}.txt"

    def ids(self) -> list[str]:
        try:
            names = os.listdir(self.folder)
        except FileNotFoundError:
            return []
        found = [m.group(1) for m in map(FILE_RE.match, names) if m]
        return sorted({str(int(i)) for i in found}, key=int)

    def default_id(self) -> str:
        ids = self.ids()
        if settings.DEFAULT_ACCOUNT in ids:
            return settings.DEFAULT_ACCOUNT
        return ids[0] if ids else "1"

    def resolve(self, acc_id: str | None) -> str:
        acc_id = str(acc_id or "").strip()
        return acc_id if acc_id in self.ids() else self.default_id()

    def client(self, acc_id: str | None = None) -> FastMossClient:
        acc_id = self.resolve(acc_id if acc_id is not None else _current.get())
        cl = self._clients.get(acc_id)
        if cl is None:
            cl = self._clients[acc_id] = FastMossClient(CookieStore(self.path(acc_id)))
        return cl

    def label(self, acc_id: str) -> str:
        return self.client(acc_id).cookies.label() or f"Akun {acc_id}"

    # --- kelola ----------------------------------------------------------------------
    def create(self, label: str = "") -> str:
        """Buat slot akun kosong berikutnya (nomor = terbesar + 1)."""
        ids = self.ids()
        acc_id = str(int(ids[-1]) + 1 if ids else 1)
        CookieStore(self.path(acc_id)).write(label or f"Akun {acc_id}")
        return acc_id

    def migrate_legacy(self) -> None:
        """Versi lama memakai satu ``config/cookies.txt`` -> jadikan ``cookies_akun_1.txt`` (sekali saja)."""
        legacy = self.folder / LEGACY_FILE
        if self.ids() or not legacy.exists():
            return
        text = legacy.read_text(encoding="utf-8", errors="replace")
        store = CookieStore(self.path("1"))
        if store.get() == "" and text.strip():
            os.replace(legacy, self.path("1"))
            if not parse_label(text):
                store.set_label("Akun 1")
            log.info("config/cookies.txt dipindah menjadi config/cookies_akun_1.txt")

    async def summary(self, acc_id: str) -> dict:
        """Status satu akun untuk tampilan (TANPA nilai cookie / path)."""
        cl = self.client(acc_id)
        acc = dict(await cl.account())
        ck = {k: v for k, v in acc.pop("cookie").items() if k != "path"}
        return {"id": acc_id, "label": self.label(acc_id), "file": self.path(acc_id).name,
                "cookie": ck, **acc}

    def clear_cache(self) -> None:
        for cl in self._clients.values():
            cl.clear_cache()

    async def close(self) -> None:
        for cl in self._clients.values():
            await cl.close()


class _CurrentClient:
    """Proxy: atribut diteruskan ke klien akun milik request yang sedang berjalan."""

    def __getattr__(self, name: str):
        return getattr(registry.client(), name)


registry = AccountRegistry(settings.COOKIE_DIR)
client = _CurrentClient()


class AccountMiddleware:
    """Middleware ASGI: baca pilihan akun dari header ``X-FM-Account`` (atau ``?acc=``) per request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        acc = ""
        for k, v in scope.get("headers") or []:
            if k == HEADER.encode():
                acc = v.decode("latin-1")
                break
        if not acc:
            m = re.search(rb"(?:^|&)acc=(\d+)", scope.get("query_string") or b"")
            acc = m.group(1).decode() if m else ""
        token = _current.set(registry.resolve(acc))
        try:
            await self.app(scope, receive, send)
        finally:
            _current.reset(token)


def current_id() -> str:
    return _current.get() or registry.default_id()
