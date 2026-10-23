"""Halaman "Tren Pasar": Ikhtisar Pasar, Panorama Kategori, Strategi Pemasaran (+ Kinerja Kategori harian).

Mengikuti halaman FastMoss ``/market/market-pulse`` (tab 1–3):

* Ikhtisar Pasar  : Harian / Mingguan / Bulanan + kalender (paling awal 2024-12-01).
* Panorama Kategori & Strategi Pemasaran : "28 hari terakhir" atau Bulanan (+ kalender bulan).
  Pada Strategi Pemasaran FastMoss tidak mengirim ``date_type`` sama sekali; hanya ``date_value``
  (bulan) bila memilih Bulanan.
* Semua request membawa ``is_mock=0`` — Lite tidak pernah memakai "mode contoh" FastMoss.

Paket gratis FastMoss hanya membuka data **harian** untuk **seluruh kategori**; sisanya dikunci
(MAG_AUTH) dan ditampilkan sebagai terkunci.
"""
from __future__ import annotations

from . import settings
from .catalog import TS, Col, M, N, T, Control, default_period_value, period, product, select, shop
from .details import Section, ad, run_section

MARKET_MIN = "2024-12-01"            # kalender Tren Pasar FastMoss mulai Desember 2024
PERIOD_PULSE = period(min=MARKET_MIN)
PERIOD_28 = period(options=[[4, "28 hari terakhir"], [3, "Bulanan"]], default=4, min=MARKET_MIN, picker=[3])
PERIOD_OLD = Control("date_type", "Periode", "select", [[1, "Harian"], [2, "Mingguan"], [3, "Bulanan"]], 1)
CATEGORY = Control("pcid", "Kategori", "dynselect", source="market", key="category")
NOTE_PCID = "Pilih kategori di atas untuk melihat bagian ini."

D = lambda label, key: Col(label, "date", key)          # noqa: E731
CAT = Col("Kategori", "entity", key="category_name", sub="region_name")

_TOP_COLS = [product(sub="shop_info.name"), Col("Harga", "price", "real_price"),
             N("Terjual (kemarin)", "yd_sold_count"), M("Omzet (kemarin)", "yd_sale_amount"),
             Col("Pertumbuhan", "pct", "sold_count_inc_rate"), N("Total terjual", "total_sold_count"),
             N("Kreator", "author_count"), N("Video", "aweme_count"), N("LIVE", "live_count"),
             Col("Komisi", "pct", "commission_rate"), Col("Rilis", "date", "launch_time")]

_OVERVIEW = "/api/analysis/GoodCategory/marketOverview"
_BASE = "/api/analysis/GoodCategory/base"
_CHART = "/api/analysis/GoodCategory/salesChart"
_PRICE = "/api/analysis/GoodCategory/priceDistribution"
_V2 = "/api/analysis/V2/"
_MOCK = {"is_mock": 0}


def _pop(label, key):
    return Col(label, "pct", key, hint="% dibanding periode sebelumnya (angka FastMoss sudah dalam persen)")


# --------------------------------------------------------------------------- Strategi: jalur penjualan
CMP = [["mom", "vs periode lalu"], ["yoy", "vs tahun lalu"]]
_CHANNELS = [("total_sale_count", "Total terjual"), ("product_card_sale_count", "Lewat kartu produk"),
             ("video_sale_count", "Lewat video"), ("live_sale_count", "Lewat LIVE")]
_PROMO = [("authors_sale_count", "Total lewat kreator"), ("shop_author_sale_count", "Kreator affiliate (independen)"),
          ("brand_author_sale_count", "Akun milik penjual")]


def _cmp_fields(items, cmp, share=True):
    out = []
    for k, lab in items:
        out.append(N(lab, f"sold.{k}"))
        if share and not k.startswith(("total", "authors")):
            out.append(T(f"Porsi {lab.lower()}", f"current.{k}_rate_show"))
        out.append(T(f"{lab} — {'vs periode lalu' if cmp == 'mom' else 'vs tahun lalu'}", f"{cmp}.{k}_{cmp}_rate_show"))
    return out


def _cmp_section(key, title, root, items, note):
    return Section(key, title, _V2 + "saleRange", "kpi", root=root, extra=_MOCK, note=note,
                   fields=_cmp_fields(items, "mom"), sync="sr",
                   controls=[Control("cmp", "Bandingkan", "view", [list(o) for o in CMP], "mom", local=True)],
                   alt={"cmp": {"yoy": {"fields": _cmp_fields(items, "yoy")}}})


