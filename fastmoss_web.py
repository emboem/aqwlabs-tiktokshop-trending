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

def create_mini_chart(dates, counts):
    """Membuat grafik sparkline interaktif dengan tanggal (Fixed)"""
    if not dates or not counts:
        return None
        
    # Menggunakan Graph Objects agar lebih fleksibel dan bebas error
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates, 
        y=counts,
        fill='tozeroy', # Isi area di bawah garis sampai ke nol
        mode='lines+markers', # Tampilkan garis dan titik
        line=dict(color='#ff6b18', width=2), # Garis oranye
        fillcolor='rgba(255, 107, 24, 0.2)', # Warna isi oranye transparan
        marker=dict(size=4, color='#ff6b18'),
        hovertemplate='<b>%{x}</b><br>Terjual: %{y}<extra></extra>' # Tooltip
    ))
    
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=10, b=0), # Margin tipis
        height=120, # Tinggi grafik
        xaxis=dict(
            showgrid=False, 
            visible=True, 
            type='category' # Pakai mode kategori agar tanggal terurut rapi
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='#f0f0f0', 
            visible=True,
            showticklabels=True
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

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

def format_rupiah_str(value):
    """Helper untuk format string Rp di chart Plotly"""
    return f"Rp{value:,.0f}".replace(",", ".")

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

    # --- PARSERS ---
    def parse_best_products(self, products_list):
        parsed_data = []
        for item in products_list:
            shop_info = item.get("shop_info", {})
            shop_name = shop_info.get("name", "-") if isinstance(shop_info, dict) else "-"
            cat_string = " > ".join(item.get("all_category_name", []) or [])
            price_raw = item.get('real_price', 0)
            growth_raw = item.get('sold_count_inc_rate', 0)
            created_time = item.get('ctime', None)
            
            parsed_data.append({
                "Judul": item.get("title"),
                "Harga Display": price_raw, 
                "Kategori": cat_string,
                "Toko": shop_name,
                "Tanggal dibuat": datetime.fromtimestamp(created_time).strftime("%Y-%m-%d") if created_time else "-",
                "Terjual (Periode)": item.get("sold_count_show"),
                "Omzet (Periode)": item.get("sale_amount_show"),
                "Terjual (Total)": item.get("total_sold_count_show"),
                "Omzet (Total)": item.get("total_sale_amount_show"),
                "Link": item.get("detail_url"),
                "Growth Rate": f"{clean_currency_to_float(growth_raw) * 100:.1f}%",
                "num_terjual_p": clean_currency_to_float(item.get("sold_count", 0)),
                "num_omzet_p": clean_currency_to_float(item.get("sale_amount", 0)),
                "num_terjual_t": clean_currency_to_float(item.get("total_sold_count", 0)),
                "num_omzet_t": clean_currency_to_float(item.get("total_sale_amount", 0)),
                "num_growth": clean_currency_to_float(growth_raw) * 100,
                "num_harga": clean_currency_to_float(price_raw)
            })
        return parsed_data

    def parse_shops(self, shops_list):
        parsed_data = []
        for item in shops_list:
            shop_id = item.get("id") or item.get("seller_id")
            link_url = f"https://www.fastmoss.com/id/shop-detail/{shop_id}" if shop_id else "#"
            growth_sold = clean_currency_to_float(item.get('sold_count_inc_rate', 0))
            parsed_data.append({
                "Nama Toko": item.get("name"),
                "Rating": item.get("rating"),
                "Jml Produk": item.get("product_count"),
                "Terjual (Periode)": item.get("inc_sold_count_show"),
                "Omzet (Periode)": item.get("inc_sale_amount_show"),
                "Growth": f"{growth_sold * 100:.1f}%",
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
            cat_string_sub = " > ".join(item.get("category_name_l2", []) or [])
            cat_string_sub_second = " > ".join(item.get("category_name_l3", []) or [])
            clean_title = remove_html_tags(item.get("title"))
            price_raw = item.get('price', "0")
            
            # --- AMBIL DATA TREN LENGKAP (TANGGAL + NILAI) ---
            trend_list = item.get("trend", [])
            trend_dates = [t.get("dt") for t in trend_list] # Ambil Tanggal
            trend_counts = [t.get("inc_sold_count", 0) for t in trend_list] # Ambil Nilai
            
            parsed_data.append({
                "Judul": clean_title,
                "Harga Display": price_raw,
                "Kategori": cat_string,
                "Kategori L2": cat_string_sub,
                "Kategori L3": cat_string_sub_second,
                "Toko": shop_name,
                "Terjual (7 Hari)": item.get("day7_sold_count_show", "0"),
                "Omzet (7 Hari)": item.get("day7_sale_amount_show", "0"),
                "Terjual (Total)": item.get("sold_count_show"),
                "Omzet (Total)": item.get("sale_amount_show"),
                "Link": item.get("detail_url"),
                
                # Simpan data tren mentah untuk dibuatkan chart nanti
                "trend_dates": trend_dates,
                "trend_counts": trend_counts,
                
                "num_terjual_p": item.get("day7_sold_count", 0), 
                "num_omzet_p": item.get("day7_sale_amount", 0),
                "num_terjual_t": item.get("sold_count", 0),
                "num_omzet_t": item.get("sale_amount", 0),
                "num_harga": clean_currency_to_float(price_raw)
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
        "📈 Analisis Tren (Multi-Bulan)" # <--- Menu Baru
        ])
    st.divider()

    time_config = {"type": "1", "value": ""}
    keyword = ""
    multi_month_target = "Produk" # Default
    selected_months = []

    # === LOGIKA UI BARU ===
    if mode == "📈 Analisis Tren (Multi-Bulan)":
        st.subheader("1. Konfigurasi Tren")
        multi_month_target = st.selectbox("Analisis Apa?", ["Produk", "Toko"])
        
        col_y, col_r = st.columns(2)
        with col_y:
            year_val = st.number_input("Tahun", min_value=2023, max_value=2030, value=datetime.now().year)
        with col_r:
            range_opt = st.selectbox("Rentang", [
                "Full Year (12 Bulan)", 
                "Semester 1 (Jan - Jun)", "Semester 2 (Jul - Des)",
                "Q1 (Jan - Mar)", "Q2 (Apr - Jun)", "Q3 (Jul - Sep)", "Q4 (Okt - Des)"
            ])
        
        # Generate list bulan untuk diproses nanti
        selected_months = get_month_list(year_val, range_opt)
        st.caption(f"Akan memproses: {len(selected_months)} bulan ({selected_months[0]} s/d {selected_months[-1]})")

    elif mode == "🔍 Cari Produk (Keyword)":
        st.subheader("1. Kata Kunci")
        keyword = st.text_input("Masukkan Nama Produk", placeholder="Contoh: Buku Anak...")
    
    else: # Mode Terlaris Biasa (Harian/Mingguan/Bulanan)
        st.subheader("1. Filter Waktu")
        time_option = st.selectbox("Pilih Periode", ["Harian", "Mingguan", "Bulanan"])
        # ... (Logika date picker lama Anda tetap di sini) ...
        # (Copy paste logika if time_option == "Harian" dst dari kode lama Anda ke sini)
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

# --- HELPER CHART ---
def plot_orange_bar(df, x_col, y_col, title, format_text='.2s'):
    ORANGE_COLOR = '#ff6b18' 
    chart_data = df.sort_values(by=x_col, ascending=True).tail(15)
    fig = px.bar(chart_data, x=x_col, y=y_col, orientation='h', title=title, text_auto=format_text, color_discrete_sequence=[ORANGE_COLOR])
    fig.update_layout(yaxis={'categoryorder':'total ascending', 'title': ''}, xaxis={'title': ''}, showlegend=False, height=500)
    fig.update_traces(textposition='outside') 
    return fig

# --- LOGIKA UTAMA ---
if start_btn:
    scraper = FastMossScraper()
    cat_config = {"l1": l1_val, "l2": l2_val, "l3": l3_val}
    all_data = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # === BARU: LOGIKA MULTI BULAN (TAMPILAN KARTU/CATALOG STYLE) ===
    # === BARU: LOGIKA MULTI BULAN (TAMPILAN KARTU - FONT DIKECILKAN & NO NUMBERING) ===
    # === BARU: LOGIKA MULTI BULAN (DENGAN DETAIL LIST BULAN) ===
    if mode == "📈 Analisis Tren (Multi-Bulan)":
        # progress_bar = st.progress(0)
        # status_text = st.empty()
        
        total_steps = len(selected_months) * max_pages
        current_step = 0

        # --- PROSES SCRAPING ---
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
                    
                    for p in parsed:
                        p['Bulan'] = month_str 
                    
                    all_data.extend(parsed)
                except Exception as e:
                    pass

                current_step += 1
                progress_bar.progress(current_step / total_steps)
                time.sleep(1) 
        
        status_text.success("✅ Selesai mengambil data tren!")

        if all_data:
            df = pd.DataFrame(all_data)
            
            # --- KONFIGURASI KOLOM DATA ---
            key_col = "Judul" if multi_month_target == "Produk" else "Nama Toko"
            metric_col = "num_terjual_p" if multi_month_target == "Produk" else "num_terjual"
            omzet_col = "num_omzet_p" if multi_month_target == "Produk" else "num_omzet"
            
            # --- FUNGSI HELPER UNTUK MEMBUAT KARTU ---
            def render_card(row, label_metric="Total Terjual", label_omzet="Total Omzet"):
                with st.container(border=True):
                    c_info, c_stats = st.columns([1.5, 2])
                    
                    # Kolom Kiri: Info Produk/Toko
                    with c_info:
                        # Judul kecil (H5) tanpa numbering
                        st.markdown(f"##### {row[key_col]}")
                        
                        if multi_month_target == "Produk":
                            st.caption(f"Upload {row.get('Tanggal dibuat', '-')}")
                            st.caption(f"🏪 Toko: **{row.get('Toko', '-')}**")
                            st.caption(f"📂 Kategori: {row.get('Kategori', '-')}")
                            st.markdown(f"🏷️ **{row.get('Harga Display', 'Rp0')}**")
                        else:
                            st.caption(f"⭐ Rating: {row.get('Rating', '-')}")
                            st.caption(f"📦 Jml Produk: {row.get('Jml Produk', '-')}")
                        
                        st.link_button("🔗 Lihat di FastMoss", row['Link'])

                    # Kolom Kanan: Statistik
                    with c_stats:
                        st.markdown("##### 📊 Performa")
                        sc1, sc2 = st.columns(2)
                        with sc1:
                            st.metric(label=label_metric, value=f"{row[metric_col]:,.0f}")
                        with sc2:
                            omzet_val = row[omzet_col]
                            omzet_str = f"Rp{omzet_val:,.0f}".replace(",", ".")
                            st.metric(label=label_omzet, value=omzet_str)
                        
                        # --- MODIFIKASI: DETAIL BULAN ---
                        if 'Frekuensi Bulan' in row:
                            st.info(f"📅 Konsistensi: Muncul di **{row['Frekuensi Bulan']} bulan** berbeda")
                            
                            # Tampilkan detail bulan jika kolom 'List Bulan' tersedia
                            if 'List Bulan' in row and row['List Bulan']:
                                st.caption(f"🗓️ *Produk ini secara konsisten muncul di bulan: {row['List Bulan']}*")

            # --- TAMPILAN DASHBOARD ---
            st.divider()
            st.header(f"📊 Laporan Tren: {multi_month_target}")
            st.caption(f"Periode: {selected_months[0]} s/d {selected_months[-1]}")

            tab1, tab2, tab3 = st.tabs(["🏆 Juara Umum (Total)", "💎 Paling Konsisten", "📅 Breakdown Bulanan"])

            # === TAB 1: JUARA UMUM (TOTAL) ===
            with tab1:
                st.subheader("🏆 Top Performance (Akumulasi Total)")
                st.markdown("Daftar diurutkan berdasarkan **total penjualan** selama periode yang dipilih.")
                
                # Group Cols
                group_cols = [key_col, 'Link']
                if multi_month_target == "Produk":
                    group_cols.extend(['Toko', 'Kategori', 'Harga Display'])
                else:
                    group_cols.extend(['Rating', 'Jml Produk']) 

                # --- AGREGASI PANDAS (MODIFIKASI UTAMA) ---
                # Menggunakan Named Aggregation untuk mendapatkan List Bulan sekaligus
                df_total = df.groupby(group_cols).agg(
                    Total_Jual=(metric_col, 'sum'),
                    Total_Omzet=(omzet_col, 'sum'),
                    Frekuensi_Bulan=('Bulan', 'nunique'),
                    List_Bulan=('Bulan', lambda x: ', '.join(sorted(x.unique()))) # Menggabungkan nama bulan jadi string
                ).reset_index()

                # Rename kolom agar sesuai dengan variabel yang dipakai render_card
                df_total = df_total.rename(columns={
                    'Total_Jual': metric_col,
                    'Total_Omzet': omzet_col,
                    'Frekuensi_Bulan': 'Frekuensi Bulan',
                    'List_Bulan': 'List Bulan'
                })
                
                df_total = df_total.sort_values(metric_col, ascending=False).reset_index(drop=True)
                
                # Render Kartu
                for idx, row in df_total.head(50).iterrows():
                    render_card(row, label_metric="Total Terjual (Akumulasi)", label_omzet="Total Omzet (Akumulasi)")
                    
                if len(df_total) > 50:
                    st.caption("⚠️ Menampilkan 50 data teratas. Download CSV untuk data lengkap.")

            # === TAB 2: PALING KONSISTEN ===
            with tab2:
                st.subheader("💎 Tingkat Konsistensi")
                st.markdown("Produk/Toko dikelompokkan berdasarkan **seberapa sering** mereka muncul di Top Rank setiap bulannya.")
                
                # df_total sudah memiliki kolom 'List Bulan' dari proses di atas
                freqs = sorted(df_total['Frekuensi Bulan'].unique(), reverse=True)
                
                for freq in freqs:
                    subset = df_total[df_total['Frekuensi Bulan'] == freq]
                    subset = subset.sort_values(metric_col, ascending=False).head(5)
                    
                    with st.expander(f"🗓️ Muncul di {freq} Bulan ({len(subset)} Item Teratas)", expanded=(freq == freqs[0])):
                        for idx, row in subset.iterrows():
                            render_card(row, label_metric="Total Terjual", label_omzet="Total Omzet")

            # === TAB 3: BREAKDOWN BULANAN ===
            with tab3:
                st.subheader("📅 Kilas Balik Per Bulan")
                st.markdown("Produk/Toko dengan penjualan tertinggi di setiap bulannya.")
                
                for bulan in sorted(selected_months):
                    df_bulan = df[df['Bulan'] == bulan].sort_values(metric_col, ascending=False).head(5)
                    
                    if not df_bulan.empty:
                        st.markdown(f"### 🗓️ Bulan: {bulan}")
                        for idx, row in df_bulan.iterrows():
                            # Tidak menampilkan List Bulan di sini karena ini view per bulan (redundant)
                            render_card(row, label_metric="Terjual (Bulan Ini)", label_omzet="Omzet (Bulan Ini)")
                        st.divider()
                    else:
                        st.caption(f"Tidak ada data untuk bulan {bulan}")

            # DOWNLOAD DATA
            st.divider()
            csv_tren = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Data Lengkap (CSV)", csv_tren, "laporan_tren_katalog.csv", "text/csv")
        
        else:
            st.warning("Data tidak ditemukan.")

    # === LOGIKA LAMA (SINGLE MODE) ===
    else:
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
        status_text.text("Selesai!")
    
        if all_data:
            df = pd.DataFrame(all_data)
            
            # === TAMPILAN KHUSUS: PENCARIAN PRODUK (RICH LIST VIEW) ===
            if mode == "🔍 Cari Produk (Keyword)":
                st.divider()
                st.subheader(f"🔎 Hasil Pencarian: '{keyword}'")
                
                # Loop data untuk membuat Tampilan Kartu
                for idx, row in df.iterrows():
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([2, 1.5, 2]) # Pembagian Kolom
                        
                        # Kolom 1: Info Produk
                        with c1:
                            st.markdown(f"**{row['Judul']}**")
                            st.caption(f"Toko: {row['Toko']}")
                            st.caption(f"Kategori: {row['Kategori']}" 
                                    f"{' > ' + row['Kategori L2'] if row.get('Kategori L2') else ''}"
                                    f"{' > ' + row['Kategori L3'] if row.get('Kategori L3') else ''}")
                            st.link_button("🔗 Buka Link Produk", row['Link'])
                        
                        # Kolom 2: Metrik Angka
                        with c2:
                            st.markdown(f"💰 **Harga:** {row['Harga Display']}")
                            st.markdown(f"📦 **Terjual (7 Hari):** {row['Terjual (7 Hari)']}")
                            st.markdown(f"📦 **Terjual (Total):** {row['Terjual (Total)']}")
                            st.markdown(f"💵 **Omzet (7 Hari):** {row['Omzet (7 Hari)']}")
                            st.markdown(f"💵 **Omzet (Total):** {row['Omzet (Total)']}")
                        
                        # Kolom 3: Grafik Tren (Sparkline dengan Tanggal)
                        with c3:
                            # Membuat grafik mini jika data tersedia
                            if row.get('trend_dates') and row.get('trend_counts'):
                                fig_spark = create_mini_chart(row['trend_dates'], row['trend_counts'])
                                st.plotly_chart(fig_spark, use_container_width=True, config={'displayModeBar': False})
                            else:
                                st.caption("Data tren tidak tersedia")

                # Tombol Download (Tetap ada)
                csv = df.to_csv(index=False).encode('utf-8')
                name_file = keyword.replace(" ", "_")
                st.download_button(label="📥 Download Data Lengkap (CSV)", data=csv, file_name=f"search_{name_file}.csv", mime="text/csv")

            # === TAMPILAN LAMA: PRODUK TERLARIS & TOKO (TABEL BIASA) ===
            elif mode != "🔍 Cari Produk (Keyword)":
                # (Kode lama yang kamu suka tetap dipertahankan di sini)
                if mode == "📦 Produk Terlaris":
                    df['Nama Pendek'] = [f"Produk ke-{i+1}" for i in range(len(df))]
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Total Produk", len(df))
                    c2.metric("Total Toko", df['Toko'].nunique())
                    c3.metric("Avg Harga", f"Rp {df['num_harga'].mean():,.0f}")
                    c4.metric("Top Omzet", f"Rp {df['num_omzet_p'].max():,.0f}")
                    st.divider()
                    st.subheader("📊 Analisis Produk")
                    t1, t2, t3 = st.tabs([f"📅 Periode Ini", "♾️ Seumur Hidup", "💰 Harga"])
                    with t1:
                        col_a, col_b = st.columns(2)
                        with col_a: st.plotly_chart(plot_orange_bar(df, "num_terjual_p", "Nama Pendek", f"Terjual"), use_container_width=True)
                        with col_b: st.plotly_chart(plot_orange_bar(df, "num_omzet_p", "Nama Pendek", f"Omzet"), use_container_width=True)
                    with t2:
                        col_c, col_d = st.columns(2)
                        with col_c: st.plotly_chart(plot_orange_bar(df, "num_terjual_t", "Nama Pendek", "Terjual (Total)"), use_container_width=True)
                        with col_d: st.plotly_chart(plot_orange_bar(df, "num_omzet_t", "Nama Pendek", "Omzet (Total)"), use_container_width=True)
                    with t3: st.plotly_chart(plot_orange_bar(df, "num_harga", "Nama Pendek", "Harga (Rp)"), use_container_width=True)
                    st.divider()
                    st.subheader("📋 Data Produk Lengkap")
                    cols_drop = [c for c in df.columns if c.startswith('num_')]
                    display_df = df.drop(columns=cols_drop)
                    st.dataframe(display_df, column_config={"Link": st.column_config.LinkColumn("Link Produk", display_text="🔗 Buka Link")}, use_container_width=True)

                else: # Toko
                    df['Nama Pendek'] = [f"Toko ke-{i+1}" for i in range(len(df))]
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Total Toko", len(df))
                    c2.metric("Avg Rating", f"{df['num_rating'].mean():.1f} ⭐")
                    c3.metric("Total Produk", f"{df['num_produk'].sum():,.0f}")
                    c4.metric("Top Omzet", f"Rp {df['num_omzet'].max():,.0f}")
                    st.divider()
                    st.subheader("📊 Analisis Toko")
                    t1, t2 = st.tabs(["💰 Omzet & Penjualan", "📦 Produk & Rating"])
                    with t1:
                        col_a, col_b = st.columns(2)
                        with col_a: st.plotly_chart(plot_orange_bar(df, "num_omzet", "Nama Pendek", "Omzet Toko"), use_container_width=True)
                        with col_b: st.plotly_chart(plot_orange_bar(df, "num_terjual", "Nama Pendek", "Penjualan Toko"), use_container_width=True)
                    with t2:
                        col_c, col_d = st.columns(2)
                        with col_c: st.plotly_chart(plot_orange_bar(df, "num_produk", "Nama Pendek", "Jml Produk"), use_container_width=True)
                        with col_d: st.plotly_chart(plot_orange_bar(df, "num_rating", "Nama Pendek", "Rating", '.1f'), use_container_width=True)
                    st.divider()
                    st.subheader("📋 Data Toko Lengkap")
                    cols_drop = [c for c in df.columns if c.startswith('num_')]
                    display_df = df.drop(columns=cols_drop)
                    st.dataframe(display_df, column_config={"Link": st.column_config.LinkColumn("Detail Toko", display_text="🔗 Cek FastMoss")}, use_container_width=True)

                csv = display_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="📥 Download Excel/CSV", data=csv, file_name=f"fastmoss_{mode.split()[0]}_{date_val}.csv", mime="text/csv")
        else:
            st.warning(f"Tidak ada data ditemukan.")
