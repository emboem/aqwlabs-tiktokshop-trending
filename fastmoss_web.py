import streamlit as st
import requests
import pandas as pd
import time
import re
from datetime import datetime
from io import BytesIO
import plotly.graph_objects as go
from fpdf import FPDF
import tempfile

# ==========================================
# 1. KONFIGURASI & DATA
# ==========================================
HEADERS_CONFIG = {
    "authority": "www.fastmoss.com",
    "accept": "application/json, text/plain, */*",
    "lang": "ID_ID",
    "region": "ID",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "fm-sign": "a2931e9423c1d113fa167252fd4647be", 
    "cookie": "NEXT_LOCALE=id; utm_country=ID; utm_south=google; utm_id=kw_id_0923_01; utm_lang=id; fp_visid=0c428e01dea23acfe5daff8f5db0e849; _gcl_au=1.1.1091888018.1765341251; _ga=GA1.1.86921883.1765341251; gg_client_id=86921883.1765341251; _fbp=fb.1.1765341262233.460796550836126988; _tt_enable_cookie=1; _ttp=01KC38KWNN831BY9E87TZ33273_.tt.1; _gcl_gs=2.1.k1^$i1765345417^$u149463969; _gcl_aw=GCL.1765345424.Cj0KCQiArt_JBhCTARIsADQZaymphoxwEDrLZ6W9deQryISq4-Wxw86K2ANDrlGzlGLImN7OxvKDmxkaAk4VEALw_wcB; _ga_J8P3E5KDGJ=deleted; region=ID; userTimeZone=Asia^%^2FJakarta; _clck=1vkm0hs^%^5E2^%^5Eg2b^%^5E0^%^5E2170; fd_tk=67eaef52771ce1d7a92349199807a8c2; _rdt_uuid=1765341252879.3992635e-f762-4357-93f5-b07da426c2bd; _rdt_em=:ee87ac9a321a7e5876fbfe9a521777e5ec1cfbb92410f51402f52971fece3701,3fc49119e3456ef63cd48e99e7b62cae90b3cb9d850e4b106fa7b5539833ca0c; _uetsid=025f45f0e5f611f08b53ddc106d85728^|15pm7q1^|2^|g2b^|0^|2191; _uetvid=7ff62600d58111f0ac53af3c8f32e7e1^|1p2yu3k^|1767150547522^|3^|1^|bat.bing.com/p/insights/c/a"
}

try:
    from fastmoss_terlaris import CATEGORY_TREE
except ImportError:
    st.error("File 'fastmoss_terlaris.py' tidak ditemukan atau variabel CATEGORY_TREE error.")
    CATEGORY_TREE = []

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def clean_currency_to_float(value):
    if value is None: return 0.0
    if isinstance(value, (int, float)): return float(value)
    str_val = str(value)
    str_val = re.sub(r'[Rp\s%]', '', str_val)
    str_val = str_val.replace('.', '') 
    str_val = str_val.replace(',', '.')
    try: return float(str_val)
    except ValueError: return 0.0

def remove_html_tags(text):
    if not text: return "-"
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def clean_text_for_pdf(text):
    if not text: return ""
    text = str(text)
    return text.encode('latin-1', 'replace').decode('latin-1')

def get_month_list(year, range_option):
    months = []
    y = int(year)
    if range_option == "Full Year (12 Bulan)": r = range(1, 13)
    elif range_option == "Semester 1 (Jan - Jun)": r = range(1, 7)
    elif range_option == "Semester 2 (Jul - Des)": r = range(7, 13)
    elif range_option == "Q1 (Jan - Mar)": r = range(1, 4)
    elif range_option == "Q2 (Apr - Jun)": r = range(4, 7)
    elif range_option == "Q3 (Jul - Sep)": r = range(7, 10)
    elif range_option == "Q4 (Okt - Des)": r = range(10, 13)
    else: r = []
    for m in r: months.append(f"{y}-{m:02d}")
    return months

def format_date_str(date_str):
    if not date_str or date_str == "-": return "-"
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b %Y")
    except:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d %b %Y")
        except: return date_str