def _trend_section(key, title, root):
    return Section(key, title, _V2 + "saleTrend", "bars", root=root + ".{m}", x="range", extra=_MOCK, sync="st",
                   series=[N("Terjual", "value_count"), T("Porsi", "value_rate_show")],
                   alt={"m": {"product": {"series": [N("Jumlah produk", "value_count"), T("Porsi", "value_rate_show")]}}},
                   controls=[select("rate_type", "Pembanding", [[1, "Periode sebelumnya"], [2, "Tahun lalu"]], 1),
                             Control("m", "Data", "view", [["sales", "Volume penjualan"], ["product", "Jumlah produk"]],
                                     "sales")])


PAGES = [
    {"key": "pulse", "title": "Ikhtisar Pasar", "referer": "/id/market/market-pulse?tab=1", "rule": "pulse",
     "desc": "Gambaran industri TikTok Shop: volume terjual, produk baru, kreator, video, LIVE, dan konsentrasi pasar.",
     "controls": [PERIOD_PULSE, CATEGORY],
     "sections": [
         Section("summary", "Gambaran umum industri", _OVERVIEW, "kpi", root="summary", extra=_MOCK,
                 note="Angka berawalan Δ = perubahan (%) dibanding periode sebelumnya. "
                      "Konsentrasi pasar = porsi 10 toko teratas; < 20% berarti pasar ramah pemain baru.",
                 fields=[N("Terjual", "sold_count"), _pop("Δ Terjual (%)", "sold_count_pop"),
                         N("Produk terjual", "sold_product_count"), _pop("Δ Produk terjual (%)", "sold_product_count_pop"),
                         N("Produk baru", "new_product_count"), _pop("Δ Produk baru (%)", "new_product_count_pop"),
                         N("Kreator berjualan", "author_cnt"), _pop("Δ Kreator (%)", "author_cnt_pop"),
                         N("Video jualan", "video_cnt"), _pop("Δ Video (%)", "video_cnt_pop"),
                         N("LIVE jualan", "live_cnt"), _pop("Δ LIVE (%)", "live_cnt_pop"),
                         M("Harga jual rata-rata", "avg_sale_amount"),
                         T("Δ Harga rata-rata", "avg_category_sale_price_mom_rate_show"),
                         T("Konsentrasi pasar", "market_concentration_percent"),
                         _pop("Δ Konsentrasi (%)", "market_concentration_mom_percent")]),
         Section("trend", "Tren periode ini", _OVERVIEW, "line", root="list", extra=_MOCK,
                 x="date", series=[N("Terjual", "sold_count"), N("Produk terjual", "sold_product_count"),
                                   N("Produk baru", "new_product_count"), N("Kreator", "author_cnt"),
                                   N("Video", "video_cnt"), N("LIVE", "live_cnt"),
                                   _pop("Δ Terjual (%)", "sold_count_pop")], wide=True),
         Section("rank", "Peringkat kategori", "/api/analysis/GoodCategory/marketRankList", "table",
                 root="list", paged=True, extra=_MOCK,
                 fields=[CAT, N("Terjual", "category_sold_count"), T("Terjual YoY", "category_sold_count_yoy_rate"),
                         T("Omzet YoY", "category_sale_amount_yoy_rate"),
                         T("Pangsa produk teratas", "top_product_shares"), T("Pangsa toko teratas", "top_shop_shares"),
                         T("Trafik video", "traffic.video_rate_show"), T("Trafik LIVE", "traffic.live_rate_show"),
                         T("Trafik lain", "traffic.other_rate_show")], wide=True),
     ]},
    {"key": "category", "title": "Panorama Kategori", "referer": "/id/market/market-pulse?tab=2", "rule": "cat",
     "desc": "Kuadran pasar (ukuran × pertumbuhan), peringkat kategori, 10 produk terlaris, dan harga rata-rata harian.",
     "controls": [PERIOD_28, CATEGORY],
     "sections": [
         Section("quadrant", "Kuadran pasar: ukuran × pertumbuhan", _V2 + "categoryDistribution", "scatter",
                 extra=_MOCK, x="category_name", wide=True,
                 note="Sumbu-X = omzet periode ini, sumbu-Y = pertumbuhan vs periode lalu. Garis putus-putus = "
                      "rata-rata/median. Kanan-atas: pasar utama (besar & tumbuh — prioritas); kiri-atas: pasar "
                      "yang belum banyak dimanfaatkan (kecil tapi tumbuh — peluang ekspansi); kanan-bawah: pasar "
                      "yang stabil (besar, matang); kiri-bawah: pasar yang sedang dikembangkan (ceruk/menurun).",
                 series=[M("Omzet", "cur_sale_amount"), T("Pertumbuhan", "category_sale_amount_mom_rate")],
                 profile={"rows": "dots", "ref": {"Rata-rata": "avg", "Median": "middle_avg"},
                          "ref_x": "avg_gmv_amount", "ref_y": "avg_rate"}),
         Section("catDist", "Sebaran omzet per kategori", _V2 + "categoryDistribution", "table", root="dots",
                 extra=_MOCK,
                 fields=[CAT, M("Omzet", "cur_sale_amount"), M("Omzet periode lalu", "last_sale_amount"),
                         T("Perubahan", "category_sale_amount_mom_rate")], wide=True),
         Section("rankV2", "Peringkat kategori", _V2 + "marketRankList", "table", root="list", paged=True,
                 extra=_MOCK,
                 fields=[CAT, N("Terjual", "category_sold_count"), T("Terjual YoY", "category_sold_count_yoy_rate_show"),
                         T("Omzet YoY", "category_sale_amount_yoy_rate_show"),
                         T("Pangsa 10 produk teratas", "top_product_shares_show"),
                         T("Pangsa 10 toko teratas", "top_shop_shares_show"),
                         T("Trafik video", "traffic.video_rate_show"), T("Δ video", "traffic.inc_video_rate_show"),
                         T("Trafik LIVE", "traffic.live_rate_show"), T("Δ LIVE", "traffic.inc_live_rate_show"),
                         T("Trafik lain", "traffic.other_rate_show")], wide=True),
         Section("top3", "3 produk teratas kategori", _V2 + "top3Goods", "table", root="list", extra=_MOCK,
                 note=NOTE_PCID, fields=[product(sub="region_name")]),
         Section("topGoods", "10 produk terlaris kategori", _V2 + "topGoodList", "table", root="list", paged=True,
                 extra=_MOCK, note=NOTE_PCID, wide=True,
                 fields=[product(img="product.cover", title="product.title", sub="shop.name"),
                         T("Harga", "product.real_price"), N("Terjual", "product_inc_sold_count"),
                         M("Omzet", "product_inc_sale_amount"), M("Harga rata-rata", "avg_sale_amount"),
                         T("Lewat video", "video_rate_show"), T("Lewat LIVE", "live_rate_show"),
                         T("Lewat kartu produk", "product_card_rate_show"),
                         T("Akun penjual", "shop_author_rate_show"), T("Kreator affiliate", "noshop_author_rate_show"),
                         T("Komisi", "commission_rate_show"),
                         Col("Tren 7 hari", "spark", "trend", x="dt", y="inc_sold_count"),
                         shop(img="", title="shop.name", sid="shop.seller_id", sub="shop.sold_count_show")]),
         Section("price", "Harga transaksi rata-rata harian", _V2 + "priceList", "line", root="list", x="date",
                 extra=_MOCK, note=NOTE_PCID, series=[M("Harga rata-rata", "price_amount")], wide=True),
     ]},
    {"key": "strategy", "title": "Strategi Pemasaran", "referer": "/id/market/market-pulse?tab=3", "rule": "strategy",
     "desc": "Ikhtisar kategori, analisis jalur penjualan & promosi, sebaran harga, dan matriks kreator.",
     "controls": [PERIOD_28, CATEGORY],
     "sections": [
         Section("overview", "Ikhtisar pasar", _V2 + "overview", "kpi", root="base", extra=_MOCK,
                 fields=[N("Terjual", "category_sold_count"), T("Terjual vs periode lalu", "category_sold_count_mom_rate"),
                         M("Omzet", "category_sale_amount"), M("Omzet periode lalu", "last_sale_amount"),
                         N("Produk sedang dijual", "onsale_product_count"),
                         T("Produk dijual vs periode lalu", "onsale_product_count_mom_rate"),
                         N("Produk baru", "new_product_count"), T("Produk baru vs periode lalu", "new_product_count_mom_rate"),
                         M("Harga jual rata-rata", "avg_category_sale_price_amount"),
                         T("Harga rata-rata vs periode lalu", "avg_category_sale_price_mom_rate"),
                         T("Konsentrasi pasar", "category_con_rate_show"),
                         T("Konsentrasi vs periode lalu", "category_con_rate_mom_rate_show")]),
         Section("overviewTrend", "Tren harian", _V2 + "overview", "line", root="list", x="dt", extra=_MOCK,
                 series=[N("Terjual", "inc_sold_count"), M("Omzet", "test.cur_sale_amount"),
                         N("Produk terjual", "test.cur_sold_product_count"), N("Produk baru", "test.cur_new_product_count"),
                         N("Terjual (periode pembanding)", "test.last_sold_count")], wide=True),
         _cmp_section("saleType", "Analisis jalur penjualan", "sale_type", _CHANNELS,
                      "Dari mana pembeli membeli: kartu produk (etalase/pencarian), video, atau LIVE."),
         _cmp_section("channel", "Analisis jalur promosi", "channel", _PROMO,
                      "Siapa yang mempromosikan: kreator affiliate independen vs akun milik penjual sendiri."),
         _trend_section("saleTrendCur", "Sebaran per rentang harga — periode ini", "cur_trend"),
         _trend_section("saleTrendLast", "Sebaran per rentang harga — periode pembanding", "last_trend"),
         Section("authorRect", "Matriks kreator (per jumlah pengikut)", _V2 + "authorRect", "table", root="list",
                 extra=_MOCK, wide=True,
                 controls=[select("sold_type", "Jenis kreator", [[1, "Semua"], [2, "Akun milik penjual"],
                                                                 [3, "Kreator affiliate"]], 1)],
                 fields=[T("Pengikut", "follower_level"), N("Kreator", "author_count"),
                         T("Porsi kreator", "author_count_rate_show"), N("Terjual", "sold_count"),
                         T("Porsi terjual", "sold_count_rate_show"), M("Omzet", "sale_amount"),
                         N("Video", "video_count"), T("Porsi video", "video_count_rate_show"),
                         N("LIVE", "live_count"), T("Porsi LIVE", "live_count_rate_show"),
                         M("Omzet rata-rata/kreator", "avg_author_sale_amount"),
                         T("Porsi omzet rata-rata", "avg_author_sale_amount_rate_show")]),
     ]},
    {"key": "category-daily", "title": "Kinerja Kategori", "referer": "/id/market/market-category", "rule": "old",
     "desc": "Volume, produk terlaris, produk viral, tren 30 hari, dan sebaran harga per kategori (harian/mingguan/bulanan).",
     "controls": [PERIOD_OLD, CATEGORY],
     "sections": [
         Section("base", "Kinerja kategori", _BASE, "kpi",
                 fields=[N("Terjual", "category_sold_count"), T("Terjual YoY", "category_sold_count_yoy_rate"),
                         T("Terjual MoM", "category_sold_count_mom_rate"), N("Produk baru", "product_count"),
                         N("Produk terjual", "sales_product_count"), N("Video jualan", "sales_video_count"),
                         N("LIVE jualan", "sales_live_count"),
                         N("Rata-rata kreator/produk teratas", "top_products_statistics_info.average_affiliate_count")]),
         Section("top", "Produk terlaris", _BASE, "table", root="top_products", fields=_TOP_COLS, wide=True),
         Section("viral", "Produk viral (tumbuh tercepat)", _BASE, "table", root="viral_products",
                 fields=_TOP_COLS, wide=True),
         Section("chart", "Tren 30 hari", _CHART, "line", root="list", x="dt",
                 series=[N("Terjual", "category_sold_count"), N("Produk baru", "inc_product_count"),
                         N("Produk terjual", "sales_product_count"), N("Kreator berjualan", "sales_author_count"),
                         N("Video jualan", "sales_video_count"), N("LIVE jualan", "sales_live_count")], wide=True),
         Section("priceSales", "Terjual per rentang harga", _PRICE, "bars", root="product_sales_price_range.sales",
                 x="range_show", series=[N("Terjual", "value_count")]),
         Section("priceCount", "Jumlah produk per rentang harga", _PRICE, "bars", root="product_number_price_range",
                 x="range", series=[N("Produk", "value_count")]),
         Section("sub", "Sub-kategori", _PRICE, "table", root="sub_category_range",
                 fields=[CAT, N("Terjual", "category_count"), M("Omzet", "category_amount"),
                         T("Perubahan", "category_rate"), Col("Porsi omzet (%)", "num", "category_amount_percent")],
                 wide=True),
     ]},
]
PAGES.append(
    {"key": "insights", "title": "Wawasan Tren", "referer": "/id/creativecenter/trend-insights", "rule": "plain",
     "group": "Iklan",
     "desc": "Iklan & video teratas per kategori produk (tingkat 3) atau kata kunci — seperti Wawasan Tren FastMoss.",
     "controls": [Control("category", "Kategori", "category", source="insights", key="product_category",
                          levels=["l1_cid", "l2_cid", "l3_cid"]),
                  Control("keyword", "Kata kunci", "text")],
     "sections": [
         Section("topAds", "Video iklan teratas", "/api/da/V4/topAds", "table", root="list", paged=True, wide=True,
                 note="Pilih kategori sampai tingkat 3 atau isi kata kunci. FastMoss belum menyediakan grafik tren, "
                      "kata kunci populer, dan audiens Wawasan Tren untuk Indonesia (datanya kosong), jadi hanya "
                      "daftar iklan teratas yang ditampilkan.",
                 fields=[ad(title="video_desc", sub="product_info.title"), TS("Diunggah", "create_time"),
                         N("Tayangan", "play_count"), N("Suka", "digg_count"), T("Interaksi", "interaction_rate_show"),
                         N("ROAS", "roas"), product(img="product_info.cover", title="product_info.title",
                                                    pid="product_info.product_id", sub="product_info.price"),
                         N("Terjual (produk)", "product_info.sold_count"),
                         M("Omzet (produk)", "product_info.sale_amount")]),
     ]})
