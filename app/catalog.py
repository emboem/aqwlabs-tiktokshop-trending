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
    type: str                 # entity | num | money | pct | text | tags | date | ts | dur | price | spark | bool | props
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
    kind: str                 # text | select | period | date | range | dperiod | category | dynselect | view
    options: list = field(default_factory=list)   # [[value, label], ...]
    default: Any = None
    source: str = ""          # dynselect/category: nama sumber opsi (lihat OPTION_SOURCES; "@x" = opsi milik detail)
    key: str = ""             # dynselect: kunci daftar di respons sumber
    params: list = field(default_factory=list)    # date/range: param tanggal | dperiod: param lain yang ikut diisi
    offset: int = 1           # date/range: tanggal bawaan & paling akhir = hari ini - offset
    advanced: bool = False    # tampil di panel "Filter lanjutan"
    levels: list = field(default_factory=lambda: ["l1_cid", "l2_cid", "l3_cid"])
    min: str = ""             # period/date/range: tanggal paling awal ("YYYY-MM-DD" atau "-15" = 15 hari lalu)
    max_days: int = 0         # range/dperiod: panjang rentang maksimum (0 = bebas)
    span: list = field(default_factory=list)      # dperiod: [param awal, param akhir] untuk rentang kustom
    picker: list = field(default_factory=list)    # period: date_type yang punya kalender (kosong = semua)
    multi: bool = False       # dynselect: boleh pilih lebih dari satu (dikirim dipisah koma)
    custom: bool = False      # dynselect: boleh isi rentang Min–Maks sendiri ("min,max", -1 = tanpa batas)
    when: dict = field(default_factory=dict)      # tampil & dikirim hanya bila param lain bernilai tertentu
    local: bool = False       # bagian detail ber-sync: kontrol ini milik bagiannya sendiri (tidak dibagi)


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
FM_MIN_DATE = "2022-07-31"     # tanggal paling awal di kalender peringkat FastMoss


def period(daily=True, weekly=True, monthly=True, default=1, min=FM_MIN_DATE, options=None, picker=()) -> Control:
    """Peringkat Harian/Mingguan/Bulanan + kalender (hari kemarin / minggu lalu / bulan lalu)."""
    opts = options or [o for o, on in (([1, "Harian"], daily), ([2, "Mingguan"], weekly), ([3, "Bulanan"], monthly)) if on]
    return Control("date_type", "Periode", "period", opts, default, min=min, picker=list(picker))


def select(param, label, opts, default=None, advanced=False, when=None) -> Control:
    return Control(param, label, "select", [list(o) for o in opts], default, advanced=advanced, when=when or {})


def words(label="Kata kunci", param="words") -> Control:
    return Control(param, label, "text")


def category(source="goods", levels=("l1_cid", "l2_cid", "l3_cid"), advanced=False, key="", label="Kategori") -> Control:
    """Kategori bertingkat. ``key`` = kunci pohon di respons sumber (bawaan "category")."""
    return Control("category", label, "category", source=source, key=key, levels=list(levels), advanced=advanced)


SALE_CATS = ("sale_category_l1", "sale_category_l2", "sale_category_l3")


def seller() -> Control:
    """Penjual lokal / lintas negara (Full-service hanya ada di negara Barat — tidak relevan untuk ID)."""
    return select("seller_type", "Penjual", [["", "Semua"], [1, "Lokal"], [2, "Lintas negara"]], advanced=True)


def fixed(param, label, opts, advanced=True, when=None) -> Control:
    """Filter berpilihan tetap (mengikuti FastMoss) dengan opsi "Semua" di depan."""
    return select(param, label, [["", "Semua"]] + [list(o) for o in opts], advanced=advanced, when=when)


GENDER = [[1, "Mayoritas pria"], [0, "Mayoritas wanita"]]
AGE = [[1, "18–24"], [2, "25–34"], [3, "35+"]]


def dyn(param, label, source, key=None, advanced=True, multi=False, custom=False, when=None) -> Control:
    return Control(param, label, "dynselect", source=source, key=key or param, advanced=advanced,
                   multi=multi, custom=custom, when=when or {})


def date(params, label="Tanggal", offset=1, min="") -> Control:
    return Control(params[0], label, "date", params=list(params), offset=offset, min=min)


def rng(params, label, max_days=0, offset=1, auto=False, min="", advanced=False) -> Control:
    """Rentang tanggal bebas (dua param). ``auto`` = selalu terisi (bawaan: satu hari, hari ini - offset)."""
    return Control(params[0], label, "range", params=list(params), offset=offset, max_days=max_days,
                   default="auto" if auto else None, min=min, advanced=advanced)


def dperiod(param, label, presets, default, span=("start_date", "end_date"), max_days=180, also=(),
            advanced=False, offset=1) -> Control:
    """Pilihan cepat (7/28/90 hari …) **atau** rentang kustom ``span`` (maks. ``max_days`` hari, s/d hari ini - offset).

    Nilai ``"custom"`` pada ``param`` berarti rentang kustom: param pilihan cepat tidak dikirim.
    ``also`` = param lain yang diisi nilai pilihan cepat yang sama (mis. ``d_type`` + ``date_type``).
    """
    return Control(param, label, "dperiod", [list(o) for o in presets], default, params=list(also),
                   span=list(span), max_days=max_days, advanced=advanced, offset=offset)


