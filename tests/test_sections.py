"""Setiap bagian detail/pasar harus punya definisi tampilan, supaya data akun berlangganan tidak tampil mentah
(mis. UID jadi "7.252.574,47 T", URL avatar meluber, label "common.goods.product_card")."""
from app.details import DETAILS
from app.market import PAGES
from app.services import dig

# bagian yang memang belum pernah berisi data dari FastMoss -> boleh digambar otomatis
AUTO_OK = {"market.strategy.top3", "market.strategy.topGoods"}


def _all_sections():
    for kind, det in DETAILS.items():
        for sec in det.sections:
            yield f"{kind}.{sec.key}", sec
    for pg in PAGES:
        for sec in pg["sections"]:
            yield f"market.{pg['key']}.{sec.key}", sec


def test_every_section_has_layout():
    missing = []
    for name, sec in _all_sections():
        if name in AUTO_OK:
            continue
        if sec.view in ("kpi", "kv", "table", "profile") and not sec.fields:
            missing.append(name)
        if sec.view in ("bars", "line", "pairs") and not (sec.x and sec.series):
            missing.append(name)
    assert missing == []


def test_tabs_point_to_existing_sections():
    for det in DETAILS.values():
        keys = [k for _, ks in det.tabs for k in ks]
        assert sorted(keys) == sorted(s.key for s in det.sections), det.kind


def test_dig_supports_list_index():
    assert dig({"cover_list": ["a", "b"]}, "cover_list.1") == "b"
    assert dig({"cover_list": []}, "cover_list.0") is None
