import streamlit as st
import requests
import pandas as pd
import time
import re
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. KONFIGURASI & DATA
# ==========================================
HEADERS_CONFIG = {
    "authority": "www.fastmoss.com",
    "accept": "application/json, text/plain, */*",
    "lang": "ID_ID",
    "region": "ID",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # PENTING: Update fm-sign dan cookie jika expired
    "fm-sign": "16fa6f79d7617ab63b9180aeb907b6bd", 
    "cookie": "NEXT_LOCALE=id; region=ID; utm_country=ID; utm_south=google; utm_id=kw_id_0923_01; utm_lang=id; userTimeZone=Asia%2FJakarta; _tt_enable_cookie=1; _ttp=01KC38KWNN831BY9E87TZ33273_.tt.1; fd_tk=3e275cb3799bba9d7a56995ef346c97a; _uetsid=7ff5cb70d58111f0a836a985b4652589|124paud|2|g1q|0|2170; _uetvid=7ff62600d58111f0ac53af3c8f32e7e1|1q6zulx|1765341784970|9|1|bat.bing.com/p/insights/c/l"
}

# Import CATEGORY_TREE
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

def get_month_list(year, range_option):
    """Generate list bulan YYYY-MM berdasarkan opsi user"""
    months = []
    y = int(year)
    
    if range_option == "Full Year (12 Bulan)":
        r = range(1, 13)
    elif range_option == "Semester 1 (Jan - Jun)":
        r = range(1, 7)
    elif range_option == "Semester 2 (Jul - Des)":
        r = range(7, 13)
    elif range_option == "Q1 (Jan - Mar)":
        r = range(1, 4)
    elif range_option == "Q2 (Apr - Jun)":
        r = range(4, 7)
    elif range_option == "Q3 (Jul - Sep)":
        r = range(7, 10)
    elif range_option == "Q4 (Okt - Des)":
        r = range(10, 13)
    else:
        r = []

    for m in r:
        months.append(f"{y}-{m:02d}")
    return months

def format_date_str(date_str):
    """Format tanggal dari YYYY-MM-DD HH:MM:SS ke format yang lebih enak dibaca"""
    if not date_str or date_str == "-": return "-"
    try:
        # Coba parsing format lengkap
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d %b %Y")
    except:
        try:
            # Fallback jika hanya tanggal
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d %b %Y")
        except:
            return date_str

