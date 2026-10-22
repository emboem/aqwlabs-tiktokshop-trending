"""Halaman detail (produk, toko, kreator, LIVE, video).

Tiap detail terdiri dari beberapa *bagian* (section). Satu bagian = satu endpoint FastMoss plus
cara menampilkannya (``view``), jadi tampilan web cukup satu penggambar generik:

* ``profile`` : kartu identitas (gambar, judul, tag, angka utama, info)
* ``kpi``     : deret angka ringkasan
* ``kv``      : daftar info label → nilai
* ``pairs``   : daftar pasangan nama/nilai dari sebuah list (mis. atribut produk)
* ``table``   : tabel berhalaman (memakai :class:`~app.catalog.Col`)
* ``line``    : grafik tren (sumbu-x tanggal)
* ``bars``    : grafik distribusi (label → nilai)

Bagian yang dikunci paket FastMoss (MAG_AUTH) tetap didaftarkan supaya pengguna tahu datanya ada,
tapi isinya tidak pernah ditampilkan — FastMoss mengirim data contoh palsu untuk bagian terkunci.
Bagian tanpa ``fields`` (umumnya yang terkunci di paket gratis) digambar otomatis dari data mentah
bila akun yang dipakai berlangganan.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from . import settings
from .catalog import Col, D, G, M, N, P, T, TS, Control, creator, live, product, shop, video
from .services import client, dig


@dataclass
class Section:
    key: str
    title: str
    path: str
    view: str
    root: str = ""                                  # path data yang dipakai ("" = seluruh data)
    fields: list = field(default_factory=list)      # kpi/kv: isi | table: kolom | profile: angka utama
    x: str = ""                                     # line: sumbu-x | bars/pairs: kunci label
    series: list = field(default_factory=list)      # line/bars/pairs: nilai | profile: daftar info
    extra: dict = field(default_factory=dict)       # parameter tetap tambahan
    controls: list = field(default_factory=list)    # pilihan pengguna (select)
    paged: bool = False
    profile: dict = field(default_factory=dict)     # profile: {title, img, sub, sub_prefix, tags, url}
    note: str = ""
    wide: bool = False

    def public(self) -> dict:
        d = asdict(self)
        d.pop("path")
        d.pop("extra")
        return d


@dataclass
class Detail:
    kind: str
    title: str
    id_param: str
    tabs: list                                     # [[judul tab, [kunci bagian, ...]], ...]
    sections: list
    referer: str = ""

    def __post_init__(self):
        self.by_key = {s.key: s for s in self.sections}

    def public(self) -> dict:
        return {"kind": self.kind, "title": self.title, "tabs": self.tabs,
                "sections": {s.key: s.public() for s in self.sections}}


def sel(param, label, opts, default) -> Control:
    return Control(param, label, "select", [list(o) for o in opts], default)


DTYPE = [[7, "7 hari"], [28, "28 hari"], [90, "90 hari"]]

# ============================================================================ PRODUK
PRODUCT = Detail("product", "Detail Produk", "product_id", referer="/id/e-commerce/detail/", tabs=[
    ["Ringkasan", ["base", "overview", "price", "attr", "sku"]],
    ["Kreator", ["authors", "authorChart"]],
    ["Video", ["videos", "ads"]],
    ["LIVE", ["lives"]],
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
                    N("Stok", "product.stock_count"), N("Indeks viral", "product.viral_index"),
                    N("Indeks popularitas", "product.popularity_index"), N("Peringkat negara", "product.country_rank"),
                    N("Peringkat kategori", "product.category_rank"), T("Ongkir", "product.transport_fee"),
                    TS("Rilis", "product.launch_time"), T("Negara", "product.region_name"),
                    N("Terjual toko", "shop.sold_count"), M("Omzet toko", "shop.sale_amount")]),
    Section("overview", "Tren penjualan", "/api/goods/v3/overview", "kpi",
            note="Grafik tren penjualan harian produk."),
    Section("price", "Riwayat harga (30 hari)", "/api/goods/v3/priceList", "line", root="price_list",
            x="date", series=[M("Harga", "price")]),
    Section("attr", "Atribut produk", "/api/goods/v3/goodsAttribute", "pairs", root="attributes",
            x="name", series=[T("Nilai", "value")]),
    Section("sku", "Varian (SKU)", "/api/goods/v3/productSku", "table", root="sku_list"),
    Section("authors", "Kreator yang mempromosikan", "/api/goods/v3/author", "table", root="list", paged=True,
            extra={"order": "2,2", "ecommerce_type": "all"},
            fields=[creator(), G("Kategori", "category"), N("Pengikut", "follower_count"),
                    N("Terjual (produk ini)", "sold_count"), M("Omzet (produk ini)", "sale_amount"),
                    M("Omzet kreator 28h", "d28_sale_amount"), N("Video", "aweme_count"),
                    D("Mulai promosi", "start_promoting")]),
    Section("authorChart", "Sebaran kreator", "/api/goods/v3/authorChart", "bars"),
    Section("videos", "Video promosi", "/api/goods/v3/video", "table", root="list", paged=True,
            extra={"order": "1,2", "d_type": 0, "date_type": 28},
            controls=[sel("is_promoted", "Jenis video", [[-1, "Semua"], [0, "Organik"], [1, "Iklan berbayar"]], -1)],
            fields=[video(img="video.cover", title="video.video_desc", sub="author.author_nickname"),
                    D("Diunggah", "create_date"), N("Tayangan", "play_count"), N("Suka", "digg_count"),
                    N("Komentar", "comment_count"), N("Dibagikan", "share_count"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), P("Interaksi", "engagement_rate"),
                    M("Estimasi biaya iklan", "estimate_cost_amount"), N("ROAS", "roas"),
                    Col("Iklan", "bool", "is_ad")]),
    Section("ads", "Video iklan produk", "/api/goods/V3/adsVideo", "table", root="list", paged=True),
    Section("lives", "Siaran LIVE yang menjual", "/api/goods/v3/live", "table", root="list", paged=True,
            extra={"d_type": 28, "order": "2,2", "live_type": "all"},
            fields=[live(sub="author.nickname"), D("Tanggal", "create_date"), T("Durasi", "live_time"),
                    N("Terjual (produk ini)", "sold_count"), M("Omzet (produk ini)", "sale_amount"),
                    N("Total penonton", "total_user"), N("Puncak penonton", "max_user_count"),
                    N("Produk di LIVE", "product_count")]),
    Section("similar", "Produk serupa", "/api/goods/v3/similarity", "table", root="list",
            fields=[product(sub="region_name"), Col("Harga", "price", "price"), N("Terjual", "sale_cnt"),
                    M("Omzet", "sale_amount"), P("Komisi", "crate"), N("Rating", "product_rating"),
                    N("Indeks viral", "viral_index"), N("Indeks popularitas", "popularity_index"),
                    G("Kategori", "category_name")]),
])

# ============================================================================ TOKO
SHOP = Detail("shop", "Detail Toko", "id", referer="/id/shop-marketing/detail/", tabs=[
    ["Ringkasan", ["base", "recent", "trend", "sale", "saleUnits"]],
    ["Produk", ["goods", "productAn"]],
    ["Kreator", ["shopAuthor", "authors", "authorAn"]],
    ["Video & LIVE", ["videoSum", "videos", "liveSum"]],
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
                    T("Ulasan positif", "shop_rate.positive_feedback_rate"), D("Buka sejak", "ctime"),
                    N("Rata-rata terjual kategori", "avg_category_sold_count"),
                    M("Rata-rata omzet kategori", "avg_category_sale_amount"),
                    T("Akun resmi", "shop_author.nickname"), N("Pengikut akun resmi", "shop_author.follower_count"),
                    T("Data per", "mtime")]),
    Section("recent", "Ringkasan 28 hari", "/api/shop/v3/recentData", "kpi", root="list.total_info",
            fields=[N("Terjual", "sold_count"), M("Omzet", "sale_amount"), N("Produk terjual", "sold_product_count"),
                    N("Kreator", "author_count"), N("Video", "aweme_count"), N("LIVE", "live_count")]),
    Section("trend", "Tren harian (180 hari)", "/api/shop/v3/recentData", "line", root="list.trend", x="dt",
            series=[N("Terjual harian", "inc_sold_count"), M("Omzet harian", "inc_sale_amount"),
                    N("Kreator baru", "inc_author_count"), N("Video baru", "inc_aweme_count"),
                    N("LIVE baru", "inc_live_count")], wide=True),
    Section("sale", "Sumber penjualan (omzet)", "/api/shop/v3/saleAnalysis", "bars",
            root="channel_distribution.gmv.list", x="source", series=[M("Omzet", "sale_amount")]),
    Section("saleUnits", "Sumber penjualan (unit terjual)", "/api/shop/v3/saleAnalysis", "bars",
            root="channel_distribution.units_sold.list", x="source", series=[N("Terjual", "sold_count")]),
    Section("goods", "Produk toko", "/api/shop/v3/goods", "table", root="product_list", paged=True,
            extra={"order": "1,2"},
            fields=[product(img="img", sub="category_name_l3"), Col("Harga", "price", "price"), P("Komisi", "crate"),
                    N("Total terjual", "sold_count"), M("Total omzet", "sale_amount"),
                    N("Kreator", "relate_author_count"), N("Video", "relate_video_count"),
                    N("LIVE", "relate_live_count"), N("Rating", "product_rating"), D("Rilis", "ctime")]),
    Section("productAn", "Analisis produk", "/api/shop/v3/productAnalysis", "kpi"),
    Section("shopAuthor", "Akun resmi toko", "/api/shop/v3/shopAuthorAnalysis", "kpi", root="base",
            fields=[N("Akun resmi", "shop_author_cnt"), N("Total pengikut", "shop_author_follower_total_cnt"),
                    N("Terjual", "shop_author_sold_count"), M("Omzet", "shop_author_sale_amount"),
                    N("Video", "shop_author_video_cnt"), N("LIVE", "shop_author_live_cnt"),
                    N("Rata-rata tayangan video", "avg_shop_author_video_play_cnt"),
                    N("Rata-rata penonton LIVE", "avg_shop_author_enter_cnt")]),
    Section("authors", "Kreator affiliate", "/api/shop/v3/author", "table", root="list", paged=True,
            extra={"is_shop": 0, "order": "2,2"},
            fields=[creator(), G("Kategori", "author_category_name"), N("Pengikut", "follower_count"),
                    N("Produk dipromosikan", "product_count"), N("Terjual", "sold_count"), M("Omzet", "sale_amount"),
                    M("GPM video maks.", "aweme_max_gpm"), M("GPM LIVE maks.", "live_gpm_max")]),
    Section("authorAn", "Analisis kreator", "/api/shop/v3/authorAnalysis", "kpi"),
    Section("videoSum", "Ringkasan video (28 hari)", "/api/shop/v3/videoAnalysisSummary", "kpi",
            fields=[N("Video jualan", "video_count"), M("Omzet dari video", "video_amount"),
                    N("Tayangan", "play_count")]),
    Section("videos", "Video jualan", "/api/shop/v3/videoAnalysis", "table", root="list", paged=True,
            extra={"order": "2,2", "is_ad": -1},
            fields=[video(img="cover", title="video_desc", sub="nickname"), D("Diunggah", "ctime"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), N("Tayangan", "play_cnt"),
                    N("Komentar", "comment_count"), N("Dibagikan", "share_count"),
                    N("Pengikut kreator", "follower_count"), Col("Iklan", "bool", "is_ad")]),
    Section("liveSum", "Ringkasan LIVE (28 hari)", "/api/shop/v3/liveAnalysisSummary", "kpi",
            fields=[N("Jumlah LIVE", "total_count"), N("Terjual", "sold_count"), M("Omzet", "sale_amount"),
                    N("Total penonton", "total_enter_count"), N("Rata-rata terjual/LIVE", "avg_sold_count"),
                    M("Rata-rata omzet/LIVE", "avg_sale_amount"), N("Rata-rata penonton/LIVE", "avg_enter_count")]),
    Section("similar", "Toko serupa", "/api/shop/v3/similarity", "table", root="shop_list"),
])

# ============================================================================ KREATOR
CREATOR = Detail("creator", "Detail Kreator", "uid", referer="/id/influencer/detail/", tabs=[
    ["Ringkasan", ["base", "index", "cat", "stat"]],
    ["Video", ["videos"]],
    ["LIVE", ["lives"]],
    ["Produk & Toko", ["goods", "shops", "cargo"]],
    ["Audiens", ["fans", "label", "active"]],
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
    Section("cat", "Kategori konten", "/api/author/v3/detail/categoryList", "bars", root="list",
            x="key", series=[N("Porsi (%)", "value")]),
    Section("stat", "Statistik penjualan", "/api/author/v3/detail/getStatInfo", "kpi"),
    Section("videos", "Video kreator", "/api/author/v3/detail/videoList", "table", root="list", paged=True,
            fields=[video(img="cover", title="video_desc", sub="unique_id"), TS("Diunggah", "create_time"),
                    N("Tayangan", "play_count"), N("Suka", "digg_count"), N("Komentar", "comment_count"),
                    N("Dibagikan", "share_count"), N("Terjual", "sold_count"), M("Omzet", "sale_amount"),
                    P("Interaksi", "interaction_rate"), Col("Durasi", "dur", "duration"), Col("Iklan", "bool", "is_ad")]),
    Section("lives", "Siaran LIVE", "/api/author/v3/detail/liveList", "table", root="list", paged=True,
            fields=[live(sub="create_date"), T("Durasi", "live_time"), N("Terjual", "sold_count"),
                    M("Omzet", "sale_amount"), N("Penonton", "total_user_count"), N("Produk", "product_count"),
                    N("Produk terjual", "sold_product_count"), M("Nilai per penonton", "uv_price"),
                    G("Kategori laris", "hot_category")]),
    Section("goods", "Produk yang dipromosikan", "/api/author/v3/detail/goodsList", "table", root="list", paged=True,
            fields=[product(sub="shop_title"), Col("Harga", "price", "real_price"), P("Komisi", "commission_rate"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), N("Rating", "product_rating"),
                    G("Kategori", "category"), D("Mulai dijual", "shelf_time")]),
    Section("shops", "Toko yang bekerja sama", "/api/author/v3/detail/shopList", "table", root="list",
            fields=[shop(img="img", title="name", sid="id"), N("Terjual (dengan kreator)", "sold_count"),
                    M("Omzet (dengan kreator)", "sale_amount"), N("Produk", "product_cnt"),
                    N("Terjual 7 hari", "day7_sold_count"), M("Omzet 7 hari", "day7_sale_amount"),
                    N("Total terjual toko", "total_sold_count")]),
    Section("cargo", "Ringkasan jualan", "/api/author/v3/detail/cargoSummary", "kpi"),
    Section("fans", "Profil pengikut", "/api/author/v3/detail/fansPortrait", "kpi"),
    Section("label", "Label konten", "/api/author/v3/detail/labelList", "kpi"),
    Section("active", "Jam aktif", "/api/author/v3/detail/authorActiveRange", "kpi"),
    Section("similar", "Kreator serupa", "/api/author/v3/detail/similarityList", "table", root="list",
            fields=[creator(), T("Kategori", "category_name"), N("Pengikut", "follower_count"),
                    M("Omzet 28h", "d28_sale_amount"), N("Terjual 28h", "d28_sold_count"),
                    N("Rata-rata tayangan", "avg_play_count"), N("Video 28h", "aweme_28d_count"),
                    N("LIVE 28h", "live_28d_count")]),
])

# ============================================================================ LIVE
LIVE = Detail("live", "Detail Siaran LIVE", "id", referer="/id/live/detail/", tabs=[
    ["Ringkasan", ["info", "overview", "trend", "cat"]],
    ["Produk", ["goods"]],
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
                    T("Konversi", "sale_rate"), M("GPM", "gpm"), T("Toko", "shop_name"),
                    N("Pengikut kreator", "follower_count"), N("Jumlah LIVE kreator", "live_count"),
                    N("Rata-rata penonton kreator", "total_avg_user_count")]),
    Section("overview", "Kinerja siaran", "/api/live/v3/detail/overview", "kpi",
            fields=[N("Puncak penonton", "max_user_count"), N("Rata-rata penonton", "avg_user_count"),
                    T("Rata-rata durasi tonton", "avg_stay_time"), N("Terjual per jam", "hour_sold_count"),
                    M("Omzet per jam", "hour_sale_amount"), T("Konversi", "sale_rate"),
                    M("Omzet per 1.000 penonton", "thound_sale_amount"), T("Rasio pengikut baru", "new_follower_rate")]),
    Section("trend", "Penonton sepanjang siaran", "/api/live/v3/detail/dataList", "line", root="data_list",
            x="ctime", series=[N("Penonton online", "user_count"), N("Total penonton", "total_user"),
                               N("Terjual (kumulatif)", "sold_count")], wide=True),
    Section("cat", "Kategori terjual", "/api/live/v3/detail/categoryList", "bars", root="sold",
            x="category_name", series=[N("Porsi (%)", "ratio")]),
    Section("goods", "Produk di siaran", "/api/live/v3/detail/goodsList", "table", root="goods_list", paged=True,
            fields=[product(sub="shop_name"), Col("Harga", "price", "real_price"), P("Komisi", "commission_rate"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), T("Kategori", "category_name")]),
    Section("similar", "Siaran LIVE serupa", "/api/live/v3/detail/similarLive", "table", root="live_list",
            fields=[live(), TS("Mulai", "create_time"), Col("Durasi", "dur", "duration"), N("Terjual", "sold_count"),
                    M("Omzet", "sale_amount"), N("Total penonton", "total_user_count"),
                    N("Puncak penonton", "max_user_count"), M("Nilai per penonton", "uv_value")]),
])

# ============================================================================ VIDEO
VIDEO = Detail("video", "Detail Video", "id", referer="/id/media-source/video/", tabs=[
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
    Section("stats", "Interaksi", "/api/video/overviewData", "kpi",
            fields=[N("Tayangan", "play_count"), N("Suka", "digg_count"), N("Komentar", "comment_count"),
                    N("Dibagikan", "share_count"), T("Interaksi", "interact_rate"), N("IPM", "ipm")]),
    Section("trend", "Tren harian", "/api/video/V2/base", "line", root="trend", x="dt",
            series=[N("Tayangan baru", "inc_play_count"), N("Suka baru", "inc_digg_count"),
                    N("Komentar baru", "inc_comment_count"), N("Dibagikan baru", "inc_share_count")], wide=True),
    Section("goods", "Produk di video", "/api/video/v2/goods", "table", root="list",
            fields=[product(sub="region_name"), Col("Harga", "price", "real_price"), P("Komisi", "commission_rate"),
                    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), N("Rating", "product_rating")]),
    Section("similar", "Video serupa", "/api/video/similar", "table", root="list",
            fields=[video(img="cover", title="desc", sub="nickname"), N("Tayangan", "play_count"),
                    N("Suka", "digg_count"), N("Komentar", "comment_count"), N("Dibagikan", "share_count"),
                    N("Pengikut kreator", "follower_count")]),
])

DETAILS: dict[str, Detail] = {d.kind: d for d in (PRODUCT, SHOP, CREATOR, LIVE, VIDEO)}


async def run_section(sec: Section, params: dict, query: dict, region: str, referer: str | None = None) -> dict:
    """Jalankan satu bagian: isi kontrol, terapkan batas paket gratis, ambil & potong datanya."""
    params = {**params, **sec.extra}
    for c in sec.controls:
        v = query.get(c.param)
        params[c.param] = v if v not in (None, "") else c.default
    limit = await client.row_limit()
    page = int(query.get("page") or 1) if sec.paged else 1
    if sec.paged:
        if limit and page > 1:
            return {"status": "locked", "limit": limit, "rows": [],
                    "message": f"Akun gratis hanya bisa melihat {limit} baris teratas. "
                               "Halaman berikutnya terkunci paket FastMoss."}
        params.update(page=page, pagesize=10)
    res = await client.get(sec.path, params, region=region, referer=referer)
    out = {"status": res.status, "message": res.message, "code": res.code, "cached": res.cached, "limit": limit}
    if not res.ok:
        return out
    data = dig(res.data, sec.root) if sec.root else res.data
    if sec.view == "table":
        rows = data if isinstance(data, list) else []
        total = None
        if isinstance(res.data, dict):
            for k in ("total", "total_count", "total_cnt", "count"):
                if isinstance(res.data.get(k), (int, float)):
                    total = int(res.data[k])
                    break
        hidden = 0
        if limit and len(rows) > limit:
            hidden, rows = len(rows) - limit, rows[:limit]
        out.update(rows=rows, total=total, hidden=hidden, page=page)
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
