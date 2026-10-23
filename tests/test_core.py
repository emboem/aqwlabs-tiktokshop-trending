"""Uji unit inti — tanpa jaringan."""
import datetime as dt

from app.catalog import MENUS, MENU_BY_KEY, build_params, default_period_value
from app.details import DETAILS
from app.fastmoss.cookies import CookieStore, cookie_get, parse_cookie_text
from app.fastmoss.client import strip_markup, classify
from app.fastmoss.signer import fm_sig, fm_sign
from app.market import MARKET_PAGES
from app.routes.export import cell_value, table_matrix, to_csv, to_xlsx, to_pdf
from app.catalog import Col


def test_signer_vector():
    # vektor dari request asli halaman pencarian produk FastMoss (Okt 2026)
    params = {"page": 1, "pagesize": 10, "order": "2,2", "region": "ID", "words": "alquran al muhaddits",
              "last_date_type": 28, "_time": 1792639911, "cnonce": 68270541}
    assert fm_sign(params) == "5b690ce58534741ae5bd0cd8a9480985"
    assert fm_sig("/api/goods/V2/search", params) ==         "g01623nx8ul82vzto2t0mp3fkw9gedjr84xgqhvp4ax2id71g8headj7021oqfvd"


def test_parse_cookie_formats():
    raw = "fd_tk=abc; NEXT_LOCALE=id"
    assert cookie_get(parse_cookie_text(raw), "fd_tk") == "abc"
    assert cookie_get(parse_cookie_text("Cookie: " + raw), "fd_tk") == "abc"
    curl = "curl 'https://www.fastmoss.com/api/x' -H 'accept: */*' -b 'fd_tk=abc; NEXT_LOCALE=id'"
    assert cookie_get(parse_cookie_text(curl), "fd_tk") == "abc"
    curl2 = 'curl "https://www.fastmoss.com/api/x" -H "cookie: fd_tk=abc; x=1"'
    assert cookie_get(parse_cookie_text(curl2), "fd_tk") == "abc"


def test_cookie_store_roundtrip(tmp_path):
    st = CookieStore(tmp_path / "cookies.txt")
    assert not st.status().exists
    st.save("Cookie: fd_tk=zzz; a=b")
    assert st.get() and cookie_get(st.get(), "fd_tk") == "zzz"
    s = st.status()
    assert s.exists and s.has_session


def test_classify():
    assert classify({"code": 200, "data": {"a": 1}}).ok
    locked = classify({"code": "MAG_AUTH_3017", "data": {"fake": 1}})
    assert locked.status == "locked"
    assert classify({"code": "MSG_30001", "msg": "Silakan masuk"}).status == "auth"
    mock = classify({"code": 200, "data": {"is_mock": 1, "attributes": [{"name": "x"}]}})
    assert mock.status == "locked" and mock.data is None


def test_default_period_value():
    d = dt.date(2026, 10, 22)
    assert default_period_value(1, d) == "2026-10-21"
    assert default_period_value(2, d) == "2026-42"
    assert default_period_value(3, d) == "2026-09"


def test_build_params_filters_unknown_keys():
    m = MENU_BY_KEY["product-sales"]
    p = build_params(m, {"date_type": "2", "evil": "x", "l1_cid": "14"})
    assert "evil" not in p and p["l1_cid"] == "14" and p["order"] == "1,2"
    assert p["date_value"] and p["page"] == 1


def test_catalog_integrity():
    keys = [m.key for m in MENUS]
    assert len(keys) == len(set(keys)) == 30
    for m in MENUS:
        assert m.columns and m.path.startswith("/api/")
    for d in DETAILS.values():
        for _, secs in d.tabs:
            for k in secs:
                assert k in d.by_key, (d.kind, k)
    assert {p["key"] for p in MARKET_PAGES} == {"pulse", "category", "strategy", "category-daily", "insights"}


def test_export_writers():
    cols = [Col("Produk", "entity", key="title", sub="shop", id="pid", link="product"),
            Col("Terjual", "num", "sold"), Col("Tags", "tags", "cats"), Col("Waktu", "ts", "t"),
            Col("Iklan", "bool", "ad"), Col("Tren", "spark", "trend")]
    rows = [{"title": "Baju\x0bmerah", "shop": "Toko A", "pid": "1", "sold": "1200", "cats": ["A", "B"], "t": 1792600000, "ad": 1}]
    header, body = table_matrix(cols, rows)
    assert "Tren" not in header and body[0][4] == 1200 and body[0][5] == "A, B" and body[0][7] == "Ya"
    assert cell_value(Col("x", "dur", "d"), {"d": 3725}) == "01:02:05"
    assert to_xlsx("Uji", header, body, "catatan")[:2] == b"PK"
    assert to_csv(header, body).startswith("\ufeff".encode())
    assert to_pdf("Uji", header, body, "catatan")[:4] == b"%PDF"


def test_strip_markup_highlight():
    raw = {"product_list": [{"title": "Alquran Kecil <span style='color:red'>Al</span>-Qur'an <SPAN style=\"color:red\">Muhaddits</SPAN> &amp; Tajwid",
                             "price": 58229, "tags": ["<b>Buku</b>", "Size <3"]}]}
    out = strip_markup(raw)["product_list"][0]
    assert out["title"] == "Alquran Kecil Al-Qur'an Muhaddits & Tajwid"
    assert out["tags"] == ["Buku", "Size <3"]
    assert out["price"] == 58229
    res = classify({"code": 200, "msg": "ok", "data": raw})
    assert "<span" not in res.data["product_list"][0]["title"]