# ==========================================
# 3. KELAS SCRAPER
# ==========================================
class FastMossScraper:
    def __init__(self):
        self.headers = HEADERS_CONFIG

    # --- MODE 1: PRODUK TERLARIS ---
    def get_best_products(self, page=1, pagesize=10, time_config=None, category_config=None):
        url = "https://www.fastmoss.com/api/goods/saleRank"
        params = {
            "page": page, "pagesize": pagesize, "order": "1,2", "region": "ID",
            "_time": int(time.time()), "date_type": time_config['type'], "date_value": time_config['value']
        }
        self._add_category_params(params, category_config)
        return self._fetch_data(url, params, "rank_list")

    # --- MODE 2: TOKO TERLARIS ---
    def get_best_shops(self, page=1, pagesize=10, time_config=None, category_config=None):
        url = "https://www.fastmoss.com/api/shop/v3/shopList"
        params = {
            "page": page, "pagesize": pagesize, "order": "1,2", "region": "ID",
            "_time": int(time.time()), "date_type": time_config['type'], "date_value": time_config['value']
        }
        self._add_category_params(params, category_config)
        return self._fetch_data(url, params, "list")

    # --- MODE 3: PENCARIAN KEYWORD ---
    def search_products(self, keyword, page=1, pagesize=10, category_config=None):
        url = "https://www.fastmoss.com/api/goods/V2/search"
        params = {
            "page": page, "pagesize": pagesize, "order": "2,2", "region": "ID",
            "words": keyword, "_time": int(time.time())
        }
        self._add_category_params(params, category_config)
        return self._fetch_data(url, params, "product_list")

    # --- PRIVATE HELPERS ---
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

    # --- PARSERS (UPDATED WITH COVER & LAUNCH TIME) ---
    def parse_best_products(self, products_list):
        parsed_data = []
        for item in products_list:
            shop_info = item.get("shop_info", {})
            shop_name = shop_info.get("name", "-") if isinstance(shop_info, dict) else "-"
            cat_string = " > ".join(item.get("all_category_name", []) or [])
            price_raw = item.get('real_price', 0)
            
            # Extract Launch Time & Cover
            launch_time = item.get("launch_time") or item.get("ctime")
            cover_url = item.get("cover")
            
            parsed_data.append({
                "Judul": item.get("title"),
                "Harga Display": price_raw, 
                "Kategori": cat_string,
                "Toko": shop_name,
                "Cover": cover_url, # NEW
                "Waktu Rilis": launch_time, # NEW
                "Link": item.get("detail_url"),
                "num_terjual_p": clean_currency_to_float(item.get("sold_count", 0)),
                "num_omzet_p": clean_currency_to_float(item.get("sale_amount", 0)),
                "num_terjual_t": clean_currency_to_float(item.get("total_sold_count", 0)),
                "num_omzet_t": clean_currency_to_float(item.get("total_sale_amount", 0)),
                "num_rating": 0 # Placeholder for aggregation
            })
        return parsed_data

    def parse_shops(self, shops_list):
        parsed_data = []
        for item in shops_list:
            shop_id = item.get("id") or item.get("seller_id")
            link_url = f"https://www.fastmoss.com/id/shop-detail/{shop_id}" if shop_id else "#"
            
            # Shops usually use 'avatar' as cover
            cover_url = item.get("avatar") 
            
            parsed_data.append({
                "Nama Toko": item.get("name"),
                "Rating": item.get("rating"),
                "Jml Produk": item.get("product_count"),
                "Cover": cover_url, # NEW
                "Link": link_url,
                "num_terjual": clean_currency_to_float(item.get("inc_sold_count", 0)),
                "num_omzet": clean_currency_to_float(item.get("inc_sale_amount", 0)),
                "num_produk": clean_currency_to_float(item.get("product_count", 0)),
                "num_rating": clean_currency_to_float(item.get("rating", 0))
            })
        return parsed_data

    def parse_search_results(self, products_list):
        parsed_data = []
        for item in products_list:
            shop_info = item.get("shop_info", {})
            shop_name = item.get("shop_name", "-") or (shop_info.get("name", "-") if isinstance(shop_info, dict) else "-")
            cat_string = " > ".join(item.get("category_name", []) or [])
            clean_title = remove_html_tags(item.get("title"))
            price_raw = item.get('price', "0")
            
            # Extract Launch Time & Cover
            launch_time = item.get("launch_time") or item.get("ctime")
            cover_url = item.get("cover")
            
            parsed_data.append({
                "Judul": clean_title,
                "Harga Display": price_raw,
                "Kategori": cat_string,
                "Toko": shop_name,
                "Cover": cover_url, # NEW
                "Waktu Rilis": launch_time, # NEW
                "Link": item.get("detail_url"),
                "num_terjual_p": item.get("day7_sold_count", 0), 
                "num_omzet_p": item.get("day7_sale_amount", 0),
                "num_terjual_t": item.get("sold_count", 0),
                "num_omzet_t": item.get("sale_amount", 0),
                "num_rating": 0
            })
        return parsed_data

# ==========================================
# 4. TAMPILAN WEB (STREAMLIT)
# ==========================================

