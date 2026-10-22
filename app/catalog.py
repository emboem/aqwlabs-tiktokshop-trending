"""Katalog semua menu FastMoss: endpoint, parameter bawaan, kontrol filter, dan kolom tabel.

Semua parameter di sini direkam dari request asli halaman FastMoss (Okt 2026), jadi
nilai bawaannya sama dengan yang dipakai situs resminya.

Satu definisi dipakai tiga tempat: tampilan tabel di web, ekspor Excel/CSV/PDF, dan validasi API.
"""
from __future__ import annotations

import base64
import datetime as _dt
from dataclasses import asdict, dataclass, field
from typing import Any


# --------------------------------------------------------------------------- model
@dataclass
class Col:
    label: str
    type: str                 # entity | num | money | pct | text | tags | date | ts | dur | price | spark | bool
    key: str = ""             # path bertitik, mis. "shop_info.name"
    img: str = ""             # entity: path gambar
    sub: str = ""             # entity: baris kecil di bawah judul
    sub_prefix: str = ""
    id: str = ""              # entity: path id untuk tautan detail
    link: str = ""            # entity: jenis detail (product/shop/creator/live/video)
    url: str = ""             # entity: tautan luar (mis. halaman TikTok)
    x: str = ""               # spark: field sumbu-x
    y: str = ""               # spark: field nilai
    hint: str = ""


@dataclass
class Control:
    param: str
    label: str
    kind: str                 # text | select | period | date | category | dynselect
    options: list = field(default_factory=list)   # [[value, label], ...]
    default: Any = None
    source: str = ""          # dynselect/category: nama sumber opsi (lihat OPTION_SOURCES)
    key: str = ""             # dynselect: kunci daftar di respons sumber
    params: list = field(default_factory=list)    # date: daftar param yang diisi tanggal yang sama
    offset: int = 1           # date/period: default = hari ini - offset
    advanced: bool = False    # tampil di panel "Filter lanjutan"
    levels: list = field(default_factory=lambda: ["l1_cid", "l2_cid", "l3_cid"])


@dataclass
class Menu:
    key: str
    group: str
    title: str
    desc: str
    path: str
    list_key: str
    columns: list
    base: dict = field(default_factory=dict)
    controls: list = field(default_factory=list)
    sorts: list = field(default_factory=list)      # [[order, label], ...]; order pertama = bawaan
    pagesize: int = 10
    referer: str = ""
    kind: str = "table"       # table | cards
    note: str = ""

    def public(self) -> dict:
        d = asdict(self)
        return d


# --------------------------------------------------------------------------- helper kolom
def product(img="cover", title="title", pid="product_id", sub="shop_info.name") -> Col:
    return Col("Produk", "entity", key=title, img=img, sub=sub, id=pid, link="product")


def shop(img="avatar", title="name", sid="seller_id", sub="category_name") -> Col:
    return Col("Toko", "entity", key=title, img=img, sub=sub, id=sid, link="shop")


def creator(img="avatar", title="nickname", uid="uid", sub="unique_id") -> Col:
    return Col("Kreator", "entity", key=title, img=img, sub=sub, sub_prefix="@", id=uid, link="creator")


def video(img="img", title="desc", vid="video_id", sub="uname") -> Col:
    return Col("Video", "entity", key=title, img=img, sub=sub, id=vid, link="video")


def live(img="cover", title="title", rid="room_id", sub="nick_name") -> Col:
    return Col("Siaran LIVE", "entity", key=title, img=img, sub=sub, id=rid, link="live")


N = lambda label, key, hint="": Col(label, "num", key, hint=hint)          # noqa: E731
M = lambda label, key, hint="": Col(label, "money", key, hint=hint)        # noqa: E731
P = lambda label, key, hint="": Col(label, "pct", key, hint=hint)          # noqa: E731
T = lambda label, key: Col(label, "text", key)                             # noqa: E731
G = lambda label, key: Col(label, "tags", key)                             # noqa: E731
D = lambda label, key: Col(label, "date", key)                             # noqa: E731
TS = lambda label, key: Col(label, "ts", key)                              # noqa: E731


# --------------------------------------------------------------------------- helper kontrol
def period(daily=True, weekly=True, monthly=True, default=1) -> Control:
    opts = []
    if daily:
        opts.append([1, "Harian"])
    if weekly:
        opts.append([2, "Mingguan"])
    if monthly:
        opts.append([3, "Bulanan"])
    return Control("date_type", "Periode", "period", opts, default)


def select(param, label, opts, default=None, advanced=False) -> Control:
    return Control(param, label, "select", [list(o) for o in opts], default, advanced=advanced)