@st.cache_data(show_spinner=False, ttl=3600) 
def load_image_proxy(url):
    if not url: return None
    try:
        r = requests.get(url, headers=HEADERS_CONFIG, timeout=3)
        if r.status_code == 200:
            return BytesIO(r.content)
        return None
    except: return None

def create_mini_chart(dates, counts):
    if not dates or not counts: return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=counts,
        fill='tozeroy', mode='lines+markers',
        line=dict(color='#ff6b18', width=2),
        fillcolor='rgba(255, 107, 24, 0.1)',
        marker=dict(size=3, color='#ff6b18'),
        hovertemplate='%{x}<br>Jual: %{y}<extra></extra>'
    ))
    fig.update_layout(
        showlegend=False, margin=dict(l=0, r=0, t=5, b=0), height=60, 
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(showgrid=False, visible=False),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- PDF GENERATOR CLASS ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Laporan Analisis TiktokShop - Aqwam Lab', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Halaman {self.page_no()}', 0, 0, 'C')

def generate_pdf_bytes(df, title_report, target_type="Produk"):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, clean_text_for_pdf(title_report), 0, 1, 'L')
    pdf.ln(5)
    
    for idx, row in df.iterrows():
        # Cek apakah ini mode Search (punya 4 metrik) atau standar
        is_search_mode = "num_terjual_7d" in row
        
        card_height = 50 if is_search_mode else 40
        pdf.set_fill_color(250, 250, 250) 
        pdf.rect(pdf.get_x(), pdf.get_y(), 190, card_height, 'F')
        
        start_x = pdf.get_x()
        start_y = pdf.get_y()
        
        # 1. GAMBAR
        image_url = row.get("Cover")
        img_placed = False
        if image_url:
            img_data = load_image_proxy(image_url)
            if img_data:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                        tmp.write(img_data.getvalue())
                        tmp_path = tmp.name
                    pdf.image(tmp_path, x=start_x + 2, y=start_y + 2, w=36, h=36)
                    img_placed = True
                except: pass
        
        if not img_placed:
            pdf.set_xy(start_x + 2, start_y + 15)
            pdf.set_font("Arial", "I", 8)
            pdf.cell(36, 10, "No Image", 0, 0, 'C')

        # 2. INFO TENGAH
        pdf.set_xy(start_x + 40, start_y + 2)
        title_txt = row.get("Judul") or row.get("Nama Toko") or "-"
        title_txt = (title_txt[:65] + '..') if len(title_txt) > 65 else title_txt
        
        pdf.set_font("Arial", "B", 10)
        pdf.multi_cell(90, 5, clean_text_for_pdf(title_txt))
        
        pdf.set_xy(start_x + 40, pdf.get_y() + 1)
        pdf.set_font("Arial", "", 8)
        
        if target_type == "Produk":
            toko = row.get('Toko', '-')
            kat = row.get('Kategori', '-')[:40]
            price = row.get('Harga Display', '-')
            pdf.cell(90, 4, clean_text_for_pdf(f"Toko: {toko}"), 0, 1)
            pdf.set_x(start_x + 40)
            pdf.cell(90, 4, clean_text_for_pdf(f"Kat: {kat}"), 0, 1)
            pdf.set_x(start_x + 40)
            pdf.set_font("Arial", "B", 9)
            pdf.cell(90, 5, clean_text_for_pdf(f"{price}"), 0, 1)
        else: 
            rating = row.get('Rating', '-')
            jml = row.get('Jml Produk', '-')
            pdf.cell(90, 5, clean_text_for_pdf(f"Rating: {rating} | Produk: {jml}"), 0, 1)

        # 3. STATISTIK KANAN
        pdf.set_xy(start_x + 135, start_y + 2)
        
        if is_search_mode:
            # Mode Search: 4 Metrik
            pdf.set_font("Arial", "", 7)
            
            # Baris 1: 7 Hari
            pdf.cell(25, 4, "Jual (7H)", 0, 0, 'L')
            pdf.cell(30, 4, "Omzet (7H)", 0, 1, 'R')
            
            pdf.set_x(start_x + 135)
            pdf.set_font("Arial", "B", 9)
            pdf.cell(25, 5, f"{row.get('num_terjual_7d',0):,.0f}", 0, 0, 'L')
            omzet7 = f"Rp{row.get('num_omzet_7d',0):,.0f}".replace(",", ".")
            pdf.cell(30, 5, omzet7, 0, 1, 'R')
            
            pdf.ln(2)
            pdf.set_x(start_x + 135)
            
            # Baris 2: Total
            pdf.set_font("Arial", "", 7)
            pdf.cell(25, 4, "Jual (Total)", 0, 0, 'L')
            pdf.cell(30, 4, "Omzet (Total)", 0, 1, 'R')
            
            pdf.set_x(start_x + 135)
            pdf.set_font("Arial", "B", 9)
            pdf.cell(25, 5, f"{row.get('num_terjual_total',0):,.0f}", 0, 0, 'L')
            omzetT = f"Rp{row.get('num_omzet_total',0):,.0f}".replace(",", ".")
            pdf.cell(30, 5, omzetT, 0, 1, 'R')

        else:
            # Mode Standar: 2 Metrik
            metric_val = row.get("num_terjual_p") or row.get("num_terjual") or row.get("Total Terjual") or 0
            omzet_val = row.get("num_omzet_p") or row.get("num_omzet") or row.get("Total Omzet") or 0
            
            pdf.set_font("Arial", "", 8)
            pdf.cell(50, 5, "Terjual", 0, 1, 'R')
            pdf.set_x(start_x + 135)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(50, 6, f"{metric_val:,.0f}", 0, 1, 'R')
            pdf.set_x(start_x + 135)
            pdf.set_font("Arial", "", 8)
            pdf.cell(50, 5, "Omzet", 0, 1, 'R')
            pdf.set_x(start_x + 135)
            pdf.set_font("Arial", "B", 10)
            omzet_str = f"Rp{omzet_val:,.0f}".replace(",", ".")
            pdf.cell(50, 6, omzet_str, 0, 1, 'R')

        pdf.set_y(start_y + card_height + 5)
        if pdf.get_y() > 250: pdf.add_page()

    return pdf.output(dest='S').encode('latin-1', 'ignore') 