def view(param, label, opts, default) -> Control:
    """Pilihan tampilan (tidak dikirim ke FastMoss) — mis. Unit/Omzet pada grafik yang sama."""
    return Control(param, label, "view", [list(o) for o in opts], default)


def _day(spec: str, today: _dt.date) -> _dt.date | None:
    if not spec:
        return None
    if spec.lstrip("-").isdigit():
        return today - _dt.timedelta(days=abs(int(spec)))
    return _dt.date.fromisoformat(spec)


def check_range(start: Any, end: Any, max_days: int = 0, offset: int = 1, min: str = "",
                today: _dt.date | None = None) -> tuple[str, str]:
    """Validasi rentang tanggal kustom. Mengembalikan (awal, akhir) ISO atau melempar ValueError berbahasa Indonesia."""
    today = today or _dt.date.today()
    try:
        s, e = _dt.date.fromisoformat(str(start)), _dt.date.fromisoformat(str(end))
    except ValueError:
        raise ValueError("Format tanggal rentang harus YYYY-MM-DD.") from None
    if s > e:
        s, e = e, s
    latest = today - _dt.timedelta(days=offset)
    if e > latest:
        raise ValueError(f"Tanggal akhir paling lambat {latest.isoformat()} (data FastMoss belum tersedia setelahnya).")
    earliest = _day(min, today)
    if earliest and s < earliest:
        raise ValueError(f"Tanggal awal paling cepat {earliest.isoformat()}.")
    if max_days and (e - s).days + 1 > max_days:
        raise ValueError(f"Rentang tanggal maksimal {max_days} hari.")
    return s.isoformat(), e.isoformat()


def apply_dperiod(c: Control, query: dict, params: dict) -> None:
    """Isi ``params`` dari kontrol dperiod: pilihan cepat, atau rentang kustom tervalidasi."""
    v = query.get(c.param)
    if v in (None, ""):
        v = c.default
    for p in [c.param, *c.params, *c.span]:
        params.pop(p, None)
    if str(v) == "custom" and c.span:
        s, e = check_range(query.get(c.span[0]), query.get(c.span[1]), c.max_days, c.offset, c.min)
        params[c.span[0]], params[c.span[1]] = s, e
    elif v not in (None, ""):
        for p in [c.param, *c.params]:
            params[p] = v


def active(c: Control, values: dict) -> bool:
    """Kontrol bersyarat (``when``) hanya berlaku bila param pemicunya bernilai yang diminta."""
    return all(str(values.get(k, "")) in [str(x) for x in (v if isinstance(v, list) else [v])]
               for k, v in c.when.items())


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
    "insights": "/api/da/V4/insightsFilter",
    "dar": "/api/dar/V3/filterInfo",                 # filter pengiklan
    "topcat": "/api/top/categoryList",               # kategori kreator di halaman peringkat kreator
    "potential": "/api/author/potential/filterInfo", # pengikut kreator potensial
}

# nilai `df` yang dikirim halaman pencarian kreator (btoa("fs_" + origin + "_ps"))
_DF = base64.b64encode(b"fs_https://www.fastmoss.com_ps").decode()

# Kode urutan (order) hasil uji langsung ke API FastMoss.
RANK_SORTS = [["1,2", "Terjual (periode)"], ["7,2", "Omzet (periode)"], ["6,2", "Pertumbuhan"],
              ["3,2", "Total terjual"], ["4,2", "Kreator (periode)"], ["5,2", "Total kreator"]]
FOLLOWER_SORTS = [["1,2", "Pengikut baru"], ["2,2", "Total pengikut"]]
SHOP_RANK_SORTS = [["1,2", "Terjual (periode)"], ["2,2", "Omzet (periode)"], ["3,2", "Pertumbuhan terjual"],
                   ["6,2", "Pertumbuhan omzet"], ["4,2", "Jumlah kreator"]]
# Kode urutan LIVE berbeda per endpoint: di /live/V2/search total penonton = 3 (4 = rata-rata penonton),
# sedangkan di /live/rank total penonton = 4 (3 = rata-rata penonton).
LIVE_SEARCH_SORTS = [["1,2", "Terjual"], ["2,2", "Omzet"], ["3,2", "Total penonton"], ["5,2", "Waktu mulai"],
                     ["7,2", "Puncak penonton"], ["4,2", "Rata-rata penonton"], ["6,2", "Nilai per penonton"]]
LIVE_RANK_SORTS = [["1,2", "Terjual"], ["2,2", "Omzet"], ["4,2", "Total penonton"], ["7,2", "Puncak penonton"],
                   ["5,2", "Waktu mulai"], ["3,2", "Rata-rata penonton"], ["6,2", "Nilai per penonton"]]

AD_SORTS = [["", "Urutan bawaan"], ["1,2", "Tayangan"], ["2,2", "Suka"], ["3,2", "Komentar"], ["4,2", "Dibagikan"],
            ["5,2", "ROAS"], ["6,2", "Estimasi biaya"], ["7,2", "Rasio suka/pengikut"], ["8,2", "Hari tayang"]]

