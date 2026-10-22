"""Halaman "Tren Pasar": denyut pasar, panorama kategori, dan strategi pemasaran.

Paket gratis FastMoss hanya membuka data **harian** untuk **seluruh kategori** di negara terpilih;
filter kategori dan periode mingguan/bulanan dikunci (MAG_AUTH_3016), dan semua endpoint
"Strategi Pemasaran" (analysis/V2/*) dikunci (MAG_AUTH_3024). Kontrolnya tetap ada supaya akun
berlangganan bisa memakainya.
"""
from __future__ import annotations

from . import settings
from .catalog import Col, M, N, T, Control, product
from .details import Section, run_section

PERIOD = Control("date_type", "Periode", "select", [[1, "Harian"], [2, "Mingguan"], [3, "Bulanan"]], 1)
CATEGORY = Control("pcid", "Kategori", "dynselect", source="market", key="category")

_TOP_COLS = [product(sub="shop_info.name"), Col("Harga", "price", "real_price"),
             N("Terjual (kemarin)", "yd_sold_count"), M("Omzet (kemarin)", "yd_sale_amount"),
             Col("Pertumbuhan", "pct", "sold_count_inc_rate"), N("Total terjual", "total_sold_count"),
             N("Kreator", "author_count"), N("Video", "aweme_count"), N("LIVE", "live_count"),
             Col("Komisi", "pct", "commission_rate"), Col("Rilis", "date", "launch_time")]

_OVERVIEW = "/api/analysis/GoodCategory/marketOverview"
_BASE = "/api/analysis/GoodCategory/base"
_CHART = "/api/analysis/GoodCategory/salesChart"
_PRICE = "/api/analysis/GoodCategory/priceDistribution"

PAGES = [
    {"key": "pulse", "title": "Denyut Pasar", "referer": "/id/market/market-pulse",
     "desc": "Gambaran harian pasar TikTok Shop: volume terjual, produk baru, kreator, video, dan LIVE.",
     "controls": [PERIOD, CATEGORY],
     "sections": [
         Section("summary", "Ringkasan pasar", _OVERVIEW, "kpi", root="summary", extra={"is_mock": 0},
                 fields=[N("Terjual", "sold_count"), N("Produk terjual", "sold_product_count"),
                         N("Produk baru", "new_product_count"), N("Kreator berjualan", "author_cnt"),
                         N("Video jualan", "video_cnt"), N("LIVE jualan", "live_cnt"),
                         M("Harga jual rata-rata", "avg_sale_amount"),
                         T("Konsentrasi pasar", "market_concentration_percent")]),
         Section("trend", "Tren beberapa hari terakhir", _OVERVIEW, "line", root="list", extra={"is_mock": 0},
                 x="date", series=[N("Terjual", "sold_count"), N("Produk terjual", "sold_product_count"),
                                   N("Produk baru", "new_product_count"), N("Kreator", "author_cnt"),
                                   N("Video", "video_cnt"), N("LIVE", "live_cnt")], wide=True),
         Section("rank", "Peringkat kategori", "/api/analysis/GoodCategory/marketRankList", "table",
                 root="list", paged=True,
                 fields=[Col("Kategori", "entity", key="category_name", sub="region_name"),
                         N("Terjual", "category_sold_count"), T("Terjual YoY", "category_sold_count_yoy_rate"),
                         T("Omzet YoY", "category_sale_amount_yoy_rate"),
                         T("Pangsa produk teratas", "top_product_shares"), T("Pangsa toko teratas", "top_shop_shares"),
                         T("Trafik video", "traffic.video_rate_show"), T("Trafik LIVE", "traffic.live_rate_show"),
                         T("Trafik lain", "traffic.other_rate_show")], wide=True),
     ]},
    {"key": "category", "title": "Panorama Kategori", "referer": "/id/market/market-pulse",
     "desc": "Volume, produk terlaris, produk viral, dan sebaran harga per kategori.",
     "controls": [PERIOD, CATEGORY],
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
                 fields=[Col("Kategori", "entity", key="category_name", sub="region_name"),
                         N("Terjual", "category_count"), M("Omzet", "category_amount"),
                         T("Perubahan", "category_rate"), Col("Porsi omzet (%)", "num", "category_amount_percent")],
                 wide=True),
     ]},
    {"key": "strategy", "title": "Strategi Pemasaran", "referer": "/id/market/marketing-strategy",
     "desc": "Analisis mendalam pasar: tren omzet, sebaran kategori, rentang harga, kreator, dan produk teratas.",
     "controls": [PERIOD, CATEGORY],
     "sections": [
         Section("overview", "Ikhtisar pasar", "/api/analysis/V2/overview", "kpi"),
         Section("saleTrend", "Tren penjualan", "/api/analysis/V2/saleTrend", "kpi"),
         Section("catDist", "Sebaran kategori", "/api/analysis/V2/categoryDistribution", "kpi"),
         Section("saleRange", "Rentang harga laris", "/api/analysis/V2/saleRange", "kpi"),
         Section("authorRect", "Peta kreator", "/api/analysis/V2/authorRect", "kpi"),
         Section("top3", "3 produk teratas", "/api/analysis/V2/top3Goods", "kpi"),
         Section("topGoods", "Produk teratas", "/api/analysis/V2/topGoodList", "table", root="list"),
         Section("priceList", "Daftar harga", "/api/analysis/V2/priceList", "kpi"),
     ]},
]
PAGE_BY_KEY = {p["key"]: p for p in PAGES}

MARKET_PAGES = [
    {"key": p["key"], "title": p["title"], "desc": p["desc"],
     "controls": [c.__dict__ for c in p["controls"]],
     "sections": [s.public() for s in p["sections"]]}
    for p in PAGES
]


async def fetch_market(page: str, section: str, query: dict, region: str) -> dict:
    pg = PAGE_BY_KEY.get(page)
    sec = next((s for s in pg["sections"] if s.key == section), None) if pg else None
    if not sec:
        return {"status": "error", "message": "Bagian tidak dikenal."}
    params: dict = {"region": region}
    for c in pg["controls"]:
        v = query.get(c.param)
        if v not in (None, ""):
            params[c.param] = v
    if str(params.get("date_type", "1")) == "1":
        params.pop("date_type", None)   # harian = bawaan FastMoss
    return await run_section(sec, params, query, region, settings.BASE_URL + pg["referer"])