# ==========================================
# 3. KELAS SCRAPER
# ==========================================
class FastMossScraper:
    def __init__(self):
        self.headers = HEADERS_CONFIG

    def get_best_products(self, page=1, pagesize=10, time_config=None, category_config=None):
        url = "https://www.fastmoss.com/api/goods/saleRank"
        params = {
            "page": page, "pagesize": pagesize, "order": "1,2", "region": "ID",
            "_time": int(time.time()), "date_type": time_config['type'], "date_value": time_config['value']
        }
        self._add_category_params(params, category_config)
        return self._fetch_data(url, params, "rank_list")

    def get_best_shops(self, page=1, pagesize=10, time_config=None, category_config=None):
        url = "https://www.fastmoss.com/api/shop/v3/shopList"
        params = {
            "page": page, "pagesize": pagesize, "order": "1,2", "region": "ID",
            "_time": int(time.time()), "date_type": time_config['type'], "date_value": time_config['value']
        }
        self._add_category_params(params, category_config)
        return self._fetch_data(url, params, "list")

    def search_products(self, keyword, page=1, pagesize=10, category_config=None):
        url = "https://www.fastmoss.com/api/goods/V2/search"
        params = {
            "page": page, "pagesize": pagesize, "order": "2,2", "region": "ID",
            "words": keyword, "_time": int(time.time())
        }
        self._add_category_params(params, category_config)
        return self._fetch_data(url, params, "product_list")

    def _add_category_params(self, params, category_config):
        if category_config:
            if category_config.get('l1'): params["l1_cid"] = category_config['l1']
            if category_config.get('l2'): params["l2_cid"] = category_config['l2']
            if category_config.get('l3'): params["l3_cid"] = category_config['l3']

    def _fetch_data(self, url, params, data_key):
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    return data.get("data", {}).get(data_key, [])
            return []
        except: return []

    def parse_best_products(self, products_list):
        parsed_data = []
        for item in products_list:
            shop_info = item.get("shop_info", {})
            shop_name = shop_info.get("name", "-") if isinstance(shop_info, dict) else "-"
            cat_string = " > ".join(item.get("all_category_name", []) or [])
            price_raw = item.get('real_price', 0)
            launch_time = item.get("launch_time") or item.get("ctime")
            cover_url = item.get("cover")
            
            parsed_data.append({
                "Judul": item.get("title"),
                "Harga Display": price_raw, 
                "Kategori": cat_string,
                "Toko": shop_name,
                "Cover": cover_url,
                "Waktu Rilis": launch_time,
                "Link": item.get("detail_url"),
                "num_terjual_p": clean_currency_to_float(item.get("sold_count", 0)),
                "num_omzet_p": clean_currency_to_float(item.get("sale_amount", 0)),
                "num_terjual_t": clean_currency_to_float(item.get("total_sold_count", 0)),
                "num_omzet_t": clean_currency_to_float(item.get("total_sale_amount", 0)),
                "num_rating": 0
            })
        return parsed_data

    def parse_shops(self, shops_list):
        parsed_data = []
        for item in shops_list:
            shop_id = item.get("id") or item.get("seller_id")
            link_url = f"https://www.fastmoss.com/id/shop-detail/{shop_id}" if shop_id else "#"
            cover_url = item.get("avatar") 
            
            parsed_data.append({
                "Nama Toko": item.get("name"),
                "Rating": item.get("rating"),
                "Jml Produk": item.get("product_count"),
                "Cover": cover_url,
                "Link": link_url,
                "num_terjual": clean_currency_to_float(item.get("inc_sold_count", 0)),
                "num_omzet": clean_currency_to_float(item.get("inc_sale_amount", 0)),
                "num_produk": clean_currency_to_float(item.get("product_count", 0)),
                "num_rating": clean_currency_to_float(item.get("rating", 0))
            })
        return parsed_data

    # --- PERBAIKAN UTAMA DI SINI ---
    def parse_search_results(self, products_list):
        parsed_data = []
        for item in products_list:
            shop_info = item.get("shop_info", {})
            shop_name = item.get("shop_name", "-") or (shop_info.get("name", "-") if isinstance(shop_info, dict) else "-")
            cat_string = " > ".join(item.get("category_name", []) or [])
            clean_title = remove_html_tags(item.get("title"))
            price_raw = item.get('price', "0")
            launch_time = item.get("launch_time") or item.get("ctime")
            cover_url = item.get("img") or item.get("cover")
            
            # Ambil Data Trend untuk Grafik
            trend_list = item.get("trend", [])
            trend_dates = [t.get("dt") for t in trend_list]
            trend_counts = [t.get("inc_sold_count", 0) for t in trend_list]
            
            # --- FIX: DATA MAPPING ---
            # Data Periode (7 Hari)
            # Kadang 'day7_sale_amount' null, kita handle dengan fallback 0
            sold_7d = item.get("day7_sold_count", 0)
            omzet_7d = item.get("day7_sale_amount", 0) 
            
            # Jika day7_sale_amount 0 tapi ada data trend, kita bisa hitung estimasi (Sold * Harga)
            # Tapi sebaiknya pakai raw data dulu jika ada
            if omzet_7d == 0 and sum(trend_counts) > 0:
               # Estimasi kasar: Total trend sold * harga saat ini
               omzet_7d = sum(trend_counts) * clean_currency_to_float(price_raw)

            # Data Total (Seumur Hidup)
            sold_total = item.get("sold_count", 0)
            omzet_total = item.get("sale_amount", 0)
            
            parsed_data.append({
                "Judul": clean_title,
                "Harga Display": price_raw,
                "Kategori": cat_string,
                "Toko": shop_name,
                "Cover": cover_url,
                "Waktu Rilis": launch_time,
                "Link": item.get("detail_url"),
                "trend_dates": trend_dates,
                "trend_counts": trend_counts,
                
                # Masukkan ke key spesifik agar bisa dibaca render_universal_card
                "num_terjual_7d": clean_currency_to_float(sold_7d),
                "num_omzet_7d": clean_currency_to_float(omzet_7d),
                "num_terjual_total": clean_currency_to_float(sold_total),
                "num_omzet_total": clean_currency_to_float(omzet_total),
                
                "num_rating": 0
            })
        return parsed_data