PAGE_BY_KEY = {p["key"]: p for p in PAGES}

MARKET_PAGES = [
    {"key": p["key"], "title": p["title"], "desc": p["desc"], "group": p.get("group", "Tren Pasar"),
     "controls": [c.__dict__ for c in p["controls"]],
     "sections": [s.public() for s in p["sections"]]}
    for p in PAGES
]


def market_params(pg: dict, query: dict, region: str) -> dict:
    """Parameter waktu & kategori persis seperti halaman FastMoss (berbeda per tab)."""
    params: dict = {"region": region}
    pcid = query.get("pcid")
    if pcid not in (None, ""):
        params["pcid"] = pcid
    dt = str(query.get("date_type") or next((c.default for c in pg["controls"] if c.param == "date_type"), ""))
    dv = query.get("date_value") or ""
    rule = pg.get("rule")
    if rule == "plain":                       # Wawasan Tren: kategori bertingkat / kata kunci apa adanya
        params.pop("pcid", None)
        for k in ("l1_cid", "l2_cid", "l3_cid", "keyword"):
            if query.get(k) not in (None, ""):
                params[k] = query[k]
        return params
    if rule == "old":
        if dt != "1":
            params["date_type"] = dt          # harian = bawaan FastMoss
    elif rule == "pulse":
        if dt not in ("1", "2", "3"):
            dt = "1"
        if dt != "1" or dv:
            params["date_type"] = dt
            params["date_value"] = dv or default_period_value(int(dt))
    else:                                     # cat / strategy: 28 hari terakhir (4) atau bulanan (3)
        if dt == "3":
            dv = dv or default_period_value(3)
            if rule == "cat":
                params["date_type"] = 3
            params["date_value"] = dv
        elif rule == "strategy":
            params["date_value"] = ""
    return params


async def fetch_market(page: str, section: str, query: dict, region: str) -> dict:
    pg = PAGE_BY_KEY.get(page)
    sec = next((s for s in pg["sections"] if s.key == section), None) if pg else None
    if not sec:
        return {"status": "error", "message": "Bagian tidak dikenal."}
    params = market_params(pg, query, region)
    if sec.note == NOTE_PCID and "pcid" not in params:
        return {"status": "empty", "message": NOTE_PCID, "limit": 0}
    if pg.get("rule") == "plain" and not (params.get("keyword") or params.get("l3_cid")):
        return {"status": "empty", "message": "Pilih kategori sampai tingkat 3 atau isi kata kunci dulu.", "limit": 0}
    res = await run_section(sec, params, query, region, settings.BASE_URL + pg["referer"])
    res["params"] = {k: v for k, v in params.items() if k in ("date_type", "date_value", "pcid")}
    return res