def words(label="Kata kunci", param="words") -> Control:
    return Control(param, label, "text")


def category(source="goods", levels=("l1_cid", "l2_cid", "l3_cid")) -> Control:
    return Control("category", "Kategori", "category", source=source, levels=list(levels))


def dyn(param, label, source, key=None, advanced=True) -> Control:
    return Control(param, label, "dynselect", source=source, key=key or param, advanced=advanced)


def date(params, label="Tanggal", offset=1) -> Control:
    return Control(params[0], label, "date", params=list(params), offset=offset)


DAYS_7_28 = [[7, "7 hari terakhir"], [28, "28 hari terakhir"]]
DAYS_7_28_90 = [[7, "7 hari terakhir"], [28, "28 hari terakhir"], [90, "90 hari terakhir"]]

# Sumber opsi filter (dimuat dinamis dari FastMoss, mengikuti negara yang dipilih).
OPTION_SOURCES = {
    "goods": "/api/goods/filterInfo",
    "author": "/api/author/filterInfoNew",
    "video": "/api/video/filterInfo",
    "live": "/api/live/filterInfo",
    "hashtag": "/api/hashtag/filterInfo",
    "shop": "/api/shop/V3/categoryInfo",
    "ads": "/api/da/V4/filterInfo",
    "country": "/api/shop/countryList",
    "market": "/api/analysis/GoodCategory/filterInfo",
}

# nilai `df` yang dikirim halaman pencarian kreator (btoa("fs_" + origin + "_ps"))
_DF = base64.b64encode(b"fs_https://www.fastmoss.com_ps").decode()

# Kode urutan (order) hasil uji langsung ke API FastMoss.
RANK_SORTS = [["1,2", "Terjual (periode)"], ["7,2", "Omzet (periode)"], ["6,2", "Pertumbuhan"],
              ["3,2", "Total terjual"], ["4,2", "Kreator (periode)"], ["5,2", "Total kreator"]]
FOLLOWER_SORTS = [["1,2", "Pengikut baru"], ["2,2", "Total pengikut"]]
SHOP_RANK_SORTS = [["1,2", "Terjual (periode)"], ["2,2", "Omzet (periode)"], ["3,2", "Pertumbuhan terjual"],
                   ["6,2", "Pertumbuhan omzet"], ["4,2", "Jumlah kreator"]]
LIVE_SORTS = [["1,2", "Terjual"], ["2,2", "Omzet"], ["4,2", "Total penonton"], ["7,2", "Puncak penonton"],
              ["6,2", "Nilai per penonton"], ["5,2", "Terbaru"]]

PRODUCT_RANK_COLS = [
    product(), Col("Harga", "price", "real_price"),
    N("Terjual (periode)", "sold_count"), M("Omzet (periode)", "sale_amount"),
    P("Pertumbuhan", "sold_count_inc_rate"),
    N("Total terjual", "total_sold_count"), M("Total omzet", "total_sale_amount"),
    P("Komisi", "commission_rate"), N("Kreator", "author_count"), N("Video", "aweme_count"),
    N("LIVE", "live_count"), G("Kategori", "category_name"), D("Rilis", "launch_time"),
]

CREATOR_GROWTH_COLS = [
    creator(img="author_info.avatar", title="author_info.nickname", uid="uid", sub="author_info.unique_id"),
    G("Kategori", "author_info.category_name"), N("Pengikut", "follower_count"),
    N("Pengikut baru", "inc_follower_count"), P("Laju pengikut", "follower_rate"),
    N("Suka baru", "inc_total_favorited"), N("Komentar baru", "inc_comment_count"),
    N("Dibagikan baru", "inc_share_count"), N("Jumlah video", "aweme_count"),
]

SHOP_RANK_COLS = [
    shop(), N("Terjual (periode)", "inc_sold_count"), M("Omzet (periode)", "inc_sale_amount"),
    P("Pertumbuhan terjual", "sold_count_inc_rate"), P("Pertumbuhan omzet", "sale_amount_inc_rate"),
    N("Produk aktif", "on_sale_product_count"), N("Kreator", "author_count"),
    N("Kreator baru", "inc_author_count"), T("Perusahaan", "seller_company"),
]

LIVE_COLS = [
    live(), TS("Mulai", "create_time"), Col("Durasi", "dur", "duration"),
    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), N("Penonton", "total_user_count"),
    N("Puncak penonton", "max_user_count"), N("Produk", "product_count"), M("Nilai per penonton", "uv_value"),
    N("Pengikut baru", "inc_follower_count"), G("Kategori laris", "hot_category"),
]