# ==========================================
# 4. TAMPILAN WEB (STREAMLIT)
# ==========================================

st.set_page_config(page_title="Aqwam Lab Tool | Tiktokshop", layout="wide")
st.title("🕵️ Tiktokshop Trending Product")
st.caption("Scraper data produk terlaris dan toko terlaris dari FastMoss.com")

if 'scraped_data' not in st.session_state: st.session_state['scraped_data'] = None
if 'active_mode' not in st.session_state: st.session_state['active_mode'] = None
if 'active_target_type' not in st.session_state: st.session_state['active_target_type'] = "Produk"
if 'active_title' not in st.session_state: st.session_state['active_title'] = "Hasil Analisis"

with st.sidebar:
    st.header("⚙️ Panel Kontrol")
    mode = st.radio("🎯 Pilih Mode", ["🔍 Cari Produk (Keyword)", "📦 Produk Terlaris", "🏪 Toko Terlaris", "📈 Analisis Tren (Multi-Bulan)"])
    st.divider()
    time_config = {"type": "1", "value": ""}
    keyword = ""
    multi_month_target = "Produk"
    selected_months = []

    if mode == "📈 Analisis Tren (Multi-Bulan)":
        st.subheader("1. Konfigurasi Tren")
        multi_month_target = st.selectbox("Analisis Apa?", ["Produk", "Toko"])
        col_y, col_r = st.columns(2)
        with col_y: year_val = st.number_input("Tahun", min_value=2023, max_value=2030, value=datetime.now().year)
        with col_r:
            range_opt = st.selectbox("Rentang", ["Full Year (12 Bulan)", "Semester 1 (Jan - Jun)", "Semester 2 (Jul - Des)", "Q1 (Jan - Mar)", "Q2 (Apr - Jun)", "Q3 (Jul - Sep)", "Q4 (Okt - Des)"])
        selected_months = get_month_list(year_val, range_opt)
        st.caption(f"Akan memproses: {len(selected_months)} bulan")
    elif mode == "🔍 Cari Produk (Keyword)":
        st.subheader("1. Kata Kunci")
        keyword = st.text_input("Masukkan Nama Produk", placeholder="Contoh: Buku Anak...")
    else: 
        st.subheader("1. Filter Waktu")
        time_option = st.selectbox("Pilih Periode", ["Harian", "Mingguan", "Bulanan"])
        if time_option == "Harian":
            date_type = "1"
            d = st.date_input("Pilih Tanggal", datetime.now()); date_val = d.strftime("%Y-%m-%d")
        elif time_option == "Mingguan":
            date_type = "2"; date_val = st.text_input("Masukkan Minggu", value=datetime.now().strftime("%Y-%W"))
        else: 
            date_type = "3"; date_val = st.text_input("Masukkan Bulan", value=datetime.now().strftime("%Y-%m"))
        time_config = {"type": date_type, "value": date_val}

    st.subheader("2. Filter Kategori")
    l1_opts = {item['label']: item for item in CATEGORY_TREE}
    selected_l1_label = st.selectbox("Kategori Utama (L1)", ["Semua"] + list(l1_opts.keys()))
    l1_val, l2_val, l3_val = None, None, None
    if selected_l1_label != "Semua":
        l1_data = l1_opts[selected_l1_label]; l1_val = l1_data['value']
        if 'children' in l1_data:
            l2_opts = {item['label']: item for item in l1_data['children']}
            selected_l2_label = st.selectbox("Sub Kategori (L2)", ["Semua"] + list(l2_opts.keys()))
            if selected_l2_label != "Semua":
                l2_data = l2_opts[selected_l2_label]; l2_val = l2_data['value']
                if 'children' in l2_data:
                    l3_opts = {item['label']: item for item in l2_data['children']}
                    selected_l3_label = st.selectbox("Sub-Sub Kategori (L3)", ["Semua"] + list(l3_opts.keys()))
                    if selected_l3_label != "Semua": l3_val = l3_opts[selected_l3_label]['value']

    st.subheader("3. Opsi Scraping")
    max_pages = st.number_input("Jumlah Halaman (max 10)", min_value=1, max_value=10, value=1)
    disable_btn = (mode == "🔍 Cari Produk (Keyword)" and not keyword)
    start_btn = st.button(f"🚀 Mulai ({mode})", type="primary", disabled=disable_btn)

