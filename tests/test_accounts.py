"""Uji multi-akun (config/cookies_akun_<N>.txt) — tanpa jaringan: akun tanpa cookie tidak menghubungi FastMoss."""
import pytest
from fastapi.testclient import TestClient

from app import accounts
from app.fastmoss.cookies import CookieStore

COOKIE = "fd_tk=abc123; NEXT_LOCALE=id"


@pytest.fixture()
def reg(tmp_path, monkeypatch):
    r = accounts.registry                     # objek tunggal yang juga dipakai routes/main
    monkeypatch.setattr(r, "folder", tmp_path)
    monkeypatch.setattr(r, "_clients", {})
    monkeypatch.setattr(accounts.settings, "DEFAULT_ACCOUNT", "")
    return r


def test_label_roundtrip_and_save_keeps_label(tmp_path):
    st = CookieStore(tmp_path / "cookies_akun_1.txt")
    st.write("Akun Gratis")
    assert st.label() == "Akun Gratis" and st.get() == ""
    st.save(f"Cookie: {COOKIE}")
    assert st.label() == "Akun Gratis" and st.get() == COOKIE
    st.set_label("Akun   Uji  ")
    assert st.label() == "Akun Uji" and st.get() == COOKIE
    assert st.status().label == "Akun Uji"


def test_registry_ids_create_and_default(reg, tmp_path):
    assert reg.ids() == [] and reg.default_id() == "1"
    for n in ("10", "2", "1"):
        (tmp_path / f"cookies_akun_{n}.txt").write_text("# nama: x\n", encoding="utf-8")
    (tmp_path / "cookies_akun_x.txt").write_text("", encoding="utf-8")     # bukan nomor -> diabaikan
    assert reg.ids() == ["1", "2", "10"]
    assert reg.create("Baru") == "11" and reg.label("11") == "Baru"
    assert reg.resolve("2") == "2" and reg.resolve("99") == "1" and reg.resolve(None) == "1"
    accounts.settings.DEFAULT_ACCOUNT = "10"
    assert reg.default_id() == "10"


def test_migrate_legacy_single_file(reg, tmp_path):
    (tmp_path / "cookies.txt").write_text(COOKIE + "\n", encoding="utf-8")
    reg.migrate_legacy()
    assert not (tmp_path / "cookies.txt").exists()
    assert reg.ids() == ["1"]
    assert reg.client("1").cookies.get() == COOKIE and reg.label("1") == "Akun 1"


def test_each_account_has_own_client(reg):
    reg.create("A")
    reg.create("B")
    assert reg.client("1") is not reg.client("2")
    assert reg.client("1").cookies.path.name == "cookies_akun_1.txt"


def test_api_picks_account_from_header(reg):
    reg.create("Akun Gratis")
    reg.create("Akun Berlangganan")
    from app.main import app
    with TestClient(app) as c:
        lst = c.get("/api/accounts").json()
        assert [a["id"] for a in lst["accounts"]] == ["1", "2"]
        assert lst["current"] == "1"
        assert all("path" not in a["cookie"] for a in lst["accounts"])          # path/cookie tidak bocor
        me = c.get("/api/account", headers={"X-FM-Account": "2"}).json()
        assert me["id"] == "2" and me["label"] == "Akun Berlangganan" and me["logged_in"] is False
        assert c.get("/api/account", headers={"X-FM-Account": "77"}).json()["id"] == "1"
        r = c.post("/api/cookie", json={"account": "2", "label": "Langganan Tim"})
        assert r.status_code == 200 and r.json()["label"] == "Langganan Tim"
        assert c.post("/api/cookie", json={"account": "9", "text": COOKIE}).status_code == 404
        new = c.post("/api/accounts", json={"label": ""}).json()
        assert new["id"] == "3" and new["file"] == "cookies_akun_3.txt"