HASHTAG_COLS = [
    Col("Hashtag", "entity", key="label_name", sub="region_name"),
    N("Skor peluang", "opportunity"), N("Total tayangan", "play_count"), N("Jumlah video", "video_count"),
]

TREND_COLS = [
    N("Postingan", "post"), N("Impresi", "impression_count"), N("Suka", "digg_count"),
    N("Dibagikan", "share_count"), N("Komentar", "comment_count"),
    Col("Tren postingan", "spark", "post_trends", x="dt", y="post"),
]


# --------------------------------------------------------------------------- daftar menu
MENUS: list[Menu] = [
    # ============================== PRODUK ==============================
    Menu("product-search", "Produk", "Cari Produk",
         "Cari produk TikTok Shop berdasarkan kata kunci, kategori, dan performa penjualan.",
         "/api/goods/V2/search", "product_list",
         [product(img="img"), Col("Harga", "price", "price"), P("Komisi", "crate"),
          N("Terjual 7 hari", "day7_sold_count"), M("Omzet 7 hari", "day7_sale_amount"),
          N("Terjual 28 hari", "day28_sold_count"), M("Omzet 28 hari", "day28_sale_amount"),
          N("Total terjual", "sold_count"), M("Total omzet", "sale_amount"),
          N("Kreator", "relate_author_count"), N("Video", "relate_video_count"), N("LIVE", "relate_live_count"),
          N("Rating", "product_rating"), P("Rasio order kreator", "author_order_rate"),
          G("Kategori", "category_name_l3"), D("Rilis", "launch_time"),
          Col("Tren 7 hari", "spark", "trend", x="dt", y="inc_sold_count")],
         base={},
         controls=[words("Kata kunci produk"), select("last_date_type", "Rentang data", DAYS_7_28, 7),
                   category(),
                   dyn("price_amount", "Harga", "goods"), dyn("crate", "Komisi", "goods"),
                   dyn("sold_count", "Total terjual", "goods"), dyn("sale_amount", "Total omzet", "goods"),
                   dyn("day7_sold_count", "Terjual 7 hari", "goods"), dyn("day28_sold_count", "Terjual 28 hari", "goods"),
                   dyn("relate_author_count", "Jumlah kreator", "goods", key="relate_author"),
                   dyn("relate_video_count", "Jumlah video", "goods", key="relate_video"),
                   dyn("launch_date", "Waktu rilis", "goods"),
                   dyn("author_order_rate", "Rasio order kreator", "goods")],
         sorts=[["2,2", "Terjual 7 hari"], ["7,2", "Omzet 7 hari"], ["12,2", "Terjual 28 hari"],
                ["3,2", "Total terjual"], ["8,2", "Total omzet"], ["4,2", "Jumlah kreator"],
                ["6,2", "Jumlah video"], ["5,2", "Jumlah LIVE"], ["9,2", "Terbaru"]],
         referer="/id/e-commerce/search"),
    Menu("product-sales", "Produk", "Produk Terlaris",
         "Peringkat produk dengan penjualan tertinggi per hari, minggu, atau bulan.",
         "/api/goods/saleRank", "rank_list", PRODUCT_RANK_COLS,
         base={}, controls=[period(), category()], sorts=RANK_SORTS,
         referer="/id/e-commerce/saleslist"),
    Menu("product-new", "Produk", "Produk Baru Laris",
         "Produk yang baru rilis dan langsung laku.",
         "/api/goods/newProduct", "list",
         [product(), Col("Harga", "price", "real_price"), N("Terjual", "sold_count"), M("Omzet", "sale_amount"),
          N("Total terjual", "total_sold_count"), M("Total omzet", "total_sale_amount"),
          P("Komisi", "commission_rate"), N("Kreator", "author_count"), N("Video", "aweme_count"),
          N("LIVE", "live_count"), G("Kategori", "category_name"), D("Rilis", "launch_time")],
         base={"rank_type": 11},
         sorts=[["1,2", "Terjual"], ["2,2", "Omzet"], ["3,2", "Total terjual"], ["4,2", "Total omzet"]],
         controls=[date(["start_date", "end_date"], "Tanggal data", offset=3), category()],
         referer="/id/e-commerce/newProducts"),
    Menu("product-hot", "Produk", "Produk Populer",
         "Produk yang paling banyak dipromosikan kreator.",
         "/api/goods/popRank", "rank_list", PRODUCT_RANK_COLS,
         base={}, controls=[period(), category()],
         sorts=[RANK_SORTS[4]] + [s for s in RANK_SORTS if s[0] != "4,2"],
         referer="/id/e-commerce/hotlist"),
    Menu("product-hotvideo", "Produk", "Produk dari Video Viral",
         "Produk yang terjual lewat video promosi paling viral.",
         "/api/video/hotGoodsVideoGroupByProduct", "product_list",
         [product(sub="shop_name"), Col("Harga", "price", "price"), N("Terjual", "sold_count"),
          M("Omzet", "sold_amount"), N("Video promosi", "video_count"), N("Tayangan", "play_count"),
          N("Suka", "digg_count"), N("Komentar", "comment_count"), N("Dibagikan", "share_count"),
          G("Kategori", "category_name"), D("Rilis", "launch_time")],
         base={},
         controls=[select("rank_type", "Video diunggah", DAYS_7_28_90, 7), category()],
         sorts=[["1,2", "Terjual"], ["2,2", "Omzet"], ["7,2", "Jumlah video"], ["3,2", "Tayangan"],
                ["4,2", "Suka"], ["5,2", "Komentar"], ["6,2", "Dibagikan"]],
         referer="/id/e-commerce/hotvideo"),

    # ============================== KREATOR ==============================
    Menu("creator-search", "Kreator", "Cari Kreator",
         "Cari kreator/affiliate berdasarkan kategori, pengikut, dan penjualan.",
         "/api/author/search", "author_list",
         [creator(), G("Kategori", "category"), N("Pengikut", "follower_count"),
          N("Pengikut baru (28h)", "follower_28d_count"), N("Video (28h)", "aweme_28d_count"),
          N("Rata-rata tayangan", "avg_play_count"), P("Interaksi", "interact_rate"),
          M("Omzet (28h)", "d28_sale_amount"), N("Terjual (28h)", "sale_28d_count"),
          M("Omzet video (28h)", "video_28d_sale_amount"), M("Omzet LIVE (28h)", "live_28d_sale_amount"),
          G("Kategori jualan", "sale_category_l3_name")],
         base={"shop_window": 1, "is_shop": 0, "df": _DF},
         controls=[words("Nama / username kreator"), select("last_date_type", "Rentang data", DAYS_7_28, 28),
                   dyn("cid", "Kategori kreator", "author", key="author_category", advanced=False),
                   select("shop_window", "Etalase", [[1, "Punya etalase"], [0, "Semua"]], 1, advanced=True),
                   dyn("follower", "Pengikut", "author", key="follower_count"),
                   dyn("follower_28d_count", "Pengikut baru 28h", "author"),
                   dyn("d28_sale_amount", "Omzet 28h", "author"), dyn("d28_sold_count", "Terjual 28h", "author"),
                   dyn("interaction_v1_rate", "Interaksi", "author"),
                   dyn("avg_28d_play_count", "Rata-rata tayangan 28h", "author"),
                   dyn("contact", "Kontak tersedia", "author")],
         sorts=[["12,2", "Terjual 28 hari"], ["7,2", "Omzet 28 hari"], ["1,2", "Pengikut"],
                ["2,2", "Pengikut baru 28 hari"], ["3,2", "Jumlah video"], ["6,2", "Rata-rata tayangan 28 hari"],
                ["8,2", "Interaksi"], ["10,2", "Video produk 28 hari"], ["11,2", "LIVE produk 28 hari"]],
         referer="/id/influencer/search"),
    Menu("creator-fans", "Kreator", "Pertumbuhan Pengikut",
         "Kreator dengan kenaikan pengikut tertinggi.",
         "/api/followers/followersList", "list", CREATOR_GROWTH_COLS,
         base={"type": 1}, sorts=FOLLOWER_SORTS,
         controls=[period(monthly=True), dyn("cid", "Kategori kreator", "author", key="author_category", advanced=False)],
         referer="/id/influencer/tiktok/fans"),
    Menu("creator-commerce", "Kreator", "Kreator Penjual Terlaris",
         "Kreator e-commerce dengan omzet penjualan tertinggi.",
         "/api/ecommerce/rank", "list",
         [creator(), G("Kategori", "category_name"), N("Pengikut", "follower_count"),
          M("Total omzet", "total_amount"), N("Total terjual", "total_sold_count"),
          M("Omzet video", "video_amount"), N("Terjual via video", "video_sold_count"),
          M("Omzet LIVE", "live_amount"), N("Terjual via LIVE", "live_sold_count"),
          N("Produk", "product_count"), N("Video", "video_count"), N("LIVE", "live_count")],
         base={"order": "1,2"},
         controls=[period(), dyn("cid", "Kategori kreator", "author", key="author_category", advanced=False)],
         referer="/id/influencer/tiktok/commerceTop"),
    Menu("creator-bluev", "Kreator", "Kreator Terverifikasi",
         "Pertumbuhan pengikut kreator bercentang biru.",
         "/api/followers/followersList", "list", CREATOR_GROWTH_COLS,
         base={"type": 2}, sorts=FOLLOWER_SORTS,
         controls=[period(), dyn("cid", "Kategori kreator", "author", key="author_category", advanced=False)],
         referer="/id/influencer/tiktok/blue-v"),
    Menu("creator-popular", "Kreator", "Kreator Paling Disukai",
         "Kreator dengan tambahan suka, komentar, dan bagikan terbanyak.",
         "/api/followers/followersList", "list", CREATOR_GROWTH_COLS,
         base={"type": 3}, sorts=FOLLOWER_SORTS[::-1],
         controls=[period(), dyn("cid", "Kategori kreator", "author", key="author_category", advanced=False)],
         referer="/id/influencer/tiktok/popular"),
    Menu("creator-potential", "Kreator", "Kreator Potensial",
         "Kreator 'kuda hitam' dengan pertumbuhan tinggi — cocok diajak kerja sama lebih awal.",
         "/api/author/potential/rank", "author_list",
         [creator(), G("Kategori", "category_name"), N("Indeks potensi", "potential_index"),
          N("Pengikut", "follower_cnt"), M("Omzet", "gmv"), N("Terjual", "sold_count"),
          N("Video", "video_cnt"), N("Rata-rata tayangan", "avg_play_count"),
          P("Interaksi", "interact_rate"), P("Laju pengikut", "follower_rate"),
          D("Video terakhir", "latest_video_create_date")],
         base={"is_ecommerce": 1},
         controls=[period(), dyn("cid", "Kategori kreator", "author", key="author_category", advanced=False)],
         referer="/id/influencer/tiktok/potentialTop"),

    # ============================== TOKO ==============================
    Menu("shop-search", "Toko", "Cari Toko",
         "Cari toko TikTok Shop berdasarkan nama, kategori, dan performa.",
         "/api/shop/v3/search", "list",
         [shop(img="shop_info.avatar", title="shop_info.name", sub="shop_info.category_name"),
          N("Total terjual", "sold_count"), M("Total omzet", "sale_amount"),
          N("Terjual (rentang)", "day7_sold_count"), M("Omzet (rentang)", "day7_sale_amount"),
          N("Produk aktif", "on_sell_product_count"), N("Kreator penjual", "sales_author_count"),
          N("Rating toko", "shop_rating"), P("Rasio produk baru", "new_product_rate"),
          Col("Tren 7 hari", "spark", "trend", x="dt", y="inc_sold_count")],
         base={},
         sorts=[["1,2", "Terjual (rentang)"], ["2,2", "Omzet (rentang)"], ["5,2", "Total terjual"],
                ["6,2", "Total omzet"], ["3,2", "Jumlah produk"], ["9,2", "Kreator penjual"]],
         controls=[words("Nama toko"), select("last_date_type", "Rentang data", DAYS_7_28, 7),
                   category("shop"),
                   dyn("sold_count_range", "Total terjual", "shop", key="sold_count"),
                   dyn("sale_amount_range", "Total omzet", "shop", key="sale_amount"),
                   dyn("shop_rating_range", "Rating toko", "shop", key="shop_rating"),
                   dyn("sales_author_count_range", "Kreator penjual", "shop", key="sales_author_count"),
                   dyn("product_count_range", "Jumlah produk", "shop", key="product_count"),
                   dyn("new_product_rate_range", "Rasio produk baru", "shop", key="new_product_rate")],
         referer="/id/shop-marketing/search"),
    Menu("shop-sales", "Toko", "Toko Terlaris",
         "Peringkat toko dengan omzet tertinggi.",
         "/api/shop/v3/shopList", "list", SHOP_RANK_COLS,
         base={}, controls=[period(), category("shop")], sorts=SHOP_RANK_SORTS,
         referer="/id/shop-marketing/tiktok"),
    Menu("shop-hot", "Toko", "Toko Populer",
         "Toko yang paling banyak dipromosikan kreator.",
         "/api/shop/v3/shopPopList", "list", SHOP_RANK_COLS,
         base={}, controls=[period(), category("shop")], sorts=[["5,2", "Popularitas"]] + SHOP_RANK_SORTS,
         referer="/id/shop-marketing/hotTiktok"),

    # ============================== LIVE ==============================
    Menu("live-search", "LIVE", "Cari Siaran LIVE",
         "Cari siaran LIVE jualan berdasarkan kata kunci dan performa.",
         "/api/live/V2/search", "live_list", LIVE_COLS,
         base={}, sorts=LIVE_SORTS,
         controls=[words("Judul / kreator"), select("date_type", "Rentang waktu", DAYS_7_28_90, 7),
                   dyn("cid", "Kategori kreator", "live", key="author_category", advanced=False),
                   dyn("follower_count", "Pengikut", "live"), dyn("total_user_count", "Penonton", "live"),
                   dyn("sold_count", "Terjual", "live")],
         referer="/id/live/search"),
    Menu("live-rank", "LIVE", "LIVE Terlaris",
         "Siaran LIVE dengan omzet tertinggi (pantauan terbaru).",
         "/api/live/rank", "live_list", LIVE_COLS,
         base={}, sorts=LIVE_SORTS,
         controls=[dyn("cid", "Kategori kreator", "live", key="author_category", advanced=False)],
         referer="/id/live/tiktok"),
    Menu("live-products", "LIVE", "Produk Laris di LIVE",
         "Produk dengan penjualan tertinggi lewat siaran LIVE.",
         "/api/live/v3/hotProduct", "rank_list",
         [product(sub="shop.name"), Col("Harga", "price", "real_price"),
          N("Terjual via LIVE", "live_sold_count"), M("Omzet LIVE", "live_sale_amount"),
          N("Jumlah LIVE", "live_count"), G("Kategori", "category_name_l3"), D("Tanggal", "dt")],
         base={"order": "1,2"}, controls=[period(weekly=False, monthly=False)],
         referer="/id/live/hotProduct"),
    Menu("live-creators", "LIVE", "Kreator LIVE Terlaris",
         "Kreator dengan omzet LIVE shopping tertinggi.",
         "/api/ecommerce/liveRank", "list",
         [creator(), G("Kategori", "category_name"), N("Pengikut", "follower_count"),
          M("Omzet LIVE", "live_amount"), N("Terjual via LIVE", "live_sold_count"),
          N("Jumlah LIVE", "live_count"), N("Produk", "product_count"),
          M("GPM tertinggi", "live_gpm_max"), D("Tanggal", "dt")],
         base={}, controls=[period(weekly=False, monthly=False),
                            dyn("cid", "Kategori kreator", "author", key="author_category", advanced=False)],
         referer="/id/live/liveCommerce"),

    # ============================== VIDEO & MUSIK ==============================
    Menu("video-search", "Video", "Cari Video",
         "Cari video TikTok berdasarkan kata kunci, tayangan, dan interaksi.",
         "/api/video/search", "video_list",
         [video(), TS("Diunggah", "ctime"), N("Tayangan", "play_count"), N("Suka", "digg_count"),
          N("Komentar", "comment_count"), N("Dibagikan", "share_count"), P("Interaksi", "interact_rate"),
          Col("Durasi", "dur", "duration"), N("Pengikut kreator", "ufollower_count"),
          Col("Video jualan", "bool", "is_ecommerce"), Col("Iklan", "bool", "is_ad")],
         base={"order": "2,2"},
         controls=[words("Kata kunci / deskripsi"),
                   select("d_type", "Diunggah", DAYS_7_28_90 + [[0, "Semua waktu"]], 7),
                   dyn("cid", "Kategori kreator", "video", key="author_category", advanced=False),
                   dyn("play", "Tayangan", "video", key="play_count"), dyn("digg", "Suka", "video", key="digg_count"),
                   dyn("follower", "Pengikut kreator", "video", key="follower_count"),
                   dyn("interact_rate", "Interaksi", "video")],
         sorts=[["2,2", "Tayangan"], ["1,2", "Suka"], ["3,2", "Komentar"], ["5,2", "Dibagikan"],
                ["4,2", "Diteruskan"], ["10,2", "Interaksi"], ["6,2", "Terbaru"], ["7,2", "Durasi"]],
         referer="/id/media-source/video"),
    Menu("video-music", "Video", "Musik Populer",
         "Lagu/musik yang paling banyak dipakai di video TikTok.",
         "/api/music/search", "music_list",
         [Col("Musik", "entity", key="music_name", img="cover", sub="author", url="play_url"),
          N("Dipakai (video)", "user_count"), Col("Durasi", "dur", "duration"),
          Col("Resmi", "bool", "official")],
         base={"order": "1, 2"}, controls=[words("Judul lagu / penyanyi")],
         referer="/id/media-source/song"),
    Menu("video-hashtag", "Video", "Hashtag Populer",
         "Hashtag dengan peluang dan tayangan tertinggi.",
         "/api/hashtag/search", "list", HASHTAG_COLS,
         base={}, sorts=[["2,2", "Tayangan"], ["3,2", "Jumlah video"]],
         controls=[words("Hashtag"), select("date_type", "Rentang", [[7, "7 hari terakhir"], [30, "30 hari terakhir"]], 7),
                   dyn("cid", "Kategori video", "hashtag", key="video_category", advanced=False),
                   dyn("play_count", "Tayangan", "hashtag"), dyn("video_count", "Jumlah video", "hashtag")],
         referer="/id/media-source/hashtag"),
    Menu("video-ai", "Video", "Video AI Terlaris",
         "Video buatan AI dengan penjualan tertinggi.",
         "/api/video/V2/aiVideoRank", "list",
         [video(img="cover", title="video_desc", sub=""),
          Col("Produk", "entity", key="product_info.title", img="product_info.cover",
              id="product_info.product_id", link="product", sub="product_info.price"),
          N("Terjual", "product_info.sold_count"), M("Omzet", "product_info.sale_amount"),
          N("Tayangan", "play_count"), N("Suka", "digg_count"), P("Interaksi", "interaction_rate"),
          N("ROAS", "roas"), TS("Diunggah", "create_time")],
         base={"rank_type": 2}, controls=[date(["date_value"], "Tanggal data")], pagesize=12,
         referer="/id/media-source/top-ai-videos"),

    # ============================== IKLAN ==============================
    Menu("ads-search", "Iklan", "Cari Iklan",
         "Cari materi iklan video TikTok (biaya, ROAS, durasi tayang).",
         "/api/da/V4/search", "ad_list",
         [video(img="cover", title="desc", sub="advertiser"), N("Tayangan", "play_count"),
          N("Suka", "digg_count"), N("Komentar", "comment_count"), N("Dibagikan", "share_count"),
          N("Hari tayang", "put_days"), M("Estimasi biaya", "estimate_cost"), T("ROAS", "roas"),
          D("Pertama tayang", "first_put_date"), D("Terakhir tayang", "last_put_date")],
         base={"da_type": 1},
         controls=[words("Kata kunci iklan"), dyn("play_count", "Tayangan", "ads"), dyn("digg_count", "Suka", "ads"),
                   dyn("estimate_cost", "Estimasi biaya", "ads"), dyn("hotness", "Popularitas", "ads"),
                   dyn("desc_language", "Bahasa", "ads", key="language")],
         pagesize=12, referer="/id/creativecenter/search"),
    Menu("ads-seed", "Iklan", "Iklan Seeding",
         "Konten native/seeding dengan interaksi tinggi.",
         "/api/da/V4/search", "ad_list",
         [video(img="cover", title="desc", sub="advertiser"), N("Tayangan", "play_count"),
          N("Suka", "digg_count"), N("Komentar", "comment_count"), N("Dibagikan", "share_count"),
          N("Hari tayang", "put_days"), M("Estimasi biaya", "estimate_cost"), T("ROAS", "roas"),
          D("Terakhir tayang", "last_put_date")],
         base={"da_type": 1, "scene": 3}, controls=[words("Kata kunci")], pagesize=12,
         referer="/id/creativecenter/seed"),
    Menu("ads-advertiser", "Iklan", "Pengiklan Teratas",
         "Toko/pengiklan dengan belanja iklan dan penjualan iklan terbesar.",
         "/api/dar/V3/search", "list",
         [shop(sub="region_name"), M("Omzet dari iklan", "ad_sale_amount"),
          M("Estimasi biaya iklan", "estimate_cost_amount"), N("ROAS", "roas"),
          N("Video iklan", "video_count"), N("Tayangan", "play_count"), N("Produk", "product_count"),
          N("Kreator", "author_count"), P("Interaksi", "interaction_rate"),
          D("Mulai beriklan", "first_put_day"), D("Terakhir beriklan", "last_put_day")],
         base={}, controls=[words("Nama pengiklan")],
         referer="/id/creativecenter/advertiser"),
    Menu("ads-hashtag", "Iklan", "Wawasan Hashtag",
         "Tren traffic hashtag/topik populer untuk ide konten iklan.",
         "/api/hashtag/search", "list", HASHTAG_COLS,
         base={"order": "2,2"},
         controls=[words("Hashtag"), select("date_type", "Rentang", [[7, "7 hari terakhir"], [30, "30 hari terakhir"]], 7),
                   dyn("cid", "Kategori video", "hashtag", key="video_category", advanced=False)],
         referer="/id/creativecenter/insightTag"),
    Menu("ads-keywords", "Iklan", "Tren Kata Kunci",
         "Kata kunci yang sedang naik di konten TikTok.",
         "/api/da/V4/keywordsTrends", "list",
         [Col("Kata kunci", "entity", key="keyword", sub="ctime")] + TREND_COLS,
         base={}, controls=[words("Kata kunci", "keyword")],
         referer="/id/creativecenter/keyword-trends"),
    Menu("ads-categories", "Iklan", "Tren Kategori Produk",
         "Kategori produk yang sedang naik daun di konten TikTok.",
         "/api/da/V4/categoryTrends", "list",
         [Col("Kategori", "entity", key="l3_category_name", sub="l1_category_name"),
          T("Sub-kategori", "l2_category_name")] + TREND_COLS,
         base={}, controls=[],
         referer="/id/creativecenter/product-category-trends"),

    # ============================== AGENSI ==============================
    Menu("agency-rank", "Agensi", "Peringkat Agensi (CAP)",
         "Agensi/partner kreator TikTok Shop dengan omzet mingguan tertinggi.",
         "/api/AffiliatePartner/rankList", "list",
         [Col("Agensi", "entity", key="partner.company_name", img="partner.company_logo_cover",
              sub="week_no"),
          M("Omzet", "sale_amount"), P("Perubahan omzet", "sale_amount_rate"),
          N("Kreator", "author_count"), N("Kreator berjualan", "author_sale_count"),
          N("Produk", "product_count"), N("Produk terjual", "product_sale_count"),
          P("Komisi", "commission_rate"), G("Kategori laris", "hot_category")],
         base={"order": "1,2", "date_type": 2}, controls=[],
         referer="/id/agency/mcn/search"),
    Menu("agency-search", "Agensi", "Cari Agensi",
         "Cari agensi/partner kreator berdasarkan nama dan performa 7 hari.",
         "/api/affiliatePartner/search", "list",
         [Col("Agensi", "entity", key="company_name", img="partner.company_logo_cover", sub="date_range_no"),
          M("Omzet 7 hari", "sale_amount_7d"), P("Perubahan omzet", "sale_amount_rate"),
          N("Kreator", "author_count"), N("Kreator berjualan", "author_sale_count"),
          N("Produk", "product_count"), N("Produk terjual", "product_sale_count"),
          P("Komisi", "commission_rate"), G("Kategori laris", "hot_category")],
         base={"order": "1,2"}, controls=[words("Nama agensi")],
         referer="/id/agency/mcn/search-list"),
]