# --- GLOBAL RENDER CARD FUNCTION ---
def render_universal_card(row, mode_type, label_metric="Terjual", label_omzet="Omzet"):
    LABEL_MAP = {
        "num_terjual_p": "Terjual (Periode)",
        "num_omzet_p": "Omzet (Periode)",
        "num_terjual": "Terjual",
        "num_omzet": "Omzet",
        "Total Terjual": "Total Terjual (Akumulasi)",
        "Total Omzet": "Total Omzet (Akumulasi)"
    }
    
    # Deteksi apakah ini data Search (punya key spesifik)
    is_search_data = "num_terjual_7d" in row

    with st.container(border=True):
        c_img, c_info, c_stats = st.columns([1, 2.5, 1.5])
        
        with c_img:
            image_url = row.get("Cover")
            if image_url:
                img_data = load_image_proxy(image_url) 
                if img_data: st.image(img_data, use_container_width=True)
                else: st.markdown("📷 *Gagal*")
            else: st.markdown("🖼️ *No Image*")

        with c_info:
            title_key = "Judul" if "Judul" in row else "Nama Toko"
            st.markdown(f"##### {row.get(title_key, '-')}")
            if "Judul" in row: # Produk
                st.caption(f"🏪 Toko: **{row.get('Toko', '-')}**")
                cat = row.get('Kategori', '-')
                if len(cat) > 50: cat = cat[:50] + "..."
                st.caption(f"📂 Kat: {cat}")
                col_p, col_d = st.columns(2)
                with col_p: st.markdown(f"🏷️ **{row.get('Harga Display', 'Rp0')}**")
                with col_d:
                    release_date = row.get('Waktu Rilis')
                    if release_date:
                        fmt_date = format_date_str(release_date)
                        st.caption(f"🚀 Rilis: **{fmt_date}**")
            else: # Toko
                st.caption(f"⭐ Rating: {row.get('Rating', '-')}")
                st.caption(f"📦 Produk Aktif: {row.get('Jml Produk', '-')}")
            st.link_button("🔗 Lihat di FastMoss", row.get('Link', '#'))

        with c_stats:
            st.markdown("##### 📊 Performa")
            
            # --- MODIFIKASI TAMPILAN KHUSUS SEARCH ---
            if is_search_data:
                # Tampilkan Grid 4 Metrik
                c1, c2 = st.columns(2)
                with c1:
                    st.caption("7 Hari Terakhir")
                    st.metric("Terjual", f"{row.get('num_terjual_7d',0):,.0f}")
                    omzet7 = f"Rp{row.get('num_omzet_7d',0):,.0f}".replace(",", ".")
                    st.metric("Omzet", omzet7)
                with c2:
                    st.caption("Total (Lifetime)")
                    st.metric("Terjual", f"{row.get('num_terjual_total',0):,.0f}")
                    omzetT = f"Rp{row.get('num_omzet_total',0):,.0f}".replace(",", ".")
                    st.metric("Omzet", omzetT)
            else:
                # Tampilan Standar (2 Metrik)
                final_label_metric = LABEL_MAP.get(label_metric, label_metric)
                final_label_omzet = LABEL_MAP.get(label_omzet, label_omzet)
                
                val_metric = row.get(label_metric)
                if val_metric is None: 
                    if "Judul" in row:
                        val_metric = row.get("num_terjual_p", 0)
                        val_omzet = row.get("num_omzet_p", 0)
                    else:
                        val_metric = row.get("num_terjual", 0)
                        val_omzet = row.get("num_omzet", 0)
                else: val_omzet = row.get(label_omzet, 0)

                st.metric(label=final_label_metric, value=f"{val_metric:,.0f}")
                omzet_str = f"Rp{val_omzet:,.0f}".replace(",", ".")
                st.metric(label=final_label_omzet, value=omzet_str)

            # Tampilkan Grafik Tren jika ada
            if row.get('trend_dates') and row.get('trend_counts'):
                if sum(row['trend_counts']) > 0:
                    st.caption("📉 Tren 7 Hari Terakhir:")
                    fig = create_mini_chart(row['trend_dates'], row['trend_counts'])
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            if 'Frekuensi Bulan' in row:
                st.info(f"📅 Konsistensi: **{row['Frekuensi Bulan']} bln**")
                if 'List Bulan' in row and row['List Bulan']: st.caption(f"🗓️ *Bulan: {row['List Bulan']}*")