PRODUCT_RANK_COLS = [
    product(sub=""),
    Col("Toko", "entity", key="shop_info.name", img="shop_info.avatar", id="shop_info.seller_id", link="shop"),
    Col("Harga", "price", "real_price"),
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
# Toko Populer: FastMoss menaruh "kreator baru yang mempromosikan" sebagai kolom utama
SHOP_POP_COLS = [SHOP_RANK_COLS[0], N("Kreator baru", "inc_author_count")] + \
    [c for c in SHOP_RANK_COLS[1:] if c.key != "inc_author_count"]

LIVE_COLS = [
    live(), TS("Mulai", "create_time"), Col("Durasi", "dur", "duration"),
    N("Terjual", "sold_count"), M("Omzet", "sale_amount"), N("Penonton", "total_user_count"),
    N("Puncak penonton", "max_user_count"), N("Produk", "product_count"), M("Nilai per penonton", "uv_value"),
    N("Pengikut baru", "inc_follower_count"), G("Kategori laris", "hot_category"),
]

HASHTAG_COLS = [
    Col("Hashtag", "entity", key="label_name", sub="region_name"),
    N("Skor peluang", "opportunity"), N("Impresi", "play_count"), N("Jumlah video", "video_count"),
]


def ad_col() -> Col:
    """Kartu iklan → halaman Detail Iklan (ID iklan FastMoss, bukan ID video)."""
    return Col("Iklan", "entity", key="desc", img="cover", sub="advertiser", id="id", link="ad")


def agency_col(key, sub="") -> Col:
    return Col("Agensi", "entity", key=key, img="partner.company_logo_cover", sub=sub, id="partner_secid", link="agency")


def ad_metric_filters() -> list:
    return [dyn("estimate_cost", "Belanja iklan", "ads"), dyn("estimated_conversion", "Estimasi konversi", "ads"),
            dyn("play_count", "Tayangan", "ads"), dyn("hotness", "Interaksi", "ads"),
            dyn("digg_count", "Suka", "ads"), dyn("comment_count", "Komentar", "ads"),
            dyn("share_count", "Dibagikan", "ads"),
            dyn("digg_follower_rate", "Rasio suka/pengikut", "ads", key="digg_follow_rate"),
            dyn("desc_language", "Bahasa", "ads", key="language"),
            fixed("duration", "Durasi video", [["0,15", "< 15 detik"], ["15,30", "15–30 detik"],
                                               ["30,60", "30–60 detik"], ["60,-1", "> 60 detik"]]),
            dyn("aspect_ratio", "Resolusi", "ads"),
            fixed("put_days", "Hari tayang", [["0,1", "Tayang perdana"], ["2,-1", "Iklan berulang"],
                                              ["1,3", "1–3 hari"], ["3,10", "3–10 hari"], ["10,-1", "> 10 hari"]])]

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
          N("Terjual {last_date_type} hari", "last_sold_count"), M("Omzet {last_date_type} hari", "last_sale_amount"),
          N("Total terjual", "sold_count"), M("Total omzet", "sale_amount"),
          N("Kreator", "relate_author_count"), N("Video", "relate_video_count"), N("LIVE", "relate_live_count"),
          N("Rating", "product_rating"), P("Rasio order kreator", "author_order_rate"),
          G("Kategori", "category_name_l3"), D("Rilis", "launch_time"),
          Col("Tren {last_date_type} hari", "spark", "trend", x="dt", y="inc_sold_count")],
         base={},
         controls=[words("Kata kunci produk"), select("last_date_type", "Rentang data", DAYS_7_28, 7),
                   category(),
                   dyn("price_amount", "Harga", "goods", custom=True), dyn("crate", "Komisi", "goods"),
                   fixed("commerce_type", "Format jual", [[1, "Video"], [2, "LIVE"]]), seller(),
                   dyn("day7_sale_amount", "Omzet 7 hari", "goods", when={"last_date_type": 7}),
                   dyn("day28_sale_amount", "Omzet 28 hari", "goods", when={"last_date_type": 28}),
                   dyn("day7_sold_count", "Terjual 7 hari", "goods", when={"last_date_type": 7}),
                   dyn("day28_sold_count", "Terjual 28 hari", "goods", when={"last_date_type": 28}),
                   dyn("sold_count", "Total terjual", "goods"), dyn("sale_amount", "Total omzet", "goods"),
                   dyn("relate_author_count", "Jumlah kreator", "goods", key="relate_author"),
                   dyn("relate_video_count", "Jumlah video", "goods", key="relate_video"),
                   dyn("launch_date", "Waktu rilis", "goods"),
                   dyn("author_order_rate", "Rasio order kreator", "goods")],
         sorts=[["2,2", "Terjual {last_date_type} hari"], ["7,2", "Omzet {last_date_type} hari"],
                ["14,2", "Rasio order dari kreator"], ["3,2", "Total terjual"], ["8,2", "Total omzet"], ["4,2", "Jumlah kreator"],
                ["6,2", "Jumlah video"], ["5,2", "Jumlah LIVE"], ["9,2", "Terbaru"]],
         referer="/id/e-commerce/search"),
    Menu("product-sales", "Produk", "Produk Terlaris",
         "Peringkat produk dengan penjualan tertinggi per hari, minggu, atau bulan.",
         "/api/goods/saleRank", "rank_list", PRODUCT_RANK_COLS,
         base={}, controls=[period(), category(), seller()], sorts=RANK_SORTS + [["15,2", "Total omzet"]],
         referer="/id/e-commerce/saleslist"),
    Menu("product-new", "Produk", "Produk Baru Laris",
         "Produk yang baru rilis dan langsung laku.",
         "/api/goods/newProduct", "list",
         [product(), Col("Harga", "price", "real_price"),
          N("Terjual 3 hari sejak rilis", "sold_count"), M("Omzet 3 hari sejak rilis", "sale_amount"),
          N("Total terjual", "total_sold_count"), M("Total omzet", "total_sale_amount"),
          P("Komisi", "commission_rate"), N("Kreator", "author_count"), N("Video", "aweme_count"),
          N("LIVE", "live_count"), G("Kategori", "category_name"), D("Rilis", "launch_time")],
         base={"rank_type": 11},
         sorts=[["1,2", "Terjual 3 hari sejak rilis"], ["2,2", "Omzet 3 hari sejak rilis"], ["3,2", "Total terjual"],
                ["4,2", "Total omzet"]],
         controls=[rng(["start_date", "end_date"], "Waktu peluncuran", max_days=30, offset=3, auto=True), category(),
                   seller()],
         referer="/id/e-commerce/newProducts"),
    Menu("product-hot", "Produk", "Produk Populer",
         "Produk yang paling banyak dipromosikan kreator.",
         "/api/goods/popRank", "rank_list",
         PRODUCT_RANK_COLS[:10] + [N("Total kreator", "total_author_count")] + PRODUCT_RANK_COLS[10:],
         base={}, controls=[period(), category(), seller()],
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
         controls=[words("Kata kunci produk"), select("rank_type", "Video diunggah", DAYS_7_28_90, 7), category()],
         sorts=[["1,2", "Terjual"], ["2,2", "Omzet"], ["7,2", "Jumlah video"], ["3,2", "Tayangan"],
                ["4,2", "Suka"], ["5,2", "Komentar"], ["6,2", "Dibagikan"]],
         referer="/id/e-commerce/hotvideo"),

    # ============================== KREATOR ==============================
    Menu("creator-search", "Kreator", "Cari Kreator",
         "Cari kreator/affiliate berdasarkan kategori, pengikut, dan penjualan.",
         "/api/author/search", "author_list",
         [creator(), G("Kategori", "category"), N("Pengikut", "follower_count"),
          N("Pengikut baru ({last_date_type}h)", "last_follower_count"),
          N("Rata-rata tayangan ({last_date_type}h)", "last_avg_play_count"), P("Interaksi", "interaction_v1_rate"),
          N("Terjual ({last_date_type}h)", "last_sold_count"), M("Omzet ({last_date_type}h)", "last_sale_amount"),
          Col("Tren penjualan", "spark", "sale_count_list.list", x="dt", y="value"),
          M("Omzet video (28h)", "video_28d_sale_amount"), M("Omzet LIVE (28h)", "live_28d_sale_amount"),
          N("Video (28h)", "aweme_28d_count"), N("Rasio suka/pengikut", "like_followers_than"),
          D("Video pertama", "first_video_time"), G("Kategori jualan", "sale_category_l3_name")],
         base={"shop_window": 1, "is_shop": 0, "df": _DF},
         controls=[words("Nama / username kreator"),
                   select("words_search_type", "Cari di", [[1, "Nama / ID kreator"], [2, "Hashtag video"]], 1),
                   select("last_date_type", "Rentang data", DAYS_7_28, 28),
                   category("author", SALE_CATS, key="product_category", label="Kategori penjualan"),
                   dyn("cid", "Kategori kreator", "author", key="author_category"),
                   select("shop_window", "Etalase", [[1, "Punya etalase"], [0, "Semua"]], 1, advanced=True),
                   select("is_shop", "Akun toko resmi", [[0, "Kecualikan"], [-1, "Sertakan"]], 0, advanced=True),
                   fixed("verify", "Centang biru", [[2, "Terverifikasi"], [1, "Belum terverifikasi"]]),
                   fixed("product", "Format jual", [[2, "LIVE"], [3, "Video"]], when={"shop_window": 1}),
                   fixed("gender", "Penonton", GENDER), fixed("age", "Usia penonton", AGE),
                   dyn("first_video_time", "Video pertama", "author"),
                   dyn("sale_amount", "Total omzet", "author"), dyn("sold_count", "Total terjual", "author"),
                   dyn("like_followers_v1_rate", "Rasio suka/pengikut", "author"),
                   dyn("performance_rate", "Pemenuhan pesanan", "author"),
                   dyn("follower", "Pengikut", "author", key="follower_count"),
                   dyn("follower_28d_count", "Pengikut baru 28h", "author"),
                   dyn("d7_sale_amount", "Omzet 7 hari", "author", when={"last_date_type": 7}),
                   dyn("d28_sale_amount", "Omzet 28 hari", "author", when={"last_date_type": 28}),
                   dyn("d7_sold_count", "Terjual 7 hari", "author", when={"last_date_type": 7}),
                   dyn("d28_sold_count", "Terjual 28 hari", "author", when={"last_date_type": 28}),
                   dyn("interaction_v1_rate", "Interaksi", "author"),
                   dyn("avg_28d_play_count", "Rata-rata tayangan 28h", "author"),
                   fixed("available_contact", "Kontak", [[-1, "Tersedia"]]),
                   dyn("contact_method", "Metode kontak", "author", multi=True),
                   dyn("contact_platform", "Platform kontak", "author", multi=True)],
         sorts=[["12,2", "Terjual {last_date_type} hari"], ["7,2", "Omzet {last_date_type} hari"],
                ["1,2", "Pengikut"], ["2,2", "Pengikut baru {last_date_type} hari"], ["3,2", "Jumlah video"],
                ["6,2", "Rata-rata tayangan {last_date_type} hari"],
                ["8,2", "Interaksi"], ["9,2", "Rasio suka/pengikut"], ["13,2", "Video pertama"],
                ["10,2", "Video produk 28 hari"], ["11,2", "LIVE produk 28 hari"]],
         referer="/id/influencer/search"),
    Menu("creator-fans", "Kreator", "Pertumbuhan Pengikut",
         "Kreator dengan kenaikan pengikut tertinggi.",
         "/api/followers/followersList", "list", CREATOR_GROWTH_COLS,
         base={"type": 1}, sorts=FOLLOWER_SORTS,
         controls=[period(monthly=True), dyn("cid", "Kategori kreator", "topcat", key="list", advanced=False)],
         referer="/id/influencer/tiktok/fans"),
    Menu("creator-commerce", "Kreator", "Kreator Penjual Terlaris",
         "Kreator e-commerce dengan omzet penjualan tertinggi.",
         "/api/ecommerce/rank", "list",
         [creator(), G("Kategori", "category_name"), N("Pengikut", "follower_count"),
          M("Total omzet", "total_amount"), N("Total terjual", "total_sold_count"),
          M("Omzet video", "video_amount"), N("Terjual via video", "video_sold_count"),
          M("Omzet LIVE", "live_amount"), N("Terjual via LIVE", "live_sold_count"),
          N("Produk", "product_count"), N("Video", "video_count"), N("LIVE", "live_count")],
         base={},
         controls=[period(), dyn("cid", "Kategori kreator", "topcat", key="list", advanced=False),
                   fixed("ecommerce_type", "Kanal jualan", [[2, "Lewat LIVE"], [1, "Lewat video"]], advanced=False),
                   category("author", SALE_CATS, key="product_category", label="Kategori penjualan", advanced=True),
                   fixed("author_type", "Jenis akun", [[1, "Akun toko"], [2, "Akun pribadi"]])],
         sorts=[["1,2", "Total omzet"], ["2,2", "Omzet video"], ["3,2", "Omzet LIVE"]],
         referer="/id/influencer/tiktok/commerceTop"),
    Menu("creator-bluev", "Kreator", "Kreator Terverifikasi",
         "Pertumbuhan pengikut kreator bercentang biru.",
         "/api/followers/followersList", "list", CREATOR_GROWTH_COLS,
         base={"type": 2}, sorts=FOLLOWER_SORTS,
         controls=[period(), dyn("cid", "Kategori kreator", "topcat", key="list", advanced=False)],
         referer="/id/influencer/tiktok/blue-v"),
    Menu("creator-popular", "Kreator", "Kreator Paling Disukai",
         "Kreator dengan tambahan suka, komentar, dan bagikan terbanyak.",
         "/api/followers/followersList", "list", CREATOR_GROWTH_COLS,
         base={"type": 3}, sorts=FOLLOWER_SORTS[::-1],
         controls=[period(), dyn("cid", "Kategori kreator", "topcat", key="list", advanced=False)],
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
         controls=[period(options=[[1, "28 hari terakhir"], [2, "Mingguan"], [3, "Bulanan"]], picker=[2, 3]),
                   dyn("cid", "Kategori kreator", "topcat", key="list", advanced=False),
                   category("author", SALE_CATS, key="product_category", label="Kategori penjualan", advanced=True),
                   dyn("follower", "Pengikut", "potential", key="follower_cnt", custom=True),
                   fixed("gender", "Penonton", GENDER), fixed("age", "Usia penonton", AGE),
                   fixed("ecommerce_method", "Kanal jualan", [[2, "LIVE"], [1, "Video"]])],
         sorts=[["1,2", "Indeks potensi"], ["2,2", "Total omzet"]],
         referer="/id/influencer/tiktok/potentialTop"),

    # ============================== TOKO ==============================
    Menu("shop-search", "Toko", "Cari Toko",
         "Cari toko TikTok Shop berdasarkan nama, kategori, dan performa.",
         "/api/shop/v3/search", "list",
         [shop(img="shop_info.avatar", title="shop_info.name", sub="shop_info.category_name"),
          N("Terjual {last_date_type} hari", "last_sold_count"), M("Omzet {last_date_type} hari", "last_sale_amount"),
          Col("Tren {last_date_type} hari", "spark", "trend", x="dt", y="inc_sold_count"),
          N("Produk laku 7 hari", "day7_product_count"), P("Rasio produk baru", "new_product_rate"),
          N("Total terjual", "sold_count"), M("Total omzet", "sale_amount"),
          N("Produk dijual", "on_sell_product_count"), N("Kreator penjual", "sales_author_count"),
          N("Rating toko", "shop_rating")],
         base={},
         sorts=[["1,2", "Terjual {last_date_type} hari"], ["2,2", "Omzet {last_date_type} hari"],
                ["4,2", "Rasio produk baru"], ["5,2", "Total terjual"],
                ["6,2", "Total omzet"], ["3,2", "Jumlah produk"], ["9,2", "Kreator penjual"]],
         controls=[words("Nama toko"), select("last_date_type", "Rentang data", DAYS_7_28, 7),
                   category("shop"),
                   dyn("day7_sale_amount_range", "Omzet 7 hari", "shop", key="day7_sale_amount",
                       when={"last_date_type": 7}),
                   dyn("day28_sale_amount_range", "Omzet 28 hari", "shop", key="day28_sale_amount",
                       when={"last_date_type": 28}),
                   dyn("day7_sold_count_range", "Terjual 7 hari", "shop", key="day7_sold_count",
                       when={"last_date_type": 7}),
                   dyn("day28_sold_count_range", "Terjual 28 hari", "shop", key="day28_sold_count",
                       when={"last_date_type": 28}),
                   dyn("sold_count_range", "Total terjual", "shop", key="sold_count"),
                   dyn("sale_amount_range", "Total omzet", "shop", key="sale_amount"),
                   dyn("shop_rating_range", "Rating toko", "shop", key="shop_rating"),
                   dyn("sales_author_count_range", "Kreator penjual", "shop", key="sales_author_count"),
                   fixed("product_count_range", "Jumlah produk", [["0,50", "< 50"], ["50,100", "50–100"],
                                                                   ["100,500", "100–500"], ["500,1000", "500–1.000"],
                                                                   ["1000,-1", "1.000+"]]),
                   seller(),
                   dyn("new_product_rate_range", "Rasio produk baru", "shop", key="new_product_rate")],
         referer="/id/shop-marketing/search"),
    Menu("shop-sales", "Toko", "Toko Terlaris",
         "Peringkat toko dengan omzet tertinggi.",
         "/api/shop/v3/shopList", "list", SHOP_RANK_COLS,
         base={}, controls=[period(), category("shop"), seller()], sorts=SHOP_RANK_SORTS,
         referer="/id/shop-marketing/tiktok"),
    Menu("shop-hot", "Toko", "Toko Populer",
         "Toko yang paling banyak dipromosikan kreator.",
         "/api/shop/v3/shopPopList", "list", SHOP_POP_COLS,
         base={}, controls=[period(), category("shop"), seller()], sorts=[["5,2", "Kreator baru"]] + SHOP_RANK_SORTS,
         referer="/id/shop-marketing/hotTiktok"),

    # ============================== LIVE ==============================
    Menu("live-search", "LIVE", "Cari Siaran LIVE",
         "Cari siaran LIVE jualan berdasarkan kata kunci dan performa.",
         "/api/live/V2/search", "live_list", LIVE_COLS,
         base={}, sorts=LIVE_SEARCH_SORTS,
         controls=[words("Judul / kreator"),
                   dperiod("date_type", "Rentang waktu", DAYS_7_28_90, 7, max_days=0, offset=0),
                   dyn("cid", "Kategori kreator", "live", key="author_category", advanced=False),
                   dyn("pcid", "Kategori produk", "live", key="product_category", advanced=False),
                   fixed("is_shop", "Jenis siaran", [[1, "Siaran toko"], [0, "Siaran kreator"]]),
                   fixed("is_live", "Status", [[1, "Sedang LIVE"]]),
                   dyn("follower_count", "Pengikut", "live"), dyn("total_user_count", "Penonton", "live"),
                   dyn("sold_count", "Terjual", "live")],
         referer="/id/live/search"),
    Menu("live-rank", "LIVE", "LIVE Terlaris",
         "Siaran LIVE dengan omzet tertinggi (pantauan terbaru).",
         "/api/live/rank", "live_list", LIVE_COLS,
         base={}, sorts=LIVE_RANK_SORTS,
         controls=[dyn("cid", "Kategori kreator", "live", key="author_category", advanced=False),
                   dyn("pcid", "Kategori produk", "live", key="product_category", advanced=False)],
         referer="/id/live/tiktok"),
    Menu("live-products", "LIVE", "Produk Laris di LIVE",
         "Produk dengan penjualan tertinggi lewat siaran LIVE.",
         "/api/live/v3/hotProduct", "rank_list",
         [product(sub="shop.name"), Col("Harga", "price", "real_price"),
          N("Terjual via LIVE", "live_sold_count"), M("Omzet LIVE", "live_sale_amount"),
          N("Jumlah LIVE", "live_count"), G("Kategori", "category_name_l3"), D("Tanggal", "dt")],
         base={}, controls=[period(), dyn("pcid", "Kategori produk", "live", key="product_category", advanced=False)],
         sorts=[["1,2", "Terjual via LIVE"], ["2,2", "Omzet LIVE"], ["3,2", "Jumlah LIVE"]],
         referer="/id/live/hotProduct"),
    Menu("live-creators", "LIVE", "Kreator LIVE Terlaris",
         "Kreator dengan omzet LIVE shopping tertinggi.",
         "/api/ecommerce/liveRank", "list",
         [creator(), G("Kategori", "category_name"), N("Pengikut", "follower_count"),
          M("Omzet LIVE", "live_amount"), N("Terjual via LIVE", "live_sold_count"),
          N("Jumlah LIVE", "live_count"), N("Produk", "product_count"),
          M("GPM tertinggi", "live_gpm_max"), D("Tanggal", "dt")],
         base={}, controls=[period(),
                            dyn("cid", "Kategori kreator", "topcat", key="list", advanced=False),
                            dyn("pcid", "Kategori penjualan", "live", key="product_category", advanced=False)],
         sorts=[["1,2", "Omzet LIVE"], ["2,2", "Terjual via LIVE"]],
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
                   dyn("interact_rate", "Interaksi", "video"),
                   fixed("bind_product", "Mempromosikan produk", [[1, "Ya"], [0, "Tidak"]])],
         sorts=[["2,2", "Tayangan"], ["1,2", "Suka"], ["11,2", "Pengikut kreator"], ["3,2", "Komentar"],
                ["5,2", "Dibagikan"],
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
         base={}, sorts=[["2,2", "Impresi"], ["3,2", "Jumlah video"]],
         controls=[words("Hashtag"), select("date_type", "Rentang", [[7, "7 hari terakhir"], [30, "30 hari terakhir"]], 7),
                   dyn("cid", "Kategori video", "hashtag", key="video_category", advanced=False),
                   dyn("play_count", "Impresi", "hashtag"), dyn("video_count", "Jumlah video", "hashtag")],
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
         base={}, controls=[select("rank_type", "Peringkat", [[2, "Penjualan teratas"], [4, "ROAS teratas"],
                                                             [1, "Impresi teratas"], [3, "Interaksi teratas"]], 2),
                            date(["date_value"], "Tanggal peringkat", min="-15"), category()], pagesize=12,
         referer="/id/media-source/top-ai-videos"),

    # ============================== IKLAN ==============================
    Menu("ads-search", "Iklan", "Cari Iklan",
         "Cari materi iklan video TikTok (biaya, ROAS, durasi tayang).",
         "/api/da/V4/search", "ad_list",
         [ad_col(), N("Tayangan", "play_count"),
          N("Suka", "digg_count"), N("Komentar", "comment_count"), N("Dibagikan", "share_count"),
          N("Hari tayang", "put_days"), M("Estimasi biaya", "estimate_cost"), T("ROAS", "roas"),
          D("Pertama tayang", "first_put_date"), D("Terakhir tayang", "last_put_date")],
         base={"da_type": 1}, sorts=AD_SORTS,
         controls=[words("Kata kunci iklan"), dperiod("date_type", "Waktu rilis", [["", "Semua"], [1, "7 hari"], [3, "28 hari"], [4, "90 hari"], [5, "180 hari"]],
                           "", span=("video_create_start_date", "video_create_end_date"), max_days=0),
                   rng(["last_start_date", "last_end_date"], "Periode kampanye"),
                   fixed("scene", "Jenis kampanye", [[1, "Salin produk viral"], [2, "Iklan toko"],
                                                     [4, "Promosi kreator"], [5, "Iklan komisi"]], advanced=False),
                   category(advanced=True),
                   fixed("shop_system", "Sistem e-niaga", [[1, "TikTok Shop"], [2, "Shopify"]]),
                   fixed("web_url", "Halaman tujuan", [[1, "Ada"], [2, "Tidak ada"]]),
                   fixed("is_spark", "Iklan Spark", [[1, "Iklan Spark"], [2, "Bukan Iklan Spark"]]),
                   fixed("roas", "ROAS", [["0,2", "< 2"], ["2,4", "2–4"], ["4,-1", "> 4"]]),
                   dyn("button_text", "Tombol CTA", "ads")] + ad_metric_filters(),
         pagesize=12, referer="/id/creativecenter/search"),
    Menu("ads-seed", "Iklan", "Iklan Seeding",
         "Konten native/seeding dengan interaksi tinggi.",
         "/api/da/V4/search", "ad_list",
         [ad_col(), N("Tayangan", "play_count"),
          N("Suka", "digg_count"), N("Komentar", "comment_count"), N("Dibagikan", "share_count"),
          N("Hari tayang", "put_days"), M("Estimasi biaya", "estimate_cost"), T("ROAS", "roas"),
          D("Terakhir tayang", "last_put_date")],
         sorts=[s for s in AD_SORTS if s[0] != "5,2"],
         base={"da_type": 1, "scene": 3}, controls=[words("Kata kunci"), dperiod("date_type", "Waktu rilis", [["", "Semua"], [1, "7 hari"], [3, "28 hari"], [4, "90 hari"], [5, "180 hari"]],
                           "", span=("video_create_start_date", "video_create_end_date"), max_days=0),
                   rng(["last_start_date", "last_end_date"], "Periode kampanye")] + ad_metric_filters(), pagesize=12,
         referer="/id/creativecenter/seed"),
    Menu("ads-advertiser", "Iklan", "Pengiklan Teratas",
         "Toko/pengiklan dengan belanja iklan dan penjualan iklan terbesar.",
         "/api/dar/V3/search", "list",
         [Col("Pengiklan", "entity", key="name", img="avatar", sub="region_name", id="id", link="advertiser"),
          M("Omzet dari iklan", "ad_sale_amount"),
          M("Estimasi biaya iklan", "estimate_cost_amount"), N("ROAS", "roas"),
          N("Video iklan", "video_count"), N("Tayangan", "play_count"), N("Produk", "product_count"),
          N("Kreator", "author_count"), P("Interaksi", "interaction_rate"),
          D("Mulai beriklan", "first_put_day"), D("Terakhir beriklan", "last_put_day")],
         base={}, controls=[words("Nama pengiklan"),
                            dperiod("date_type", "Waktu ditemukan", [["", "Semua"], [1, "7 hari"], [3, "28 hari"],
                                                                     [4, "90 hari"]], "",
                                    span=("last_start_date", "last_end_date"), max_days=0),
                            fixed("dar_type", "Jenis pengiklan", [[1, "Pengiklan baru"], [2, "Pengiklan berulang"]],
                                  advanced=False),
                            dyn("estimate_cost", "Belanja iklan", "dar"), dyn("play_count", "Tayangan", "dar"),
                            dyn("video_count", "Kreatif iklan", "dar"), dyn("roas", "ROAS", "dar"),
                            dyn("interaction_rate", "Interaksi", "dar"), dyn("sold_count", "Penjualan iklan", "dar")],
         sorts=[["", "Urutan bawaan"], ["1,2", "ROAS"], ["2,2", "Total tayangan"], ["3,2", "Kreatif iklan"],
                ["4,2", "Belanja iklan"]],
         referer="/id/creativecenter/advertiser"),
    Menu("ads-hashtag", "Iklan", "Wawasan Hashtag",
         "Tren traffic hashtag/topik populer untuk ide konten iklan.",
         "/api/hashtag/search", "list", HASHTAG_COLS,
         base={}, sorts=[["2,2", "Impresi"], ["3,2", "Jumlah video"], ["1,2", "Skor peluang (pilih kategori produk)"]],
         controls=[words("Hashtag"), select("date_type", "Rentang", [[7, "7 hari terakhir"], [30, "30 hari terakhir"]], 7),
                   dyn("cid", "Kategori video", "hashtag", key="video_category", advanced=False),
                   category(levels=("l1_cid",), label="Kategori produk"),
                   fixed("tag_type", "Tipe hashtag", [[1, "Hashtag populer"], [2, "Hashtag potensial"]], advanced=False),
                   dyn("play_count", "Impresi", "hashtag"), dyn("video_count", "Jumlah video", "hashtag")],
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
         [agency_col("partner.company_name", sub="week_no"),
          M("Omzet", "sale_amount"), P("Perubahan omzet", "sale_amount_rate"),
          N("Kreator", "author_count"), N("Kreator berjualan", "author_sale_count"),
          N("Produk", "product_count"), N("Produk terjual", "product_sale_count"),
          P("Komisi", "commission_rate"), G("Kategori laris", "hot_category")],
         base={"order": "1,2"},
         controls=[period(options=[[2, "Mingguan"], [3, "Bulanan"]], default=2, min="2025-01-01")],
         referer="/id/agency/mcn/search"),
    Menu("agency-search", "Agensi", "Cari Agensi",
         "Cari agensi/partner kreator berdasarkan nama dan performa 7 hari.",
         "/api/affiliatePartner/search", "list",
         [agency_col("company_name", sub="date_range_no"),
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
        elif c.kind in ("date", "range"):
            allowed |= set(c.params)
        elif c.kind == "period":
            allowed |= {"date_type", "date_value"}
        elif c.kind == "dperiod":
            allowed |= {c.param, *c.params, *c.span}
        elif c.kind != "view":
            allowed.add(c.param)
    return allowed


def build_params(menu: Menu, query: dict) -> dict:
    """Gabungkan parameter bawaan menu + pilihan pengguna (hanya kunci yang dikenal).

    Melempar ValueError (pesan Indonesia) bila rentang tanggal kustom tidak valid.
    """
    allowed = control_params(menu)
    params: dict = dict(menu.base)
    params.setdefault("pagesize", menu.pagesize)
    for c in menu.controls:
        if c.default is not None and c.kind in ("select", "period"):
            params.setdefault(c.param, c.default)
    for k, v in query.items():
        if k in allowed and v not in (None, ""):
            params[k] = v
    if menu.sorts and "order" not in query and menu.sorts[0][0]:   # order "" = urutan bawaan FastMoss (tak dikirim)
        params.setdefault("order", menu.sorts[0][0])
    today = _dt.date.today()
    for c in menu.controls:
        if c.when and not active(c, params):
            for p in ([c.param] if c.kind != "category" else c.levels):
                params.pop(p, None)
        elif c.kind == "period" and not params.get("date_value"):
            params["date_value"] = default_period_value(int(params.get("date_type") or 1))
        elif c.kind == "date":
            day = params.get(c.params[0]) or (today - _dt.timedelta(days=c.offset)).isoformat()
            for p in c.params:
                params[p] = day
        elif c.kind == "range":
            s, e = params.get(c.params[0]), params.get(c.params[1])
            if s or e:
                params[c.params[0]], params[c.params[1]] = check_range(s or e, e or s, c.max_days, c.offset, c.min)
            elif c.default == "auto":
                params[c.params[0]] = params[c.params[1]] = (today - _dt.timedelta(days=c.offset)).isoformat()
        elif c.kind == "dperiod":
            apply_dperiod(c, query, params)
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