MENU_BY_KEY = {m.key: m for m in MENUS}
GROUP_ORDER = ["Tren Pasar", "Produk", "Kreator", "Toko", "LIVE", "Video", "Iklan", "Agensi"]


def control_params(menu: Menu) -> set[str]:
    allowed = {"page", "pagesize", "order", "region"} | set(menu.base)
    for c in menu.controls:
        if c.kind == "category":
            allowed |= set(c.levels)
        elif c.kind == "date":
            allowed |= set(c.params)
        elif c.kind == "period":
            allowed |= {"date_type", "date_value"}
        else:
            allowed.add(c.param)
    return allowed


def build_params(menu: Menu, query: dict) -> dict:
    """Gabungkan parameter bawaan menu + pilihan pengguna (hanya kunci yang dikenal)."""
    allowed = control_params(menu)
    params: dict = dict(menu.base)
    params.setdefault("pagesize", menu.pagesize)
    for c in menu.controls:
        if c.default is not None and c.kind in ("select", "period"):
            params.setdefault(c.param, c.default)
    for k, v in query.items():
        if k in allowed and v not in (None, ""):
            params[k] = v
    if menu.sorts and "order" not in query:
        params.setdefault("order", menu.sorts[0][0])
    for c in menu.controls:
        if c.kind == "period" and not params.get("date_value"):
            params["date_value"] = default_period_value(int(params.get("date_type") or 1))
        elif c.kind == "date":
            day = params.get(c.params[0]) or (_dt.date.today() - _dt.timedelta(days=c.offset)).isoformat()
            for p in c.params:
                params[p] = day
    params.setdefault("page", 1)
    return params


def default_period_value(date_type: int, today: _dt.date | None = None) -> str:
    """Nilai ``date_value`` bawaan FastMoss: kemarin / minggu lalu (ISO ``YYYY-WW``) / bulan lalu."""
    today = today or _dt.date.today()
    if date_type == 2:
        y, w, _ = (today - _dt.timedelta(days=7)).isocalendar()
        return f"{y}-{w:02d}"
    if date_type == 3:
        first = today.replace(day=1) - _dt.timedelta(days=1)
        return first.strftime("%Y-%m")
    return (today - _dt.timedelta(days=1)).isoformat()