# --- LOGIKA UTAMA (PROSES & SIMPAN KE SESSION STATE) ---
if start_btn:
    scraper = FastMossScraper()
    cat_config = {"l1": l1_val, "l2": l2_val, "l3": l3_val}
    temp_data = [] 
    
    if mode == "📈 Analisis Tren (Multi-Bulan)":
        progress_bar = st.progress(0); status_text = st.empty()
        total_steps = len(selected_months) * max_pages; current_step = 0
        for idx_m, month_str in enumerate(selected_months):
            for page in range(1, max_pages + 1):
                status_text.markdown(f"⏳ Sedang mengambil data **{month_str}** (Halaman {page})...")
                curr_time_config = {"type": "3", "value": month_str}
                try:
                    if multi_month_target == "Produk":
                        raw = scraper.get_best_products(page=page, time_config=curr_time_config, category_config=cat_config)
                        parsed = scraper.parse_best_products(raw)
                    else: 
                        raw = scraper.get_best_shops(page=page, time_config=curr_time_config, category_config=cat_config)
                        parsed = scraper.parse_shops(raw)
                    for p in parsed: p['Bulan'] = month_str 
                    temp_data.extend(parsed)
                except: pass
                current_step += 1; progress_bar.progress(current_step / total_steps); time.sleep(1) 
        status_text.success("✅ Selesai mengambil data tren!")
        st.session_state['active_title'] = f"Laporan Tren {multi_month_target} ({selected_months[0]} s/d {selected_months[-1]})"
        st.session_state['active_target_type'] = multi_month_target

    else:
        progress_bar = st.progress(0); status_text = st.empty()
        for i in range(1, max_pages + 1):
            status_text.text(f"Mengambil halaman {i} dari {max_pages}...")
            if mode == "📦 Produk Terlaris":
                raw = scraper.get_best_products(page=i, time_config=time_config, category_config=cat_config)
                if raw: temp_data.extend(scraper.parse_best_products(raw))
            elif mode == "🏪 Toko Terlaris":
                raw = scraper.get_best_shops(page=i, time_config=time_config, category_config=cat_config)
                if raw: temp_data.extend(scraper.parse_shops(raw))
            elif mode == "🔍 Cari Produk (Keyword)":
                raw = scraper.search_products(keyword=keyword, page=i, category_config=cat_config)
                if raw: temp_data.extend(scraper.parse_search_results(raw))
            progress_bar.progress(i / max_pages); time.sleep(1)
        status_text.success("Selesai!")

        if mode == "🔍 Cari Produk (Keyword)":
            st.session_state['active_title'] = f"Hasil Pencarian: '{keyword}'"
            st.session_state['active_target_type'] = "Produk"
        elif mode == "📦 Produk Terlaris":
            st.session_state['active_title'] = f"Produk Terlaris ({time_option})"
            st.session_state['active_target_type'] = "Produk"
        else:
            st.session_state['active_title'] = f"Toko Terlaris ({time_option})"
            st.session_state['active_target_type'] = "Toko"

    if temp_data:
        st.session_state['scraped_data'] = pd.DataFrame(temp_data)
        st.session_state['active_mode'] = mode
    else:
        st.session_state['scraped_data'] = None; st.warning("Data tidak ditemukan.")

