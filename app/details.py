"""Halaman detail (produk, toko, kreator, LIVE, video, iklan, pengiklan, agensi).

Tiap detail terdiri dari beberapa *bagian* (section). Satu bagian = satu endpoint FastMoss plus
cara menampilkannya (``view``), jadi tampilan web cukup satu penggambar generik:

* ``profile`` : kartu identitas (gambar, judul, tag, angka utama, info)
* ``kpi``     : deret angka ringkasan
* ``kv``      : daftar info label → nilai
* ``pairs``   : daftar pasangan nama/nilai dari sebuah list (mis. atribut produk)
* ``list``    : daftar teks sederhana (mis. poin penjualan)
* ``table``   : tabel berhalaman (memakai :class:`~app.catalog.Col`)
* ``line``    : grafik tren (sumbu-x tanggal)
* ``bars``    : grafik distribusi (label → nilai)

Kontrol per bagian mengikuti halaman FastMoss asli: periode (pilihan cepat + rentang kustom
≤180 hari), filter, dan urutan. Bagian dengan ``sync`` yang sama berbagi kontrol non-lokal
(mis. satu pemilih periode untuk kartu ringkasan + grafik tren + donat). Kontrol ``view`` tidak
dikirim ke FastMoss; ia memilih tampilan lewat ``alt`` (mis. Unit/Omzet pada donat yang sama).

Bagian yang dikunci paket FastMoss (MAG_AUTH) tetap didaftarkan supaya pengguna tahu datanya ada,
tapi isinya tidak pernah ditampilkan — FastMoss mengirim data contoh palsu untuk bagian terkunci.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from . import settings
from .catalog import (Col, D, G, M, N, P, T, TS, Control, active, apply_dperiod, category, creator, dperiod,
                      live, product, select, shop, video, view)
from .services import client, dig


@dataclass
class Section:
    key: str
    title: str
    path: str
    view: str
    root: str = ""                                  # path data ("" = seluruh data); boleh "{param}" & "*"
    fields: list = field(default_factory=list)      # kpi/kv: isi | table: kolom | profile: angka utama
    x: str = ""                                     # line: sumbu-x | bars/pairs: kunci label
    series: list = field(default_factory=list)      # line/bars/pairs: nilai | profile: daftar info
    extra: dict = field(default_factory=dict)       # parameter tetap tambahan
    controls: list = field(default_factory=list)    # pilihan pengguna
    paged: bool = False
    profile: dict = field(default_factory=dict)     # profile: {title, img, sub, sub_prefix, tags, url}
    note: str = ""
    wide: bool = False
    alt: dict = field(default_factory=dict)         # {param: {nilai: {root/x/series/fields/view/title}}}
    sync: str = ""                                  # grup bagian yang berbagi kontrol (periode dsb.)
    pagesize: int = 10

    def public(self) -> dict:
        d = asdict(self)
        for k in ("path", "extra", "alt"):
            d.pop(k)
        return d


@dataclass
class Opt:
    """Sumber opsi filter milik satu detail (mis. kategori produk di toko ini)."""
    path: str
    lists: dict                                     # nama daftar -> (root, kunci nilai, kunci label)
    extra: dict = field(default_factory=dict)


@dataclass
class Detail:
    kind: str
    title: str
    id_param: str
    tabs: list                                     # [[judul tab, [kunci bagian, ...]], ...]
    sections: list
    referer: str = ""
    options: dict = field(default_factory=dict)    # nama -> Opt (dipakai kontrol bersumber "@nama")
    fm_path: str = ""                              # halaman FastMoss asli (tautan "Buka di FastMoss")

    def __post_init__(self):
        self.by_key = {s.key: s for s in self.sections}

    def public(self) -> dict:
        return {"kind": self.kind, "title": self.title, "tabs": self.tabs, "fm_path": self.fm_path,
                "sections": {s.key: s.public() for s in self.sections}}


# --------------------------------------------------------------------------- helper
def sel(param, label, opts, default, local=False) -> Control:
    c = select(param, label, opts, default)
    c.local = local
    return c


def order(opts, param="order") -> Control:
    """Urutan tabel; selalu milik bagiannya sendiri."""
    return sel(param, "Urutkan", opts, opts[0][0], local=True)


def per(param="d_type", presets=None, default=28, label="Periode", custom=True, also=()) -> Control:
    """Periode detail FastMoss: pilihan cepat + (bila ``custom``) rentang bebas maks. 180 hari s/d kemarin."""
    presets = presets if presets is not None else D7_180
    if not custom:
        return sel(param, label, presets, default)
    return dperiod(param, label, presets, default, also=also)


def local(c: Control) -> Control:
    c.local = True
    return c


def ad(img="cover", title="desc", aid="id", sub="advertiser") -> Col:
    return Col("Iklan", "entity", key=title, img=img, sub=sub, id=aid, link="ad")


def advertiser(img="avatar", title="name", aid="id", sub="region_name") -> Col:
    return Col("Pengiklan", "entity", key=title, img=img, sub=sub, id=aid, link="advertiser")


D7_180 = [[7, "7 hari"], [28, "28 hari"], [90, "90 hari"], [180, "180 hari"]]
D7_14_180 = [[7, "7 hari"], [14, "14 hari"], [28, "28 hari"], [90, "90 hari"], [180, "180 hari"]]
D7_90 = [[7, "7 hari"], [28, "28 hari"], [90, "90 hari"]]
D7_ALL = [[7, "7 hari"], [28, "28 hari"], [90, "90 hari"], [-1, "Semua"]]
UNIT_GMV = [["gmv", "Omzet"], ["units_sold", "Unit terjual"]]
UNITS = {"units_sold": {"series": [N("Terjual", "sold_count")]}}
VARIANT = Col("Varian", "props", "sku_sale_props")

# ============================================================================ PRODUK
P_OV = dict(sync="ov", controls=[per("d_type", D7_180, 28)])


def _p_dist(key, title, root, x):
    return Section(key, title, "/api/goods/v3/overview", "bars", root=root + ".{m}.list", x=x,
                   series=[M("Omzet", "sale_amount")], alt={"m": UNITS},
                   sync="ov", controls=[per("d_type", D7_180, 28), view("m", "Metrik", UNIT_GMV, "gmv")])


PRODUCT = Detail("product", "Detail Produk", "product_id", referer="/id/e-commerce/detail/",
                 fm_path="e-commerce/detail", tabs=[
    ["Ringkasan", ["base", "overview", "trend", "channel", "content", "adsDist", "price", "attr", "selling"]],
    ["Analisis SKU", ["skuBest", "skuShare", "sku"]],
    ["Kreator", ["authorChart", "authorType", "authors"]],
    ["Iklan", ["invest", "investTrend", "ads"]],
    ["Video", ["videos"]],
    ["LIVE", ["lives"]],
    ["Ulasan", ["reviews"]],
    ["Produk Serupa", ["similar"]],
], sections=[
    Section("base", "Profil produk", "/api/goods/v3/base", "profile",
            profile={"title": "product.title", "img": "product.cover_list.0", "sub": "shop.name",
                     "sub_link": ["shop", "shop.seller_id"], "url": "product.detail_url",
                     "tags": ["product.category_name", "product.category_name_l2", "product.category_name_l3"]},
            fields=[Col("Harga", "price", "product.real_price"), N("Total terjual", "product.sold_count"),
                    M("Total omzet", "product.sale_amount"), N("Kreator", "product.author_count"),
                    N("Video", "product.aweme_count"), N("LIVE", "product.live_count"),
                    N("Ulasan", "product.review_count"), N("Rating", "product.product_rating")],
            series=[P("Komisi", "product.commission_rate"), Col("Harga asli", "price", "product.original_price"),
                    N("Stok", "product.stock_count"), N("Indeks viral (7 hari)", "product.viral_index"),
                    N("Indeks popularitas", "product.popularity_index"),
                    N("Peringkat negara (7 hari)", "product.country_rank"),
                    N("Peringkat kategori", "product.category_rank"), T("Ongkir", "product.transport_fee"),
                    TS("Rilis", "product.launch_time"), T("Negara", "product.region_name"),
                    Col("Produk baru", "bool", "product.is_new_product"),
                    Col("Dikelola penuh (S-shop)", "bool", "product.is_sshop"),
                    Col("Diturunkan dari etalase", "bool", "product.off_shelves"),
                    N("Terjual toko", "shop.sold_count"), M("Omzet toko", "shop.sale_amount")]),
    Section("overview", "Ringkasan penjualan", "/api/goods/v3/overview", "kpi", root="overview", **P_OV,
            fields=[N("Terjual", "sold_count"), M("Omzet", "sale_amount"),
                    N("Rata-rata terjual/hari", "avg_sold_count"), M("Rata-rata omzet/hari", "avg_sale_amount"),
                    Col("Harga transaksi rata-rata", "price", "price"),
                    N("Terjual dari video", "video_sold_count"), M("Omzet dari video", "video_sale_amount"),
                    N("Terjual dari LIVE", "live_sold_count"), M("Omzet dari LIVE", "live_sale_amount"),
                    N("Kreator", "author_count"), N("Video", "aweme_count"), N("LIVE", "live_count")]),
    Section("trend", "Tren penjualan", "/api/goods/v3/overview", "line", root="chart_list", x="dt", **P_OV,
            series=[N("Terjual harian", "inc_sold_count"), M("Omzet harian", "inc_sale_amount"),
                    N("Kreator baru", "inc_author_count"), N("Video baru", "inc_aweme_count"),
                    N("LIVE baru", "inc_live_count"), Col("Harga rata-rata", "money", "price"),
                    N("Total terjual", "sold_count"), M("Total omzet", "sale_amount"),
                    N("Total kreator", "author_count"), N("Total video", "aweme_count"),
                    N("Total LIVE", "live_count")], wide=True),
    _p_dist("channel", "Proporsi saluran transaksi", "channel_distribution", "source"),
    _p_dist("content", "Proporsi jenis konten", "content_distribution", "category"),
    _p_dist("adsDist", "Proporsi transaksi iklan", "ads_distribution", "category"),
    Section("price", "Riwayat harga (30 hari)", "/api/goods/v3/priceList", "line", root="price_list",
            x="date", series=[M("Harga", "price")]),
    Section("attr", "Atribut produk", "/api/goods/v3/goodsAttribute", "pairs", root="attributes",
            x="name", series=[T("Nilai", "value")]),
    Section("selling", "Poin penjualan", "/api/goods/v3/goodsAttribute", "list", root="selling_points",
            fields=[T("Poin", "")]),
    Section("skuBest", "SKU performa terbaik", "/api/goods/v3/productSku", "kpi", root="best_sku",
            sync="sku", controls=[sel("d_type", "Periode", [[7, "7 hari"], [28, "28 hari"]], 28)],
            fields=[T("Properti", "sku_name"), T("Varian", "sku_value"), N("Terjual", "sold_count"),
                    M("Omzet", "sale_amount"), Col("Harga", "price", "price"), N("Stok", "stock")]),
    Section("skuShare", "Porsi per varian", "/api/goods/v3/productSku", "table", root="sku_{m}.*.list",
            sync="sku", controls=[sel("d_type", "Periode", [[7, "7 hari"], [28, "28 hari"]], 28),
                                  view("m", "Metrik", [["units_sold", "Unit terjual"], ["gmv", "Omzet"],
                                                       ["stock", "Stok saat ini"]], "units_sold")],
            fields=[T("Properti", "_group"), T("Varian", "source"), T("Porsi", "propotion"),
                    N("Terjual", "sold_count")],
            alt={"m": {"gmv": {"fields": [T("Properti", "_group"), T("Varian", "source"), T("Porsi", "propotion"),
                                          M("Omzet", "sale_amount")]},
                       "stock": {"fields": [T("Properti", "_group"), T("Varian", "source"),
                                            T("Porsi", "propotion"), N("Stok", "sold_count")]}}}),
    Section("sku", "Daftar varian (SKU)", "/api/goods/v3/productSku", "table", root="sku_list",
            fields=[VARIANT, Col("Harga", "price", "real_price"), Col("Harga coret", "price", "original_price"),
                    T("Diskon", "discount"), N("Stok", "stock"), T("Diperbarui", "mtime")]),
    Section("authorChart", "Sebaran kreator per jumlah pengikut", "/api/goods/v3/authorChart", "bars",
            root="level_distribution", x="follower_level", series=[N("Kreator", "follower_count")]),
    Section("authorType", "Tipe kreator", "/api/goods/v3/authorChart", "bars",
            root="type_distribution", x="type", series=[N("Porsi (%)", "percent")]),
    Section("authors", "Kreator yang mempromosikan", "/api/goods/v3/author", "table", root="list", paged=True,
            controls=[sel("ecommerce_type", "Jenis", [["all", "Semua"], ["video", "Kreator video"],
                                                     ["live", "Kreator LIVE"]], "all"),
                      order([["2,2", "Terjual"], ["3,2", "Omzet"]])],
            fields=[creator(), G("Kategori", "category"), N("Pengikut", "follower_count"),
                    N("Terjual (produk ini)", "sold_count"), M("Omzet (produk ini)", "sale_amount"),
                    M("Omzet kreator 28h", "d28_sale_amount"), N("Video", "aweme_count"),
                    M("GPM video min.", "aweme_min_gpm"), M("GPM video maks.", "aweme_max_gpm"),
                    M("GPM LIVE min.", "live_gpm_min"), M("GPM LIVE maks.", "live_gpm_max"),
                    D("Mulai promosi", "start_promoting")]),
    Section("invest", "Analisis penempatan iklan", "/api/goods/V3/investment", "kpi", root="overview",
            sync="inv", controls=[per("d_type", D7_90, 28, custom=False)],
            note="Angka 'rata-rata' = rata-rata produk di kategori yang sama.",
            fields=[M("Estimasi biaya iklan", "estimate_cost_amount"), N("Tayangan iklan", "play_count"),
                    N("Terjual dari iklan", "sold_count"), M("Omzet dari iklan", "sale_amount"),
                    N("Jumlah materi iklan", "video_count"), T("Porsi omzet iklan", "ad_sale_percent"),
                    N("ROAS", "roas"), M("Total omzet produk", "total_sale_amount"),
                    M("Rata-rata biaya iklan", "avg_estimate_cost_amount"),
                    N("Rata-rata tayangan", "avg_play_count"), N("Rata-rata terjual", "avg_sold_count"),
                    M("Rata-rata omzet", "avg_sale_amount")]),
    Section("investTrend", "Tren iklan", "/api/goods/V3/investment", "line", root="trends", x="dt",
            sync="inv", controls=[per("d_type", D7_90, 28, custom=False)],
            series=[M("Estimasi biaya iklan", "estimate_cost_amount"), N("Tayangan", "play_count"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), N("Materi iklan", "video_count"),
                    N("ROAS", "roas")], wide=True),
    Section("ads", "Materi iklan produk", "/api/goods/V3/adsVideo", "table", root="list", paged=True,
            sync="inv", controls=[per("d_type", D7_90, 28, custom=False)],
            fields=[ad(), TS("Diunggah", "create_time"), N("Tayangan", "play_count"),
                    M("Estimasi biaya iklan", "estimate_cost_amount"), M("Omzet", "sale_amount"), N("ROAS", "roas")]),
    Section("videos", "Video terkait produk", "/api/goods/v3/video", "table", root="list", paged=True,
            controls=[sel("date_type", "Data", [[7, "7 hari"], [28, "28 hari"], [90, "90 hari"], [0, "Semua"]], 28),
                      dperiod("d_type", "Waktu publikasi", [[0, "Semua"], [7, "7 hari"], [14, "14 hari"],
                                                            [28, "28 hari"], [60, "60 hari"], [90, "90 hari"]], 0),
                      sel("is_promoted", "Status iklan", [[-1, "Semua"], [1, "Sudah diiklankan"],
                                                         [0, "Belum diiklankan"]], -1),
                      order([["1,2", "Terjual"], ["2,2", "Omzet"], ["3,2", "Tayangan"], ["4,2", "Suka"],
                             ["6,2", "Terbaru"]])],
            fields=[video(img="video.cover", title="video.video_desc", sub="author.author_nickname"),
                    D("Diunggah", "create_date"), N("Tayangan", "play_count"), N("Suka", "digg_count"),
                    N("Komentar", "comment_count"), N("Dibagikan", "share_count"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), P("Interaksi", "engagement_rate"),
                    Col("Durasi", "dur", "video.duration"),
                    M("Estimasi biaya iklan", "estimate_cost_amount"), N("ROAS", "roas"),
                    Col("Iklan", "bool", "is_ad")]),
    Section("lives", "Siaran LIVE terkait produk", "/api/goods/v3/live", "table", root="list", paged=True,
            controls=[dperiod("d_type", "Periode", D7_14_180, 28),
                      sel("live_type", "Jenis siaran", [["all", "Semua"], ["affiliate", "Siaran kreator"],
                                                        ["shop", "Siaran toko"]], "all"),
                      order([["2,2", "Terjual"], ["4,2", "Omzet"], ["3,2", "Total penonton"],
                             ["1,2", "Waktu mulai"]])],
            fields=[live(img="live_info.cover", title="live_info.title", sub="author.nickname"),
                    D("Tanggal", "create_date"), T("Durasi", "live_time"),
                    N("Terjual (produk ini)", "inc_sold_count"), M("Omzet (produk ini)", "inc_sale_amount"),
                    N("Terjual (siaran)", "sold_count"), M("Omzet (siaran)", "sale_amount"),
                    N("Total penonton", "total_user"), N("Puncak penonton", "max_user_count"),
                    N("Produk di LIVE", "product_count")]),
    Section("reviews", "Ulasan produk", "/api/goods/reviewList", "table", root="review_list", paged=True,
            controls=[sel("near_day", "Periode", [[0, "Semua"], [7, "7 hari"], [28, "28 hari"], [90, "90 hari"]], 0),
                      sel("is_like", "Jenis ulasan", [[0, "Semua"], [2, "Positif"], [1, "Kritis"]], 0)],
            fields=[T("Ulasan", "review_text"), N("Bintang", "rating"), T("Varian", "sku_info.name"),
                    T("Label", "label_list"), T("Waktu", "review_time")]),
    Section("similar", "Produk serupa", "/api/goods/v3/similarity", "table", root="list",
            fields=[product(sub="region_name"), Col("Harga", "price", "price"), N("Terjual", "sale_cnt"),
                    M("Omzet", "sale_amount"), P("Komisi", "crate"), N("Rating", "product_rating"),
                    N("Indeks viral", "viral_index"), N("Indeks popularitas", "popularity_index"),
                    G("Kategori", "category_name")]),
])

# ============================================================================ TOKO
S_RD = dict(sync="rd", controls=[per("d_type", D7_180, 28, also=("date_type",))])
S_SA = [per("d_type", D7_ALL, 28, custom=False)]
METRIC3 = [["sale_amount_by", "Omzet"], ["sold_count_by", "Terjual"], ["product_count_by", "Jumlah produk"]]
METRIC3_RANGE = [["sale_amount_range", "Omzet"], ["sold_count_range", "Terjual"], ["product_num_range", "Jumlah produk"]]


def _cnt(label_money, label_num, key):
    """alt: kolom nilai berganti jenis (uang/jumlah) mengikuti metrik."""
    return {"sale_amount_by": {"series": [M(label_money, key)]}, "sold_count_by": {"series": [N(label_num, key)]},
            "product_count_by": {"series": [N("Produk", key)]}}


def _rng(key="value"):
    return {"sale_amount_range": {"series": [M("Omzet", key)]}, "sold_count_range": {"series": [N("Terjual", key)]},
            "product_num_range": {"series": [N("Produk", key)]}}


def _s_dist(key, title, root, x):
    return Section(key, title, "/api/shop/v3/saleAnalysis", "bars", root=root + ".{m}.list", x=x,
                   series=[M("Omzet", "sale_amount")], alt={"m": UNITS}, sync="sa",
                   controls=[*S_SA, view("m", "Metrik", UNIT_GMV, "gmv")])


SHOP = Detail("shop", "Detail Toko", "id", referer="/id/shop-marketing/detail/", fm_path="shop-marketing/detail",
              options={"goodsStats": Opt("/api/shop/goodsStats", {"category": ("category_info", "category_id",
                                                                               "category_name")},
                                         extra={"order": "1,2"}),
                       "priceRange": Opt("/api/shop/v3/priceRange", {"price": ("list", "value", "label")})},
              tabs=[
    ["Tren Data", ["base", "recent", "trend"]],
    ["Transaksi", ["sale", "saleContent"]],
    ["Produk", ["productAn", "prodCat", "prodPrice", "goods"]],
    ["Kreator", ["authorAn", "authFollower", "authType", "authors"]],
    ["Akun Resmi", ["shopAuthor", "officialList"]],
    ["LIVE", ["liveSum", "lives"]],
    ["Video", ["videoSum", "videos"]],
    ["Toko Serupa", ["similar"]],
], sections=[
    Section("base", "Profil toko", "/api/shop/v3/base", "profile",
            profile={"title": "shop_name", "img": "shop_avatar", "sub": "shop_category_name",
                     "tags": ["region_name"]},
            fields=[N("Total terjual", "sold_count"), M("Total omzet", "sale_amount"),
                    N("Produk aktif", "product_count"), N("Total produk", "total_product_count"),
                    N("Kreator", "author_count"), N("Video", "video_count"), N("LIVE", "live_count"),
                    N("Peringkat negara", "rank.region_rank")],
            series=[N("Peringkat kategori", "rank.category_rank"), N("Rating toko", "shop_rate.shop_rating"),
                    T("Ketepatan kirim", "shop_rate.delivery_rate"), T("Tingkat respons", "shop_rate.response_rate"),
                    T("Ulasan positif", "shop_rate.positive_feedback_rate"),
                    T("Lebih baik dari toko lain", "shop_rate.outperform_rate"), D("Buka sejak", "ctime"),
                    N("Rata-rata terjual kategori", "avg_category_sold_count"),
                    M("Rata-rata omzet kategori", "avg_category_sale_amount"),
                    T("Akun resmi", "shop_author.nickname"), N("Pengikut akun resmi", "shop_author.follower_count"),
                    T("Data per", "mtime")]),
    Section("recent", "Ringkasan data", "/api/shop/v3/recentData", "kpi", root="list.total_info", **S_RD,
            fields=[N("Terjual", "sold_count"), M("Omzet", "sale_amount"), N("Produk terjual", "sold_product_count"),
                    N("Kreator", "author_count"), N("Video", "aweme_count"), N("LIVE", "live_count")]),
    Section("trend", "Tren data", "/api/shop/v3/recentData", "line", root="list.trend", x="dt", **S_RD,
            series=[N("Terjual harian", "inc_sold_count"), M("Omzet harian", "inc_sale_amount"),
                    N("Produk terjual", "sold_product_count"), N("Kreator baru", "inc_author_count"),
                    N("Video baru", "inc_aweme_count"), N("LIVE baru", "inc_live_count"),
                    N("Total terjual", "sold_count"), M("Total omzet", "sale_amount"),
                    N("Total kreator", "author_count"), N("Total video", "aweme_count"),
                    N("Total LIVE", "live_count")], wide=True),
    _s_dist("sale", "Proporsi saluran transaksi", "channel_distribution", "source"),
    _s_dist("saleContent", "Distribusi metode penjualan", "content_distribution", "category"),
    Section("productAn", "Analisis produk", "/api/shop/v3/productAnalysis", "kpi", root="summary",
            sync="pa", controls=S_SA,
            fields=[N("Produk sepanjang waktu", "history_product_count"), N("Produk sedang dijual", "on_sell_product_count"),
                    T("Komisi terendah", "commission_rate_min_rate"), T("Komisi tertinggi", "commission_rate_max_rate")]),
    Section("prodCat", "Sebaran per kategori", "/api/shop/v3/productAnalysis", "bars",
            root="category.{m}.{lv}", x="category_name", series=[M("Omzet", "category_count")],
            alt={"m": _cnt("Omzet", "Terjual", "category_count")}, sync="pa",
            controls=[*S_SA, view("m", "Metrik", METRIC3, "sale_amount_by"),
                      view("lv", "Tingkat", [["first_category", "Kategori utama"],
                                             ["second_category", "Sub-kategori"]], "first_category")]),
    Section("prodPrice", "Sebaran per rentang harga", "/api/shop/v3/productAnalysis", "bars",
            root="price.{m}", x="label", series=[M("Omzet", "value")], alt={"m": _cnt("Omzet", "Terjual", "value")},
            sync="pa", controls=[*S_SA, view("m", "Metrik", METRIC3, "sale_amount_by")]),
    Section("goods", "Produk toko", "/api/shop/v3/goods", "table", root="product_list", paged=True, sync="pa",
            controls=[*S_SA,
                      local(dperiod("date_type", "Waktu rilis", [[-1, "Semua"], [7, "7 hari"], [14, "14 hari"],
                                                                 [28, "28 hari"], [90, "90 hari"], [180, "180 hari"]],
                                    -1)),
                      local(category("@goodsStats")),
                      local(Control("price", "Harga", "dynselect", source="@priceRange", key="price")),
                      sel("crate", "Komisi", [["", "Semua"], ["5,10", "5–10%"], ["10,15", "10–15%"],
                                              ["15,20", "15–20%"], ["20,30", "20–30%"], ["30,", "≥30%"]], "", local=True),
                      sel("sold_count", "Terjual", [["", "Semua"], ["1,1000", "1–1rb"], ["1000,10000", "1rb–10rb"],
                                                    ["10000,", "≥10rb"]], "", local=True),
                      order([["1,2", "Terjual"], ["2,2", "Omzet"], ["3,2", "Terbaru"], ["4,2", "Komisi"]])],
            fields=[product(img="img", sub="category_name_l3"), Col("Harga", "price", "price"), P("Komisi", "crate"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount"),
                    N("Kreator", "relate_author_count"), N("Video", "relate_video_count"),
                    N("LIVE", "relate_live_count"), N("Rating", "product_rating"), D("Rilis", "ctime")]),
    Section("authorAn", "Analisis kreator", "/api/shop/v3/authorAnalysis", "kpi", root="summary",
            sync="aa", controls=S_SA,
            fields=[N("Kreator", "author_count"), N("Kreator baru", "inc_author_count"), N("Video", "video_count"),
                    N("LIVE", "live_count"), N("Terjual", "sold_count"), M("Omzet", "sale_amount")]),
    Section("authFollower", "Sebaran per jumlah pengikut kreator", "/api/shop/v3/authorAnalysis", "bars",
            root="follower_range.{m}", x="label", series=[M("Omzet", "value")], alt={"m": _rng()}, sync="aa",
            controls=[*S_SA, view("m", "Metrik", METRIC3_RANGE, "sale_amount_range")]),
    Section("authType", "Sebaran per jenis kreator", "/api/shop/v3/authorAnalysis", "bars",
            root="auther_type_range.{m}", x="label", series=[M("Omzet", "value")], alt={"m": _rng()}, sync="aa",
            controls=[*S_SA, view("m", "Metrik", METRIC3_RANGE, "sale_amount_range")]),
    Section("authors", "Daftar kreator", "/api/shop/v3/author", "table", root="list", paged=True, sync="aa",
            controls=[*S_SA,
                      sel("author_product_type", "Jenis kreator", [[3, "Semua"], [2, "Kreator LIVE"],
                                                                  [1, "Kreator video"]], 3, local=True),
                      sel("follower_count", "Pengikut", [["", "Semua"], ["1,1000", "<1rb"], ["1000,5000", "1rb–5rb"],
                                                        ["5000,10000", "5rb–10rb"], ["10000,50000", "10rb–50rb"],
                                                        ["50000,100000", "50rb–100rb"], ["100000,", "≥100rb"]], "",
                          local=True),
                      sel("sold_count", "Terjual", [["", "Semua"], ["1,1000", "1–1rb"], ["1000,10000", "1rb–10rb"],
                                                    ["10000,", "≥10rb"]], "", local=True),
                      order([["2,2", "Terjual"], ["3,2", "Omzet"], ["1,2", "Pengikut"]])],
            fields=[creator(), G("Kategori", "author_category_name"), N("Pengikut", "follower_count"),
                    N("Produk dipromosikan", "product_count"), N("Terjual", "sold_count"), M("Omzet", "sale_amount"),
                    M("GPM video maks.", "aweme_max_gpm"), M("GPM LIVE maks.", "live_gpm_max")]),
    Section("shopAuthor", "Akun resmi toko", "/api/shop/v3/shopAuthorAnalysis", "kpi", root="base",
            sync="of", controls=[per("d_type", [[7, "7 hari"], [28, "28 hari"], [90, "90 hari"], [180, "Semua"]], 28,
                                     custom=False)],
            fields=[N("Akun resmi", "shop_author_cnt"), N("Total pengikut", "shop_author_follower_total_cnt"),
                    N("Terjual", "shop_author_sold_count"), M("Omzet", "shop_author_sale_amount"),
                    N("Video", "shop_author_video_cnt"), N("Rata-rata tayangan video", "avg_shop_author_video_play_cnt"),
                    N("Rata-rata terjual/video", "avg_shop_author_video_sold_count"),
                    N("LIVE", "shop_author_live_cnt"), N("Rata-rata penonton LIVE", "avg_shop_author_enter_cnt"),
                    N("Rata-rata terjual/LIVE", "avg_shop_author_live_sold_count")]),
    Section("officialList", "Daftar akun resmi", "/api/shop/v3/shopAuthorAnalysis", "table", root="author_list",
            sync="of", controls=[per("d_type", [[7, "7 hari"], [28, "28 hari"], [90, "90 hari"], [180, "Semua"]], 28,
                                     custom=False)],
            fields=[creator(), N("Pengikut", "follower_count"), N("Video", "video_count"), N("LIVE", "live_count"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount")]),
    Section("liveSum", "Ringkasan siaran LIVE", "/api/shop/v3/liveAnalysisSummary", "kpi", sync="lv",
            controls=[dperiod("date_type", "Waktu mulai siaran", [[-1, "Semua"], [7, "7 hari"], [28, "28 hari"],
                                                                  [90, "90 hari"], [180, "180 hari"]], 28,
                              also=("d_type",)),
                      sel("is_shop", "Jenis siaran", [[0, "Semua"], [1, "Akun toko"], [2, "Kreator affiliate"]], 0)],
            fields=[N("Jumlah LIVE", "total_count"), N("Terjual", "sold_count"), M("Omzet", "sale_amount"),
                    N("Total penonton", "total_enter_count"), N("Rata-rata terjual/LIVE", "avg_sold_count"),
                    M("Rata-rata omzet/LIVE", "avg_sale_amount"), N("Rata-rata penonton/LIVE", "avg_enter_count")]),
    Section("lives", "Daftar siaran LIVE", "/api/shop/v3/liveAnalysis", "table", root="list", paged=True, sync="lv",
            controls=[dperiod("date_type", "Waktu mulai siaran", [[-1, "Semua"], [7, "7 hari"], [28, "28 hari"],
                                                                  [90, "90 hari"], [180, "180 hari"]], 28),
                      sel("is_shop", "Jenis siaran", [[0, "Semua"], [1, "Akun toko"], [2, "Kreator affiliate"]], 0),
                      order([["2,2", "Terjual"], ["6,2", "Omzet"], ["4,2", "Total penonton"], ["1,2", "Waktu mulai"]])],
            fields=[live(sub="nickname"), TS("Mulai", "create_time"), Col("Durasi", "dur", "duration"),
                    N("Terjual (toko ini)", "shop_sold_count"), M("Omzet (toko ini)", "shop_sale_amount"),
                    N("Terjual (siaran)", "sold_count"), M("Omzet (siaran)", "sale_amount"),
                    N("Total penonton", "total_user"), N("Produk", "product_count"),
                    N("Pengikut kreator", "follower_count"), G("Kategori laris", "hot_category")]),
    Section("videoSum", "Ringkasan video", "/api/shop/v3/videoAnalysisSummary", "kpi",
            sync="vd", controls=S_SA,
            fields=[N("Video jualan", "video_count"), M("Omzet dari video", "video_amount"),
                    N("Tayangan", "play_count")]),
    Section("videos", "Video jualan", "/api/shop/v3/videoAnalysis", "table", root="list", paged=True, sync="vd",
            controls=[*S_SA,
                      local(dperiod("date_type", "Waktu publikasi", [[-1, "Semua"], [7, "7 hari"], [14, "14 hari"],
                                                                     [28, "28 hari"], [90, "90 hari"], [180, "180 hari"]],
                                    180)),
                      sel("is_ad", "Status iklan", [[-1, "Semua"], [1, "Iklan"], [0, "Organik"]], -1, local=True),
                      order([["2,2", "Terjual"], ["3,2", "Omzet"], ["5,2", "Tayangan"], ["4,2", "Suka"],
                             ["1,2", "Terbaru"]])],
            fields=[video(img="cover", title="video_desc", sub="nickname"), D("Diunggah", "ctime"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), N("Tayangan", "play_cnt"),
                    N("Suka", "digg_cnt"), N("Komentar", "comment_count"), N("Dibagikan", "share_count"),
                    T("Interaksi", "interact_rate"), N("Pengikut kreator", "follower_count"),
                    Col("Iklan", "bool", "is_ad")]),
    Section("similar", "Toko serupa", "/api/shop/v3/similarity", "table", root="shop_list",
            fields=[shop(img="img", title="name", sid="id"), G("Kategori", "category_name"),
                    N("Total terjual", "sold_count"), M("Total omzet", "sale_amount"), N("Produk", "product_cnt"),
                    N("Kreator", "author_cnt"), N("Video", "aweme_cnt")]),
])

# ============================================================================ KREATOR
C_CORE = dperiod("date_type", "Periode", D7_14_180, 28)
_MONEY_FT = ("sale_amount", "video_sale_amount", "live_sale_amount", "showcase_amt")


def _datalist(key, title, opts, default):
    return Section(key, title, "/api/author/v3/detail/dataList", "line", root="list", x="key",
                   series=[N(opts[0][1], "value")], sync="core", wide=True,
                   controls=[C_CORE, sel("field_type", "Data", opts, default, local=True)],
                   alt={"field_type": {v: {"series": [(M if v in _MONEY_FT else N)(lab, "value")]}
                                       for v, lab in opts}})


def _catlist(key, title, typ):
    return Section(key, title, "/api/author/v3/detail/categoryList", "bars", root="list", x="key",
                   series=[N("Porsi (%)", "value")], extra={"type": typ},
                   controls=[sel("from", "Sumber", [["video", "Video"], ["live", "LIVE"]], "video")])


CREATOR = Detail("creator", "Detail Kreator", "uid", referer="/id/influencer/detail/", fm_path="influencer/detail",
                 options={"goodsFilter": Opt("/api/author/v3/detail/goodsFilter",
                                             {"category": ("category", "category_id", "category_name")})},
                 tabs=[
    ["Ringkasan", ["base", "index", "stat", "contact"]],
    ["Data Inti", ["dlFollow", "dlSale"]],
    ["Audiens", ["fans", "fansAge", "fansState", "fansAn"]],
    ["Jam Aktif", ["active", "activePeak", "activePeriods", "comprehensive"]],
    ["Video", ["label", "videos"]],
    ["LIVE", ["lives"]],
    ["Penjualan & Produk", ["cargo", "cargoCat", "catP", "catS", "goods", "shops"]],
    ["Kreator Serupa", ["similar"]],
], sections=[
    Section("base", "Profil kreator", "/api/author/v3/detail/baseInfo", "profile",
            profile={"title": "nickname", "img": "avatar", "sub": "unique_id", "sub_prefix": "@",
                     "url_tpl": "https://www.tiktok.com/@{unique_id}", "round": True,
                     "tags": ["category_name", "market_category_l1_name", "region_name"]},
            fields=[N("Pengikut", "follower_count")],
            series=[T("Bio", "signature"), D("Video pertama", "first_video_time"),
                    T("Kategori produk", "product_category_name"), T("ID toko", "seller_id")]),
    Section("index", "Indeks & performa 28 hari", "/api/author/v3/detail/authorIndex", "kpi",
            fields=[N("Peringkat negara", "region_rank"), N("Peringkat kategori", "category_rank"),
                    N("Indeks trafik", "flow_index"), N("Indeks jualan", "carry_index"),
                    N("Pengikut", "follower_count"), N("Pengikut baru 28h", "follower_28_count"),
                    N("Video 28h", "aweme_28_count"), N("LIVE 28h", "live_28_count"),
                    N("Rata-rata tayangan video", "video_28_avg_play_count"),
                    N("Rata-rata interaksi video", "video_28_avg_interaction_count"),
                    N("Rata-rata terjual/produk", "goods_28_avg_sole_count"),
                    M("Rata-rata omzet/produk", "goods_28_avg_sale_amount"),
                    N("Rata-rata terjual/LIVE", "live_28_avg_sold_count"),
                    M("Rata-rata omzet/LIVE", "live_28_avg_sale_amount"), T("Video terakhir", "last_video_time")]),
    Section("stat", "Kemampuan penjualan & konten", "/api/author/v3/detail/getStatInfo", "kpi",
            fields=[M("Omzet total", "goods_sale_amount"), M("Omzet dari video", "video_sale_amount"),
                    M("Omzet dari LIVE", "live_sale_amount"), N("Peringkat omzet di negara", "goods_sale_country_rank"),
                    T("Peringkat periode lalu", "goods_sale_last_country_rank"),
                    N("Total video", "aweme_total_count"), N("Video jualan", "aweme_count"),
                    N("Total tayangan video", "aweme_play_count"), N("Rata-rata tayangan", "aweme_avg_play_count"),
                    N("Median tayangan", "aweme_mid_play_count"), T("Rata-rata interaksi", "aweme_avg_interaction_rate"),
                    M("GPM video terendah", "aweme_min_gpm"), M("GPM video tertinggi", "aweme_max_gpm"),
                    N("Jumlah LIVE", "live_count"), Col("Rata-rata durasi LIVE", "dur", "live_avg_time"),
                    N("Rata-rata penonton LIVE", "live_avg_user_count"), N("Penonton LIVE terbanyak", "live_max_user_count"),
                    N("Rata-rata puncak penonton", "live_avg_peak_count"),
                    M("GPM LIVE terendah", "live_gpm_min"), M("GPM LIVE tertinggi", "live_gpm_max")]),
    Section("contact", "Kontak kreator", "/api/author/v3/detail/authorContact", "table", root="list",
            fields=[T("Kanal", "name"), T("Kontak", "id"), T("Tautan", "link")]),
    _datalist("dlFollow", "Data baru-baru ini", [["follower", "Perubahan pengikut"], ["play", "Tayangan"],
                                                  ["like", "Suka"], ["video_comment", "Komentar"],
                                                  ["video_collect", "Disimpan"], ["video_share", "Dibagikan"]],
              "follower"),
    _datalist("dlSale", "Data penjualan", [["sold_count", "Terjual"], ["sale_amount", "Omzet"],
                                           ["video_sold_count", "Terjual via video"],
                                           ["video_sale_amount", "Omzet via video"],
                                           ["live_sold_count", "Terjual via LIVE"], ["live_sale_amount", "Omzet via LIVE"],
                                           ["showcase_qty", "Terjual via etalase"], ["showcase_amt", "Omzet via etalase"]],
              "sale_amount"),
    Section("fans", "Gender pengikut", "/api/author/v3/detail/fansPortrait", "bars", sync="core", controls=[C_CORE],
            root="follower_genders", x="key", series=[N("Porsi (%)", "value")]),
    Section("fansAge", "Usia pengikut", "/api/author/v3/detail/fansPortrait", "bars", sync="core", controls=[C_CORE],
            root="follower_ages", x="key", series=[N("Porsi (%)", "value")]),
    Section("fansState", "Provinsi pengikut teratas", "/api/author/v3/detail/fansPortrait", "bars", sync="core",
            controls=[C_CORE], root="state_distribution", x="key", series=[N("Porsi (%)", "value")]),
    Section("fansAn", "Kategori aktivitas pengikut", "/api/author/v3/detail/authorFansAnalysis", "kpi",
            fields=[T("Pengikut aktif", "active_rate"), T("Pengikut potensial", "poten_rate"),
                    T("Lainnya", "other_rate"), T("Tingkat keaktifan", "active_level"), T("Data per", "data_date")]),
    Section("active", "Jumlah video dirilis per jam", "/api/author/v3/detail/authorActiveRange", "bars",
            sync="act", controls=[dperiod("date_type", "Periode", [[7, "7 hari"], [14, "14 hari"], [28, "28 hari"]], 28)],
            root="hourly_stats", x="hour", series=[N("Video", "video_count")], wide=True),
    Section("activePeak", "Jam interaksi tertinggi", "/api/author/v3/detail/authorActiveRange", "pairs",
            sync="act", controls=[dperiod("date_type", "Periode", [[7, "7 hari"], [14, "14 hari"], [28, "28 hari"]], 28)],
            root="high_interaction_periods.top_periods", x="time_range", series=[T("Interaksi", "interaction_rate_show")]),
    Section("activePeriods", "Jam paling aktif mengunggah", "/api/author/v3/detail/authorActiveRange", "pairs",
            sync="act", controls=[dperiod("date_type", "Periode", [[7, "7 hari"], [14, "14 hari"], [28, "28 hari"]], 28)],
            root="active_periods.top_periods", x="time_range", series=[N("Video", "video_count")]),
    Section("comprehensive", "Periode puncak aktif", "/api/author/v3/detail/authorActiveRange", "table",
            sync="act", controls=[dperiod("date_type", "Periode", [[7, "7 hari"], [14, "14 hari"], [28, "28 hari"]], 28)],
            root="comprehensive_active.time_periods",
            fields=[T("Periode", "name"), T("Jam", "range"), N("Video", "video_count"),
                    T("Porsi", "percentage_rate_show")]),
    Section("label", "Tag / tema video", "/api/author/v3/detail/labelList", "bars",
            root="label_list", x="key", series=[N("Porsi (%)", "value")]),
    Section("videos", "Video kreator", "/api/author/v3/detail/videoList", "table", root="list", paged=True,
            controls=[dperiod("date_type", "Periode", D7_14_180, 28),
                      sel("type", "Status iklan", [["all", "Semua"], ["ad_aweme", "Video iklan"],
                                                   ["no_ad_aweme", "Bukan iklan"]], "all"),
                      order([["sold_count,2", "Terjual"], ["sale_amount,2", "Omzet"], ["play_count,2", "Tayangan"],
                             ["digg_count,2", "Suka"], ["interaction_rate,2", "Interaksi"], ["create_time,2", "Terbaru"]])],
            fields=[video(img="cover", title="video_desc", sub="unique_id"), TS("Diunggah", "create_time"),
                    N("Tayangan", "play_count"), N("Suka", "digg_count"), N("Komentar", "comment_count"),
                    N("Dibagikan", "share_count"), N("Produk", "product_count"), N("Terjual", "sold_count"),
                    M("Omzet", "sale_amount"), T("Interaksi", "interaction_rate"), Col("Durasi", "dur", "duration"),
                    Col("Iklan", "bool", "is_ad")]),
    Section("lives", "Siaran LIVE", "/api/author/v3/detail/liveList", "table", root="list", paged=True,
            extra={"is_live": ""},
            controls=[dperiod("date_type", "Periode", D7_14_180, 28),
                      order([["create_time,2", "Terbaru"], ["sale_amount,2", "Omzet"], ["product_count,2", "Produk"],
                             ["sold_product_count,2", "Produk terjual"], ["total_user_count,2", "Penonton"]])],
            fields=[live(sub="create_date"), T("Durasi", "live_time"), N("Terjual", "sold_count"),
                    M("Omzet", "sale_amount"), N("Penonton", "total_user_count"), N("Produk", "product_count"),
                    N("Produk terjual", "sold_product_count"), M("Nilai per penonton", "uv_price"),
                    G("Kategori laris", "hot_category")]),
    Section("cargo", "Ringkasan data penjualan", "/api/author/v3/detail/cargoSummary", "kpi",
            fields=[N("Total terjual", "total_sold_count"), M("Total omzet", "total_sale_amount"),
                    N("Terjual dari video", "video_sold_count"), M("Omzet dari video", "video_sale_amount"),
                    N("Terjual dari LIVE", "live_sold_count"), M("Omzet dari LIVE", "live_sale_amount"),
                    N("Toko", "shop_count"), N("Toko lewat video", "shop_video_count"),
                    N("Toko lewat LIVE", "shop_live_count"), N("Produk", "goods_count"),
                    N("Produk lewat video", "goods_video_count"), N("Produk lewat LIVE", "goods_live_count"),
                    N("Rata-rata terjual/video", "video_avg_sold_count"), M("Rata-rata omzet/video", "video_avg_sale_amount"),
                    N("Rata-rata terjual/LIVE", "live_avg_sold_count"), M("Rata-rata omzet/LIVE", "live_avg_sale_amount"),
                    M("Belanja per pembeli", "per_customer_amount")]),
    Section("cargoCat", "Kategori teratas", "/api/author/v3/detail/cargoSummary", "bars",
            root="{m}", x="key", series=[N("Porsi (%)", "value")],
            controls=[view("m", "Berdasarkan", [["most_sold_category_list", "Terjual"],
                                                ["most_num_category_list", "Jumlah promosi"]],
                           "most_sold_category_list")]),
    _catlist("catP", "Rasio jumlah produk per kategori", "product_count"),
    _catlist("catS", "Rasio penjualan per kategori", "sold_count"),
    Section("goods", "Daftar produk", "/api/author/v3/detail/goodsList", "table", root="list", paged=True,
            controls=[sel("date_type", "Periode", [[7, "7 hari"], [14, "14 hari"], [28, "28 hari"], [90, "90 hari"],
                                                   [0, "Semua"]], 28),
                      Control("category_id", "Kategori", "dynselect", source="@goodsFilter", key="category"),
                      order([["sold_count,2", "Terjual"], ["sale_amount,2", "Omzet"], ["commission_rate,2", "Komisi"]])],
            fields=[product(sub="shop_title"), Col("Harga", "price", "real_price"), P("Komisi", "commission_rate"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), N("Rating", "product_rating"),
                    G("Kategori", "category"), D("Mulai dijual", "shelf_time")]),
    Section("shops", "Toko kerja sama", "/api/author/v3/detail/shopList", "table", root="list",
            controls=[order([["sold_count,2", "Terjual"], ["sale_amount,2", "Omzet"], ["product_count,2", "Produk"]])],
            fields=[shop(img="img", title="name", sid="id"), N("Terjual (dengan kreator)", "sold_count"),
                    M("Omzet (dengan kreator)", "sale_amount"), N("Produk", "product_cnt"),
                    N("Terjual 7 hari", "day7_sold_count"), M("Omzet 7 hari", "day7_sale_amount"),
                    N("Total terjual toko", "total_sold_count")]),
    Section("similar", "Kreator serupa", "/api/author/v3/detail/similarityList", "table", root="list",
            fields=[creator(), T("Kategori", "category_name"), N("Pengikut", "follower_count"),
                    M("Omzet 28h", "d28_sale_amount"), N("Terjual 28h", "d28_sold_count"),
                    N("Rata-rata tayangan", "avg_play_count"), N("Video 28h", "aweme_28d_count"),
                    N("LIVE 28h", "live_28d_count")]),
])

# ============================================================================ LIVE
_LIVE_EVENTS = [T("Mulai", "ctime"), N("Jumlah produk", "total_num"),
                Col("Produk", "entity", key="product_list.0.title", img="product_list.0.cover",
                    id="product_list.0.product_id", link="product", sub="product_list.0.real_price"),
                N("Terjual (produk pertama)", "product_list.0.sold_count")]

LIVE = Detail("live", "Detail Siaran LIVE", "id", referer="/id/live/detail/", fm_path="live/detail",
              options={"goodsFilter": Opt("/api/live/v3/detail/goodsFilter",
                                          {"category": ("category", "category_id", "category_name"),
                                           "store": ("store", "seller_id", "shop_name")})},
              tabs=[
    ["Ringkasan", ["info", "host", "overview", "top3", "trend", "catQty", "cat"]],
    ["Produk", ["goods", "explain", "listed"]],
    ["LIVE Serupa", ["similar"]],
], sections=[
    Section("info", "Profil siaran", "/api/live/v3/detail/info", "profile",
            profile={"title": "title", "img": "cover", "sub": "nickname", "sub_link": ["creator", "uid"],
                     "tags": ["hot_category_name", "source", "user_region_name"]},
            fields=[N("Terjual", "sold_count"), M("Omzet", "sale_amount"), N("Total penonton", "total_user_count"),
                    N("Produk", "product_count"), N("Produk terjual", "sold_product_count"),
                    M("Nilai per penonton", "uv_value"), M("Harga rata-rata", "avg_price"),
                    N("Pengikut baru", "inc_follower_count")],
            series=[TS("Mulai", "create_time"), TS("Selesai", "finish_time"), Col("Durasi", "dur", "duration"),
                    Col("Siaran akun toko", "bool", "is_shop"), T("Konversi", "sale_rate"), M("GPM", "gpm"),
                    T("Toko", "shop_name"), N("Pengikut kreator", "follower_count"),
                    N("Jumlah LIVE kreator", "live_count"), N("Rata-rata penonton kreator", "total_avg_user_count")]),
    Section("host", "Pembawa siaran (28 hari)", "/api/live/v3/detail/author", "kpi",
            fields=[T("Kreator", "nick_name"), N("Pengikut", "follower_count"), N("Video", "aweme_count"),
                    N("LIVE 28 hari", "live_28_count"), N("Rata-rata terjual/LIVE", "live_28_avg_sold_count"),
                    M("Rata-rata omzet/LIVE", "live_28_avg_sale_amount")]),
    Section("overview", "Ringkasan data siaran", "/api/live/v3/detail/overview", "kpi",
            fields=[N("Total penonton", "total_user_count"), N("Puncak penonton", "max_user_count"),
                    N("Rata-rata penonton", "avg_user_count"), N("Pengikut baru", "inc_user_count"),
                    T("Rasio pengikut baru", "new_follower_rate"), T("Rata-rata durasi tonton", "avg_stay_time"),
                    N("Terjual", "sold_count"), N("Terjual per jam", "hour_sold_count"),
                    M("Omzet", "sale_amount"), M("Omzet per jam", "hour_sale_amount"),
                    M("Harga rata-rata", "avg_price"), M("Nilai per penonton", "uv_value"),
                    N("Produk", "product_count"), N("Produk terjual", "sold_product_count"),
                    T("Konversi", "sale_rate"), M("Omzet per 1.000 penonton", "thound_sale_amount")]),
    Section("top3", "3 produk terlaris", "/api/live/v3/detail/info", "table", root="top3_product_list",
            fields=[product(sub=""), Col("Harga", "price", "real_price"), N("Terjual", "sold_count"),
                    M("Omzet", "sale_amount")]),
    Section("trend", "Tren trafik sepanjang siaran", "/api/live/v3/detail/dataList", "line", root="data_list",
            x="ctime", series=[N("Penonton online", "user_count"), N("Total penonton", "total_user"),
                               N("Pengikut baru", "inc_follower_count"), N("Terjual (kumulatif)", "sold_count"),
                               M("Omzet (kumulatif)", "sale_amount")], wide=True),
    Section("catQty", "Kategori produk (jumlah produk)", "/api/live/v3/detail/categoryList", "bars", root="quantity",
            x="category_name", series=[N("Porsi (%)", "ratio")]),
    Section("cat", "Kategori produk (terjual)", "/api/live/v3/detail/categoryList", "bars", root="sold",
            x="category_name", series=[N("Porsi (%)", "ratio")]),
    Section("goods", "Daftar produk siaran", "/api/live/v3/detail/goodsList", "table", root="goods_list", paged=True,
            controls=[Control("category_id", "Kategori", "dynselect", source="@goodsFilter", key="category"),
                      Control("seller_id", "Toko", "dynselect", source="@goodsFilter", key="store"),
                      order([["1,2", "Terjual"], ["2,2", "Omzet"], ["3,2", "Komisi"]], param="orderby")],
            fields=[product(sub="shop_name"), Col("Harga", "price", "real_price"), P("Komisi", "commission_rate"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), T("Kategori", "category_name")]),
    Section("explain", "Produk yang dijelaskan", "/api/live/v3/detail/dataList", "table", root="explanation_list",
            fields=_LIVE_EVENTS),
    Section("listed", "Produk yang ditayangkan", "/api/live/v3/detail/dataList", "table", root="listed_product_list",
            fields=_LIVE_EVENTS),
    Section("similar", "Siaran LIVE serupa", "/api/live/v3/detail/similarLive", "table", root="live_list",
            fields=[live(), TS("Mulai", "create_time"), Col("Durasi", "dur", "duration"), N("Terjual", "sold_count"),
                    M("Omzet", "sale_amount"), N("Total penonton", "total_user_count"),
                    N("Puncak penonton", "max_user_count"), M("Nilai per penonton", "uv_value")]),
])

# ============================================================================ VIDEO
VIDEO = Detail("video", "Detail Video", "id", referer="/id/media-source/video/", fm_path="media-source/video", tabs=[
    ["Ringkasan", ["overview", "stats", "trend"]],
    ["Produk", ["goods"]],
    ["Video Serupa", ["similar"]],
], sections=[
    Section("overview", "Profil video", "/api/video/overview", "profile",
            profile={"title": "video_desc", "img": "cover", "sub": "nickname", "sub_link": ["creator", "uid"],
                     "url_tpl": "https://www.tiktok.com/@{unique_id}/video/{video_id}",
                     "tags": ["category", "region_name"]},
            fields=[N("Tayangan", "play_count"), N("Suka", "digg_count"), N("Komentar", "comment_count"),
                    N("Dibagikan", "share_count"), N("Diteruskan", "forward_count"), N("Produk", "product_cnt")],
            series=[TS("Diunggah", "create_time"), Col("Durasi", "dur", "duration"), Col("Iklan", "bool", "is_ad"),
                    N("Pengikut kreator", "follower_count"), N("Rata-rata tayangan kreator", "total_avg_play_count"),
                    T("Data per", "mtime")]),
    Section("stats", "Ringkasan data", "/api/video/overviewData", "kpi",
            fields=[N("Tayangan", "play_count"), N("Suka", "digg_count"), N("Komentar", "comment_count"),
                    N("Dibagikan", "share_count"), T("Interaksi", "interact_rate"), N("IPM", "ipm")]),
    Section("trend", "Tren data video", "/api/video/V2/base", "line", root="trend", x="dt",
            controls=[sel("d_type", "Periode", [[7, "7 hari"], [14, "14 hari"], [28, "28 hari"], [90, "90 hari"]], 28)],
            series=[N("Tayangan baru", "inc_play_count"), N("Suka baru", "inc_digg_count"),
                    N("Komentar baru", "inc_comment_count"), N("Dibagikan baru", "inc_share_count"),
                    N("Total tayangan", "play_count"), N("Total suka", "digg_count"),
                    N("Total komentar", "comment_count"), N("Total dibagikan", "share_count")], wide=True),
    Section("goods", "Produk di video", "/api/video/v2/goods", "table", root="list", paged=True,
            controls=[order([["1,2", "Terjual"], ["2,2", "Omzet"], ["3,2", "Waktu tayang"], ["4,2", "Komisi"]])],
            fields=[product(sub="region_name"), Col("Harga", "price", "real_price"), P("Komisi", "commission_rate"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), N("Rating", "product_rating"),
                    G("Kategori", "category_name")]),
    Section("similar", "Video serupa", "/api/video/similar", "table", root="list",
            fields=[video(img="cover", title="desc", sub="nickname"), N("Tayangan", "play_count"),
                    N("Suka", "digg_count"), N("Komentar", "comment_count"), N("Dibagikan", "share_count"),
                    N("Pengikut kreator", "follower_count")]),
])

# ============================================================================ IKLAN
_AD_LIST = [ad(), N("Tayangan", "play_count"), N("Suka", "digg_count"), N("Komentar", "comment_count"),
            N("Dibagikan", "share_count"), N("Terjual", "sold_count"), M("Omzet", "sale_amount"),
            M("Estimasi biaya", "estimate_cost_amount"), N("Popularitas", "hotness_count")]

AD = Detail("ad", "Detail Iklan", "id", referer="/id/creativecenter/newdetail/", fm_path="creativecenter/newdetail",
            tabs=[
    ["Ringkasan", ["detail", "products", "overview", "overviewTrend", "trend", "calendar", "put"]],
    ["Iklan Produk Sama", ["same"]],
    ["Iklan Pengiklan Sama", ["sameAdv"]],
    ["Iklan Serupa", ["similar"]],
], sections=[
    Section("detail", "Profil iklan", "/api/da/V4/detail", "profile",
            profile={"title": "desc", "img": "cover", "sub": "advertiser", "sub_link": ["advertiser", "new_advertiser_id"],
                     "url": "tiktok_url", "tags": ["region_name", "advertiser_type"]},
            fields=[N("Tayangan", "play_count"), N("Suka", "digg_count"), N("Komentar", "comment_count"),
                    N("Dibagikan", "share_count"), N("Disimpan", "collect_count"), N("Hari tayang", "put_days"),
                    M("Estimasi biaya", "estimate_cost_amount"), N("ROAS", "roas")],
            series=[D("Video dibuat", "create_date"), D("Pertama ditemukan", "first_put_date"),
                    D("Terakhir ditemukan", "last_put_date"), T("Rasio suka", "digg_rate"),
                    N("Estimasi konversi", "estimated_conversion_count"), M("Omzet", "sale_amount"),
                    T("Halaman tujuan", "web_url")]),
    Section("products", "Produk yang diiklankan", "/api/da/V4/detail", "table", root="product_list",
            fields=[product(sub=""), T("Harga", "price"), N("Terjual", "sold_count")]),
    Section("overview", "Ringkasan data iklan (28 hari)", "/api/da/V4/overview", "kpi", extra={"date_type": 28},
            note="Angka 'rata-rata' = rata-rata harian iklan ini.",
            fields=[N("Tayangan", "play_count"), M("Estimasi biaya iklan", "estimate_cost_amount"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), M("Omzet dari iklan", "ad_sale_amount"),
                    N("Estimasi konversi", "estimated_conversion_count"), N("Pengikut baru", "inc_follower_count"),
                    N("Interaksi", "interaction_count"), T("Tingkat interaksi", "interaction_rate"),
                    T("Rasio suka/pengikut", "digg_follower_rate"), T("CTR", "click_rate"),
                    N("Rata-rata tayangan", "play_avg_count"), N("Rata-rata pengikut baru", "inc_follower_avg_count"),
                    M("Rata-rata biaya", "estimate_cost_avg_amount"), M("Rata-rata omzet", "sale_avg_amount")]),
    Section("overviewTrend", "Tren perubahan data", "/api/da/V4/overview", "line", root="trend", x="dt",
            extra={"date_type": 28},
            series=[N("Tayangan", "play_count"), M("Estimasi biaya", "estimate_cost_amount"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), N("ROAS", "roas"),
                    N("Pengikut baru", "inc_follower_count"), N("Estimasi konversi", "estimated_conversion_count")],
            wide=True),
    Section("trend", "Tren interaksi video", "/api/da/V2/trend", "line", root="trend", x="dt",
            series=[N("Tayangan baru", "inc_play_count"), N("Suka baru", "inc_digg_count"),
                    N("Komentar baru", "inc_comment_count"), N("Dibagikan baru", "inc_share_count"),
                    N("Total tayangan", "play_count")], wide=True),
    Section("calendar", "Kalender iklan (90 hari)", "/api/da/V4/calendar", "table", root="calendar",
            extra={"date_type": 90},
            fields=[D("Tanggal", "dt"), M("Estimasi biaya", "estimate_cost_amount"),
                    N("Estimasi konversi", "estimated_conversion_count"), N("ROAS", "roas")]),
    Section("put", "Tanggal iklan ditemukan tayang", "/api/da/putInfo", "list", root="date_list",
            fields=[T("Tanggal", "")]),
    Section("same", "Iklan untuk produk yang sama", "/api/da/V4/same", "table", root="ad_list", paged=True,
            fields=_AD_LIST),
    Section("sameAdv", "Iklan lain dari pengiklan yang sama", "/api/da/V4/sameadvertiserlist", "table",
            root="ad_list", paged=True,
            fields=_AD_LIST + [D("Pertama tayang", "first_put_date"), D("Terakhir tayang", "last_put_date")]),
    Section("similar", "Iklan serupa", "/api/da/V4/similar", "table", root="ad_list", paged=True,
            fields=[ad(), N("Tayangan", "play_count"), N("Suka", "digg_count"), N("Komentar", "comment_count"),
                    N("Dibagikan", "share_count"), N("Hari tayang", "put_days"), M("Estimasi biaya", "estimate_cost"),
                    T("ROAS", "roas"), Col("Durasi", "dur", "duration"), D("Terakhir tayang", "last_put_date")]),
])

# ============================================================================ PENGIKLAN
ADVERTISER = Detail("advertiser", "Detail Pengiklan", "id", referer="/id/creativecenter/advertiserDetail/",
                    fm_path="creativecenter/advertiserDetail", tabs=[
    ["Kinerja Data", ["base", "trendSum", "trend"]],
    ["Produk Dipromosikan", ["products"]],
    ["Materi Kreatif Populer", ["videos"]],
    ["Kreator Berkolaborasi", ["authors"]],
    ["Pengiklan Serupa", ["similar"]],
], sections=[
    Section("base", "Profil pengiklan", "/api/dar/V3/base", "profile",
            profile={"title": "name", "img": "avatar", "sub": "shop_category_name", "sub_link": ["shop", "seller_id"],
                     "tags": ["region_name"]},
            fields=[N("Materi iklan", "video_count"), N("Tayangan", "play_count"), N("Suka", "digg_count"),
                    N("Produk", "product_count"), N("Kreator", "author_count"),
                    M("Estimasi biaya iklan", "estimate_cost_amount"), M("Omzet", "sale_amount"), N("ROAS", "roas")],
            series=[D("Mulai beriklan", "first_put_day"), D("Terakhir beriklan", "last_put_day"),
                    N("Tayangan minggu lalu", "last_week_play_count"), N("Suka minggu lalu", "last_week_digg_count"),
                    T("Materi baru vs minggu lalu", "video_count_ctlw"), T("Kreator baru vs minggu lalu", "author_count_ctlw"),
                    T("Produk baru vs minggu lalu", "product_count_ctlw"), N("ROAS vs minggu lalu", "roas_ctlw"),
                    T("Mata uang", "currency")]),
    Section("trendSum", "Ringkasan kinerja terbaru", "/api/dar/V3/dataTrends", "kpi", extra={"date_type": 28},
            fields=[N("ROAS", "roas"), M("Estimasi biaya iklan", "estimate_cost_amount"), M("Omzet", "sale_amount"),
                    N("Materi iklan", "video_count"), N("Kreator", "author_count"), N("Produk", "product_count")]),
    Section("trend", "Tren kinerja", "/api/dar/V3/dataTrends", "line", root="trend", x="dt", extra={"date_type": 28},
            series=[N("ROAS", "roas"), M("Estimasi biaya iklan", "estimate_cost_amount"), M("Omzet", "sale_amount"),
                    N("Kreator", "author_count"), N("Materi iklan", "video_count"), N("Produk", "product_count")],
            wide=True),
    Section("products", "Produk yang dipromosikan", "/api/dar/V3/productList", "table", root="list", paged=True,
            extra={"date_type": 28, "order": "1,2"},
            fields=[product(sub="category_name_l3"), T("Harga", "price"), N("Materi iklan", "video_count"),
                    N("Tayangan", "play_count"), G("Kategori", "category_name_l1")]),
    Section("videos", "Materi kreatif populer", "/api/dar/V3/videoList", "table", root="list", paged=True,
            extra={"date_type": 28, "order": "1,2"},
            fields=[ad(sub="video_craete_date"), N("Tayangan", "play_count"), N("Suka", "digg_count"),
                    N("Komentar", "comment_count"), N("Dibagikan", "share_count"), N("Disimpan", "collect_count"),
                    N("ROAS", "roas"), Col("Durasi", "dur", "duration"), D("Terakhir tayang", "last_put_day")]),
    Section("authors", "Kreator yang berkolaborasi", "/api/dar/V3/authorList", "table", root="list", paged=True,
            extra={"date_type": 28, "order": "1,2"},
            fields=[creator(), N("Pengikut", "follower_count"), N("Materi kolaborasi", "video_count"),
                    N("Tayangan", "play_count"), N("Suka", "digg_count"), N("Komentar", "comment_count"),
                    D("Kolaborasi terakhir", "last_put_day")]),
    Section("similar", "Pengiklan serupa", "/api/dar/V3/similar", "table", root="list",
            fields=[advertiser(), M("Omzet dari iklan", "ad_sale_amount"),
                    M("Estimasi biaya iklan", "estimate_cost_amount"), N("ROAS", "roas"), N("Materi iklan", "video_count"),
                    N("Tayangan", "play_count"), N("Produk", "product_count"), N("Kreator", "author_count"),
                    T("Interaksi", "interaction_rate"), D("Mulai beriklan", "first_put_day")]),
])

# ============================================================================ AGENSI
_AG = {"date_type": 28}
AGENCY = Detail("agency", "Detail Agensi", "partner_secid", referer="/id/agency/mcn/detail/", fm_path="agency/mcn/detail",
                tabs=[
    ["Ringkasan", ["trend"]],
    ["Analisis Kreator", ["authFollower", "authType", "authors"]],
    ["Analisis Produk", ["goodsCat", "goodsPrice", "goods"]],
    ["Analisis Toko", ["shops"]],
], sections=[
    Section("trend", "Kinerja 28 hari terakhir", "/api/AffiliatePartner/trendAnalysis", "kpi", extra=_AG,
            fields=[M("Omzet", "inc_sale_amount"), N("Kreator baru", "inc_author_count"),
                    N("Produk baru", "inc_product_count"), N("Toko baru", "inc_shop_count"),
                    N("Video baru", "inc_video_count")]),
    Section("authFollower", "Sebaran kreator per jumlah pengikut", "/api/AffiliatePartner/authorAnalyse", "bars",
            root="follower_range.{m}", x="label", series=[M("Omzet", "value")], alt={"m": _rng()}, extra=_AG,
            controls=[view("m", "Metrik", METRIC3_RANGE, "sale_amount_range")]),
    Section("authType", "Sebaran per jenis kreator", "/api/AffiliatePartner/authorAnalyse", "bars",
            root="author_type_range.{m}", x="label", series=[M("Omzet", "value")], alt={"m": _rng()}, extra=_AG,
            controls=[view("m", "Metrik", METRIC3_RANGE, "sale_amount_range")]),
    Section("authors", "Kreator agensi", "/api/AffiliatePartner/authorList", "table", root="list", paged=True,
            extra=_AG,
            fields=[creator(img="author_info.avatar", title="author_info.nickname", uid="author_info.uid",
                            sub="author_info.unique_id"),
                    G("Kategori", "author_info.category_name"), N("Pengikut", "follower_count"),
                    N("Terjual", "inc_sold_count"), M("Omzet", "inc_sale_amount"),
                    T("GPM video", "video_gpm"), T("GPM LIVE", "live_gpm")]),
    Section("goodsCat", "Sebaran produk per kategori", "/api/AffiliatePartner/goodsAnalyse", "bars",
            root="category.{m}.{lv}", x="category_name", series=[M("Omzet", "category_count")],
            alt={"m": _cnt("Omzet", "Terjual", "category_count")}, extra=_AG,
            controls=[view("m", "Metrik", METRIC3, "sale_amount_by"),
                      view("lv", "Tingkat", [["first_category", "Kategori utama"],
                                             ["second_category", "Sub-kategori"]], "first_category")]),
    Section("goodsPrice", "Sebaran per rentang harga", "/api/AffiliatePartner/goodsAnalyse", "bars",
            root="price.{m}", x="label", series=[M("Omzet", "value")], alt={"m": _cnt("Omzet", "Terjual", "value")},
            extra=_AG, controls=[view("m", "Metrik", METRIC3, "sale_amount_by")]),
    Section("goods", "Produk agensi", "/api/AffiliatePartner/goodsList", "table", root="list", paged=True, extra=_AG,
            fields=[product(img="good_info.cover", title="good_info.title", pid="good_info.product_id",
                            sub="shop_info.name"),
                    T("Harga", "sale_price"), T("Komisi", "commission_rate"), N("Terjual", "inc_sold_count"),
                    M("Omzet", "inc_sale_amount"), N("Total terjual produk", "good_info.sold_count"),
                    T("Kategori", "good_info.category_name")]),
    Section("shops", "Toko kerja sama", "/api/AffiliatePartner/shopList", "table", root="list", paged=True, extra=_AG,
            fields=[shop(img="shop_info.avatar", title="shop_info.name", sid="shop_info.seller_id",
                         sub="shop_info.category_name"),
                    N("Produk", "product_count"), N("Terjual", "inc_sold_count"), M("Omzet", "inc_sale_amount"),
                    N("Total terjual toko", "shop_info.sold_count"), M("Total omzet toko", "shop_info.sale_amount")]),
])

DETAILS: dict[str, Detail] = {d.kind: d for d in (PRODUCT, SHOP, CREATOR, LIVE, VIDEO, AD, ADVERTISER, AGENCY)}


# --------------------------------------------------------------------------- eksekusi
def control_values(sec: Section, query: dict) -> dict:
    """Nilai tiap kontrol (pilihan pengguna atau bawaan)."""
    vals = {}
    for c in sec.controls:
        if c.kind == "category":
            continue
        v = query.get(c.param)
        vals[c.param] = v if v not in (None, "") else c.default
    return vals


def pick(data, path: str):
    """``dig`` + wildcard ``*``: ``"a.*.list"`` menggabungkan list dari tiap anak ``a`` (diberi ``_group``)."""
    if not path:
        return data
    if "*" not in path.split("."):
        return dig(data, path)
    head, _, tail = path.partition("*")
    base = dig(data, head.rstrip(".")) if head.rstrip(".") else data
    tail = tail.lstrip(".")
    out = []
    if isinstance(base, dict):
        for k, v in base.items():
            sub = dig(v, tail) if tail else v
            if isinstance(sub, list):
                out.extend({**r, "_group": k} if isinstance(r, dict) else r for r in sub)
    return out


def layout_for(sec: Section, vals: dict) -> tuple[dict, str]:
    """Tampilan aktif (dari ``alt``) + root data yang sudah diisi nilai kontrol."""
    lay: dict = {}
    for param, mapping in sec.alt.items():
        ov = mapping.get(str(vals.get(param)))
        if ov:
            lay.update(ov)
    root = lay.pop("root", sec.root)
    if "{" in root:
        root = root.format_map({k: ("" if v is None else v) for k, v in vals.items()})
    return lay, root


def _public_layout(lay: dict) -> dict:
    return {k: ([asdict(c) for c in v] if k in ("fields", "series") else v) for k, v in lay.items()}


async def run_section(sec: Section, params: dict, query: dict, region: str, referer: str | None = None) -> dict:
    """Jalankan satu bagian: isi kontrol, terapkan batas paket gratis, ambil & potong datanya."""
    params = {**params, **sec.extra}
    vals = control_values(sec, query)
    try:
        for c in sec.controls:
            if c.kind == "view" or (c.when and not active(c, vals)):
                continue
            if c.kind == "dperiod":
                apply_dperiod(c, query, params)
            elif c.kind == "category":
                for lv in c.levels:
                    if query.get(lv) not in (None, ""):
                        params[lv] = query[lv]
            elif vals.get(c.param) not in (None, ""):
                params[c.param] = vals[c.param]
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    lay, root = layout_for(sec, vals)
    limit = await client.row_limit()
    page = int(query.get("page") or 1) if sec.paged else 1
    out = {"limit": limit, "layout": _public_layout(lay)}
    if sec.paged:
        if limit and page > 1:
            return {**out, "status": "locked", "rows": [],
                    "message": f"Akun gratis hanya bisa melihat {limit} baris teratas. "
                               "Halaman berikutnya terkunci paket FastMoss."}
        params.update(page=page, pagesize=sec.pagesize)
    res = await client.get(sec.path, params, region=region, referer=referer)
    out.update(status=res.status, message=res.message, code=res.code, cached=res.cached)
    if not res.ok:
        return out
    data = pick(res.data, root)
    if lay.get("view", sec.view) == "table":
        rows = data if isinstance(data, list) else []
        total = None
        if isinstance(res.data, dict):
            for k in ("total", "total_count", "total_cnt", "count"):
                v = res.data.get(k)
                if isinstance(v, (int, float)) or (isinstance(v, str) and v.isdigit()):
                    total = int(v)
                    break
        hidden = 0
        if limit and len(rows) > limit:
            hidden, rows = len(rows) - limit, rows[:limit]
        out.update(rows=rows, total=total, hidden=hidden, page=page, pagesize=sec.pagesize)
    else:
        out["data"] = data
    return out


async def fetch_section(kind: str, item_id: str, section: str, query: dict, region: str) -> dict:
    det = DETAILS.get(kind)
    sec = det.by_key.get(section) if det else None
    if not sec:
        return {"status": "error", "message": "Bagian detail tidak dikenal."}
    referer = settings.BASE_URL + det.referer + item_id if det.referer else None
    return await run_section(sec, {det.id_param: item_id}, query, region, referer)


def _opt(item, vk: str, lk: str) -> dict | None:
    if not isinstance(item, dict) or item.get(vk) in (None, ""):
        return None
    lab = item.get(lk)
    if isinstance(lab, list):
        lab = " › ".join(str(x) for x in lab if x)
    lab = str(lab if lab not in (None, "") else item[vk])
    if lab.strip().lower() in ("semua", "all"):
        return None
    o = {"v": item[vk], "l": lab}
    if isinstance(item.get("sub"), list) and item["sub"]:
        o["sub"] = [x for x in (_opt(s, vk, lk) for s in item["sub"]) if x]
    return o


async def fetch_option(kind: str, item_id: str, name: str, region: str) -> dict:
    """Opsi filter milik satu detail (kategori/toko/harga) — bentuknya sama dengan ``/api/options``."""
    det = DETAILS.get(kind)
    opt = det.options.get(name) if det else None
    if not opt:
        return {"status": "error", "message": "Sumber opsi tidak dikenal.", "options": {}}
    referer = settings.BASE_URL + det.referer + item_id if det.referer else None
    res = await client.get(opt.path, {det.id_param: item_id, **opt.extra}, region=region, referer=referer)
    if not res.ok:
        return {"status": res.status, "message": res.message, "options": {}}
    out = {}
    for key, (root, vk, lk) in opt.lists.items():
        items = dig(res.data, root) if root else res.data
        out[key] = [o for o in (_opt(i, vk, lk) for i in (items if isinstance(items, list) else [])) if o]
    return {"status": "ok", "options": out}