st.set_page_config(page_title="Aqwam Lab Tool | Tiktokshop", layout="wide")
st.title("🕵️ Tiktokshop Trending Product")
st.caption("Scraper data produk terlaris dan toko terlaris dari FastMoss.com")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Panel Kontrol")
    mode = st.radio("🎯 Pilih Mode", [
        "🔍 Cari Produk (Keyword)", 
        "📦 Produk Terlaris", 
        "🏪 Toko Terlaris",
        "📈 Analisis Tren (Multi-Bulan)"
        ])
    st.divider()

    time_config = {"type": "1", "value": ""}
    keyword = ""
    multi_month_target = "Produk" # Default
    selected_months = []

    if mode == "📈 Analisis Tren (Multi-Bulan)":
        st.subheader("1. Konfigurasi Tren")
        multi_month_target = st.selectbox("Analisis Apa?", ["Produk", "Toko"])
        col_y, col_r = st.columns(2)
        with col_y:
            year_val = st.number_input("Tahun", min_value=2023, max_value=2030, value=datetime.now().year)
        with col_r:
            range_opt = st.selectbox("Rentang", [
                "Full Year (12 Bulan)", "Semester 1 (Jan - Jun)", "Semester 2 (Jul - Des)",
                "Q1 (Jan - Mar)", "Q2 (Apr - Jun)", "Q3 (Jul - Sep)", "Q4 (Okt - Des)"
            ])
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
            d = st.date_input("Pilih Tanggal", datetime.now())
            date_val = d.strftime("%Y-%m-%d")
        elif time_option == "Mingguan":
            date_type = "2"
            date_val = st.text_input("Masukkan Minggu", value=datetime.now().strftime("%Y-%W"))
        else: 
            date_type = "3"
            date_val = st.text_input("Masukkan Bulan", value=datetime.now().strftime("%Y-%m"))
        time_config = {"type": date_type, "value": date_val}

    st.subheader("2. Filter Kategori")
    l1_opts = {item['label']: item for item in CATEGORY_TREE}
    selected_l1_label = st.selectbox("Kategori Utama (L1)", ["Semua"] + list(l1_opts.keys()))
    l1_val, l2_val, l3_val = None, None, None
    if selected_l1_label != "Semua":
        l1_data = l1_opts[selected_l1_label]
        l1_val = l1_data['value']
        if 'children' in l1_data:
            l2_opts = {item['label']: item for item in l1_data['children']}
            selected_l2_label = st.selectbox("Sub Kategori (L2)", ["Semua"] + list(l2_opts.keys()))
            if selected_l2_label != "Semua":
                l2_data = l2_opts[selected_l2_label]
                l2_val = l2_data['value']
                if 'children' in l2_data:
                    l3_opts = {item['label']: item for item in l2_data['children']}
                    selected_l3_label = st.selectbox("Sub-Sub Kategori (L3)", ["Semua"] + list(l3_opts.keys()))
                    if selected_l3_label != "Semua": l3_val = l3_opts[selected_l3_label]['value']

    st.subheader("3. Opsi Scraping")
    max_pages = st.number_input("Jumlah Halaman (max 10)", min_value=1, max_value=10, value=1)
    
    disable_btn = (mode == "🔍 Cari Produk (Keyword)" and not keyword)
    start_btn = st.button(f"🚀 Mulai ({mode})", type="primary", disabled=disable_btn)

# --- GLOBAL RENDER CARD FUNCTION (BERLAKU UNTUK SEMUA MODE) ---
def render_universal_card(row, mode_type, label_metric="Terjual", label_omzet="Omzet"):
    """
    Fungsi render kartu standar untuk semua mode.
    Menampilkan: Cover Image (Kiri), Info Detail (Tengah), Statistik (Kanan)
    """
    with st.container(border=True):
        # Layout 3 Kolom: Gambar | Info | Statistik
        c_img, c_info, c_stats = st.columns([1, 2.5, 1.5])
        
        # 1. Kolom Gambar
        with c_img:
            if row.get("Cover"):
                st.image(row["Cover"], use_container_width=True)
            else:
                st.markdown("🖼️ *No Image*")

        # 2. Kolom Info
        with c_info:
            # Tentukan Key Judul (Produk vs Toko)
            title_key = "Judul" if "Judul" in row else "Nama Toko"
            
            # Judul Kecil (H5)
            st.markdown(f"##### {row.get(title_key, '-')}")
            
            # Detail Info
            if "Judul" in row: # Konteks Produk
                st.caption(f"🏪 Toko: **{row.get('Toko', '-')}**")
                # Kategori (pendekkan jika terlalu panjang)
                cat = row.get('Kategori', '-')
                if len(cat) > 50: cat = cat[:50] + "..."
                st.caption(f"📂 Kat: {cat}")
                
                # Harga & Tanggal Rilis
                col_p, col_d = st.columns(2)
                with col_p:
                    st.markdown(f"🏷️ **{row.get('Harga Display', 'Rp0')}**")
                with col_d:
                    release_date = row.get('Waktu Rilis')
                    if release_date:
                        fmt_date = format_date_str(release_date)
                        st.caption(f"🚀 Rilis: **{fmt_date}**")
            else: # Konteks Toko
                st.caption(f"⭐ Rating: {row.get('Rating', '-')}")
                st.caption(f"📦 Produk Aktif: {row.get('Jml Produk', '-')}")

            st.link_button("🔗 Lihat di FastMoss", row.get('Link', '#'))

        # 3. Kolom Statistik
        with c_stats:
            st.markdown("##### 📊 Performa")
            
            # Metric Utama
            # Logic: Gunakan metric_col yang dikirim atau cari default
            metric_val = 0
            omzet_val = 0
            
            # Mapping manual jika key berbeda antar mode
            if mode_type == "trend":
                # Di mode trend, kolom sudah diagregasi (Total_Jual -> num_terjual_p)
                # Lihat mapping di fungsi utama nanti
                pass 
            
            # Tampilkan Metric
            # Pastikan row[column] adalah float/int
            
            # Coba ambil value berdasarkan label (untuk mode Trend yg kolomnya dinamis)
            # Atau ambil langsung dari row jika nama kolom standar
            
            val_metric = row.get(label_metric) # Jika dikirim dari loop Trend sudah angka
            if val_metric is None: 
                # Fallback ke nama kolom standar scraping
                if "Judul" in row: # Produk
                    val_metric = row.get("num_terjual_p", 0)
                    val_omzet = row.get("num_omzet_p", 0)
                else: # Toko
                    val_metric = row.get("num_terjual", 0)
                    val_omzet = row.get("num_omzet", 0)
            else:
                val_omzet = row.get(label_omzet, 0)

            st.metric(label=label_metric.replace("num_", "").title(), value=f"{val_metric:,.0f}")
            
            omzet_str = f"Rp{val_omzet:,.0f}".replace(",", ".")
            st.metric(label="Omzet", value=omzet_str)

            # Info Tambahan untuk Mode Trend
            if 'Frekuensi Bulan' in row:
                st.info(f"📅 Konsistensi: **{row['Frekuensi Bulan']} bln**")
                if 'List Bulan' in row and row['List Bulan']:
                     st.caption(f"🗓️ *Bulan: {row['List Bulan']}*")