# --- TAMPILAN DATA DARI SESSION STATE ---
if st.session_state['scraped_data'] is not None:
    df = st.session_state['scraped_data']
    active_mode = st.session_state['active_mode']
    active_title = st.session_state['active_title']
    target_type = st.session_state['active_target_type'] 

    if active_mode == "📈 Analisis Tren (Multi-Bulan)":
        key_col = "Judul" if target_type == "Produk" else "Nama Toko"
        metric_col = "num_terjual_p" if target_type == "Produk" else "num_terjual"
        omzet_col = "num_omzet_p" if target_type == "Produk" else "num_omzet"
        
        group_cols = [key_col, 'Link', 'Cover']
        if target_type == "Produk": group_cols.extend(['Toko', 'Kategori', 'Harga Display', 'Waktu Rilis'])
        else: group_cols.extend(['Rating', 'Jml Produk']) 

        st.divider(); st.header(f"📊 {active_title}")
        
        df_total = df.groupby(group_cols).agg(
            num_total=(metric_col, 'sum'),
            num_omzet=(omzet_col, 'sum'),
            Frekuensi_Bulan=('Bulan', 'nunique'),
            List_Bulan=('Bulan', lambda x: ', '.join(sorted(x.unique())))
        ).reset_index()
        
        df_total = df_total.rename(columns={'num_total': 'Total Terjual', 'num_omzet': 'Total Omzet', 'Frekuensi_Bulan': 'Frekuensi Bulan', 'List_Bulan': 'List Bulan'})
        df_total = df_total.sort_values('Total Terjual', ascending=False).reset_index(drop=True)

        tab1, tab2, tab3 = st.tabs(["🏆 Juara Umum", "💎 Konsistensi", "📅 Breakdown"])

        with tab1:
            st.subheader("🏆 Top Performance")
            for idx, row in df_total.head(50).iterrows():
                render_universal_card(row, "trend", label_metric="Total Terjual", label_omzet="Total Omzet")
            st.divider(); c_csv, c_pdf = st.columns(2)
            with c_csv:
                csv_data = df_total.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Excel/CSV", csv_data, "trend_report.csv", "text/csv", use_container_width=True)
            with c_pdf:
                if st.button("📄 Generate PDF Report (Juara Umum)", key="pdf_trend"):
                    with st.spinner("Sedang membuat PDF..."):
                        pdf_bytes = generate_pdf_bytes(df_total.head(50), active_title, target_type)
                        st.download_button("⬇️ Download PDF", pdf_bytes, "trend_report.pdf", "application/pdf", use_container_width=True)

        with tab2:
            st.subheader("💎 Tingkat Konsistensi")
            freqs = sorted(df_total['Frekuensi Bulan'].unique(), reverse=True)
            for freq in freqs:
                subset = df_total[df_total['Frekuensi Bulan'] == freq].sort_values('Total Terjual', ascending=False).head(5)
                with st.expander(f"🗓️ Muncul di {freq} Bulan ({len(subset)} Item)", expanded=(freq==freqs[0])):
                    for idx, row in subset.iterrows():
                        render_universal_card(row, "trend", label_metric="Total Terjual", label_omzet="Total Omzet")

        with tab3:
            st.subheader("📅 Kilas Balik Per Bulan")
            months_avail = sorted(df['Bulan'].unique())
            for bulan in months_avail:
                df_bulan = df[df['Bulan'] == bulan].sort_values(metric_col, ascending=False).head(5)
                if not df_bulan.empty:
                    st.markdown(f"### 🗓️ {bulan}")
                    for idx, row in df_bulan.iterrows():
                        row_mod = row.copy()
                        row_mod['Terjual Bulan Ini'] = row[metric_col]
                        row_mod['Omzet Bulan Ini'] = row[omzet_col]
                        render_universal_card(row_mod, "trend", label_metric="Terjual Bulan Ini", label_omzet="Omzet Bulan Ini")
                    st.divider()

    else:
        st.divider(); st.subheader(active_title)
        for idx, row in df.iterrows():
            if active_mode == "🏪 Toko Terlaris":
                render_universal_card(row, "single", label_metric="num_terjual", label_omzet="num_omzet")
            else:
                render_universal_card(row, "single", label_metric="num_terjual_p", label_omzet="num_omzet_p")
        
        st.divider(); c_csv, c_pdf = st.columns(2)
        with c_csv:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", data=csv, file_name=f"data_fastmoss.csv", mime="text/csv", use_container_width=True)
        with c_pdf:
            if st.button("📄 Generate PDF Report", key="pdf_single"):
                with st.spinner("Sedang menggambar PDF dari kartu produk..."):
                    pdf_bytes = generate_pdf_bytes(df, active_title, target_type)
                    st.download_button("⬇️ Download PDF", pdf_bytes, "laporan_produk.pdf", "application/pdf", use_container_width=True)

else:
    if not start_btn: st.info("👈 Silakan konfigurasi di menu samping dan klik 'Mulai'.")