# --- LOGIKA UTAMA ---
if start_btn:
    scraper = FastMossScraper()
    cat_config = {"l1": l1_val, "l2": l2_val, "l3": l3_val}
    all_data = []
    
    # ========================================================
    # MODE 1: ANALISIS TREN (MULTI BULAN)
    # ========================================================
    if mode == "📈 Analisis Tren (Multi-Bulan)":
        progress_bar = st.progress(0)
        status_text = st.empty()
        total_steps = len(selected_months) * max_pages
        current_step = 0

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
                    all_data.extend(parsed)
                except: pass
                current_step += 1
                progress_bar.progress(current_step / total_steps)
                time.sleep(1) 
        
        status_text.success("✅ Selesai mengambil data tren!")

        if all_data:
            df = pd.DataFrame(all_data)
            
            # Config Kolom
            key_col = "Judul" if multi_month_target == "Produk" else "Nama Toko"
            metric_col = "num_terjual_p" if multi_month_target == "Produk" else "num_terjual"
            omzet_col = "num_omzet_p" if multi_month_target == "Produk" else "num_omzet"
            
            # Helper fields untuk grouping (Static fields)
            group_cols = [key_col, 'Link', 'Cover'] # Tambahkan Cover di grouping
            if multi_month_target == "Produk":
                group_cols.extend(['Toko', 'Kategori', 'Harga Display', 'Waktu Rilis']) # Tambah Waktu Rilis
            else:
                group_cols.extend(['Rating', 'Jml Produk']) 

            st.divider()
            st.header(f"📊 Laporan Tren: {multi_month_target}")
            tab1, tab2, tab3 = st.tabs(["🏆 Juara Umum", "💎 Konsistensi", "📅 Breakdown"])

            # TAB 1: JUARA UMUM
            with tab1:
                st.subheader("🏆 Top Performance")
                df_total = df.groupby(group_cols).agg(
                    num_total=(metric_col, 'sum'),
                    num_omzet=(omzet_col, 'sum'),
                    Frekuensi_Bulan=('Bulan', 'nunique'),
                    List_Bulan=('Bulan', lambda x: ', '.join(sorted(x.unique())))
                ).reset_index()
                
                # Mapping nama kolom agar sesuai render_universal_card
                df_total = df_total.rename(columns={'num_total': 'Total Terjual', 'num_omzet': 'Total Omzet', 'Frekuensi_Bulan': 'Frekuensi Bulan', 'List_Bulan': 'List Bulan'})
                df_total = df_total.sort_values('Total Terjual', ascending=False).reset_index(drop=True)
                
                for idx, row in df_total.head(50).iterrows():
                    render_universal_card(row, "trend", label_metric="Total Terjual", label_omzet="Total Omzet")

            # TAB 2: KONSISTENSI
            with tab2:
                st.subheader("💎 Tingkat Konsistensi")
                freqs = sorted(df_total['Frekuensi Bulan'].unique(), reverse=True)
                for freq in freqs:
                    subset = df_total[df_total['Frekuensi Bulan'] == freq].sort_values('Total Terjual', ascending=False).head(5)
                    with st.expander(f"🗓️ Muncul di {freq} Bulan ({len(subset)} Item)", expanded=(freq==freqs[0])):
                        for idx, row in subset.iterrows():
                            render_universal_card(row, "trend", label_metric="Total Terjual", label_omzet="Total Omzet")

            # TAB 3: BREAKDOWN
            with tab3:
                st.subheader("📅 Kilas Balik Per Bulan")
                for bulan in sorted(selected_months):
                    df_bulan = df[df['Bulan'] == bulan].sort_values(metric_col, ascending=False).head(5)
                    if not df_bulan.empty:
                        st.markdown(f"### 🗓️ {bulan}")
                        for idx, row in df_bulan.iterrows():
                            # Mapping manual untuk breakdown karena nama kolom di df asli pakai 'num_terjual_p'
                            # Kita buat alias sementara agar masuk ke fungsi render
                            row_mod = row.copy()
                            row_mod['Terjual Bulan Ini'] = row[metric_col]
                            row_mod['Omzet Bulan Ini'] = row[omzet_col]
                            render_universal_card(row_mod, "trend", label_metric="Terjual Bulan Ini", label_omzet="Omzet Bulan Ini")
                        st.divider()

            st.divider()
            csv_tren = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Data Lengkap (CSV)", csv_tren, "laporan_tren.csv", "text/csv")
        else:
            st.warning("Data tidak ditemukan.")

    # ========================================================
    # MODE 2 & 3: TERLARIS & KEYWORD (TAMPILAN KARTU JUGA)
    # ========================================================
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(1, max_pages + 1):
            status_text.text(f"Mengambil halaman {i} dari {max_pages}...")
            
            if mode == "📦 Produk Terlaris":
                raw = scraper.get_best_products(page=i, time_config=time_config, category_config=cat_config)
                if raw: all_data.extend(scraper.parse_best_products(raw))
            
            elif mode == "🏪 Toko Terlaris":
                raw = scraper.get_best_shops(page=i, time_config=time_config, category_config=cat_config)
                if raw: all_data.extend(scraper.parse_shops(raw))
            
            elif mode == "🔍 Cari Produk (Keyword)":
                raw = scraper.search_products(keyword=keyword, page=i, category_config=cat_config)
                if raw: all_data.extend(scraper.parse_search_results(raw))
            
            progress_bar.progress(i / max_pages)
            time.sleep(1)
        
        status_text.success("Selesai!")
        
        if all_data:
            df = pd.DataFrame(all_data)
            
            st.divider()
            if mode == "🔍 Cari Produk (Keyword)":
                st.subheader(f"🔎 Hasil Pencarian: '{keyword}'")
            elif mode == "📦 Produk Terlaris":
                st.subheader(f"📦 Produk Terlaris: {time_option}")
            else:
                st.subheader(f"🏪 Toko Terlaris: {time_option}")
            
            # --- RENDER KARTU UNTUK SEMUA MODE ---
            for idx, row in df.iterrows():
                # Tentukan label metric berdasarkan mode
                if mode == "🏪 Toko Terlaris":
                    l_metric = "Penjualan"
                    l_omzet = "Omzet"
                    # Di parse_shops kita pakai num_terjual dan num_omzet
                    # Kita mapping manual ke key yang diharapkan fungsi render jika perlu,
                    # tapi render_universal_card sudah punya fallback logic.
                    # Kita oper row apa adanya.
                    render_universal_card(row, "single", label_metric="num_terjual", label_omzet="num_omzet")
                else:
                    # Produk Terlaris / Keyword
                    # Di parse_best_products kita pakai num_terjual_p (periode)
                    # Untuk display kartu single, kita ingin tampilkan metric periode tersebut
                    render_universal_card(row, "single", label_metric="num_terjual_p", label_omzet="num_omzet_p")
            
            st.divider()
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Download Data Lengkap (CSV)", data=csv, file_name=f"data_fastmoss.csv", mime="text/csv")
        
        else:
            st.warning("Data tidak ditemukan.")
