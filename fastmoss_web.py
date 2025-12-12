import streamlit as st
import requests
import pandas as pd
import time
import re
from datetime import datetime
import plotly.express as px

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
# 2. HELPER: PEMBERSIH ANGKA
# ==========================================
def clean_currency_to_float(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    str_val = str(value)
    str_val = re.sub(r'[Rp\s%]', '', str_val)
    str_val = str_val.replace('.', '') 
    str_val = str_val.replace(',', '.')
    try:
        return float(str_val)
    except ValueError:
        return 0.0

# ==========================================
# 3. KELAS SCRAPER (PRODUK & TOKO)
# ==========================================
class FastMossScraper:
    def __init__(self):
        self.headers = HEADERS_CONFIG

    # --- FUNGSI API PRODUK ---
    def get_best_products(self, page=1, pagesize=10, time_config=None, category_config=None):
        url = "https://www.fastmoss.com/api/goods/saleRank"
        params = {
            "page": page, "pagesize": pagesize, "order": "1,2", "region": "ID",
            "_time": int(time.time()), "date_type": time_config['type'], "date_value": time_config['value']
        }
        if category_config:
            if category_config.get('l1'): params["l1_cid"] = category_config['l1']
            if category_config.get('l2'): params["l2_cid"] = category_config['l2']
            if category_config.get('l3'): params["l3_cid"] = category_config['l3']

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("rank_list", []) if data.get("code") == 200 else []
            return []
        except: return []

    # --- FUNGSI API TOKO (BARU) ---
    def get_best_shops(self, page=1, pagesize=10, time_config=None, category_config=None):
        url = "https://www.fastmoss.com/api/shop/v3/shopList"
        params = {
            "page": page, "pagesize": pagesize, "order": "1,2", "region": "ID",
            "_time": int(time.time()), "date_type": time_config['type'], "date_value": time_config['value']
        }
        # Parameter kategori toko sama dengan produk
        if category_config:
            if category_config.get('l1'): params["l1_cid"] = category_config['l1']
            if category_config.get('l2'): params["l2_cid"] = category_config['l2']
            if category_config.get('l3'): params["l3_cid"] = category_config['l3']

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("list", []) if data.get("code") == 200 else []
            return []
        except: return []

    # --- PARSER DATA PRODUK ---
    def parse_products(self, products_list):
        parsed_data = []
        for item in products_list:
            shop_info = item.get("shop_info", {})
            shop_name = shop_info.get("name", "-") if isinstance(shop_info, dict) else "-"
            
            price_raw = item.get('real_price', 0)
            growth_raw = item.get('sold_count_inc_rate', 0)
            price_val = clean_currency_to_float(price_raw)
            growth_val = clean_currency_to_float(growth_raw)

            cat_list = item.get("all_category_name", [])
            cat_string = " > ".join(cat_list) if cat_list else "-"

            product_data = {
                "Judul": item.get("title"),
                "Harga Real": price_raw, 
                "Kategori": cat_string,
                "Toko": shop_name,
                "Terjual (Periode)": item.get("sold_count_show"),
                "Omzet (Periode)": item.get("sale_amount_show"),
                "Terjual (Total)": item.get("total_sold_count_show"),
                "Omzet (Total)": item.get("total_sale_amount_show"),
                "Link": item.get("detail_url"),
                "Growth Rate": f"{growth_val * 100:.1f}%",
                
                "num_terjual_periode": clean_currency_to_float(item.get("sold_count", 0)),
                "num_omzet_periode": clean_currency_to_float(item.get("sale_amount", 0)),
                "num_terjual_total": clean_currency_to_float(item.get("total_sold_count", 0)),
                "num_omzet_total": clean_currency_to_float(item.get("total_sale_amount", 0)),
                "num_growth": growth_val * 100,
                "num_harga": price_val
            }
            parsed_data.append(product_data)
        return parsed_data

    # --- PARSER DATA TOKO (BARU) ---
    def parse_shops(self, shops_list):
        parsed_data = []
        for item in shops_list:
            # Mengambil ID Toko untuk Link FastMoss (Karena link TikTok butuh username)
            shop_id = item.get("id") or item.get("seller_id")
            link_url = f"https://www.fastmoss.com/id/shop-detail/{shop_id}" if shop_id else "#"

            growth_sold = clean_currency_to_float(item.get('sold_count_inc_rate', 0))
            
            shop_data = {
                "Nama Toko": item.get("name"),
                "Rating": item.get("rating"),
                "Jml Produk": item.get("product_count"),
                "Terjual (Periode)": item.get("inc_sold_count_show"),
                "Omzet (Periode)": item.get("inc_sale_amount_show"),
                "Growth (Penjualan)": f"{growth_sold * 100:.1f}%",
                "Link": link_url,

                # Numerik untuk Chart
                "num_terjual": clean_currency_to_float(item.get("inc_sold_count", 0)),
                "num_omzet": clean_currency_to_float(item.get("inc_sale_amount", 0)),
                "num_produk": clean_currency_to_float(item.get("product_count", 0)),
                "num_rating": clean_currency_to_float(item.get("rating", 0))
            }
            parsed_data.append(shop_data)
        return parsed_data

# ==========================================
# 4. TAMPILAN WEB (STREAMLIT)
# ==========================================

st.set_page_config(page_title="FastMoss Scraper", layout="wide")
st.title("🕵️ FastMoss Ultimate Scraper")

# --- SIDEBAR: KONFIGURASI ---
with st.sidebar:
    st.header("⚙️ Panel Kontrol")

    # 1. PILIH MODE (BARU)
    mode = st.radio("🎯 Pilih Mode Scraping", ["📦 Produk Terlaris", "🏪 Toko Terlaris"])
    st.divider()

    # 2. Filter Waktu
    st.subheader("1. Filter Waktu")
    time_option = st.selectbox("Pilih Periode", ["Harian", "Mingguan", "Bulanan"])
    date_val = ""
    date_type = "1"
    if time_option == "Harian":
        date_type = "1"
        d = st.date_input("Pilih Tanggal", datetime.now())
        date_val = d.strftime("%Y-%m-%d")
    elif time_option == "Mingguan":
        date_type = "2"
        st.info("Format: YYYY-WW (Contoh: 2025-49)")
        date_val = st.text_input("Masukkan Minggu", value=datetime.now().strftime("%Y-%W"))
    else: 
        date_type = "3"
        st.info("Format: YYYY-MM (Contoh: 2025-11)")
        date_val = st.text_input("Masukkan Bulan", value=datetime.now().strftime("%Y-%m"))

    # 3. Filter Kategori
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
                    if selected_l3_label != "Semua":
                        l3_val = l3_opts[selected_l3_label]['value']

    # 4. Jumlah Halaman
    st.subheader("3. Opsi Scraping")
    max_pages = st.number_input("Jumlah Halaman (max 10)", min_value=1, max_value=10, value=1)
    
    label_tombol = f"🚀 Mulai Scraping {mode.split()[1]}" # Jadi "Scraping Produk" atau "Scraping Toko"
    start_btn = st.button(label_tombol, type="primary")

# --- HELPER CHART ---
def plot_orange_bar(df, x_col, y_col, title, format_text='.2s'):
    ORANGE_COLOR = '#ff6b18' 
    chart_data = df.sort_values(by=x_col, ascending=True).tail(15)
    
    fig = px.bar(
        chart_data, x=x_col, y=y_col, orientation='h', title=title,
        text_auto=format_text, color_discrete_sequence=[ORANGE_COLOR]
    )
    fig.update_layout(
        yaxis={'categoryorder':'total ascending', 'title': ''},
        xaxis={'title': ''}, showlegend=False, height=500
    )
    fig.update_traces(textposition='outside') 
    return fig

# --- LOGIKA EKSEKUSI ---
if start_btn:
    scraper = FastMossScraper()
    time_config = {"type": date_type, "value": date_val}
    cat_config = {"l1": l1_val, "l2": l2_val, "l3": l3_val}
    
    all_data = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(1, max_pages + 1):
        status_text.text(f"Mengambil halaman {i} dari {max_pages}...")
        
        # --- CABANG LOGIKA BERDASARKAN MODE ---
        if mode == "📦 Produk Terlaris":
            raw_data = scraper.get_best_products(page=i, time_config=time_config, category_config=cat_config)
            if raw_data:
                clean_data = scraper.parse_products(raw_data)
                all_data.extend(clean_data)
        else: # Toko Terlaris
            raw_data = scraper.get_best_shops(page=i, time_config=time_config, category_config=cat_config)
            if raw_data:
                clean_data = scraper.parse_shops(raw_data)
                all_data.extend(clean_data)
        
        progress_bar.progress(i / max_pages)
        time.sleep(1)
        
    status_text.text("Selesai!")
    
    if all_data:
        df = pd.DataFrame(all_data)
        
        # --- TAMPILAN MODE: PRODUK ---
        if mode == "📦 Produk Terlaris":
            df['Nama Pendek'] = [f"Produk ke-{i+1}" for i in range(len(df))]
            
            # Metrik
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Produk", len(df))
            c2.metric("Total Toko", df['Toko'].nunique())
            c3.metric("Avg Harga", f"Rp {df['num_harga'].mean():,.0f}")
            c4.metric("Top Omzet", f"Rp {df['num_omzet_periode'].max():,.0f}")
            st.divider()

            # Chart
            st.subheader("📊 Analisis Produk")
            t1, t2, t3 = st.tabs(["📅 Periode Ini", "♾️ Seumur Hidup", "📈 Growth & Harga"])
            with t1:
                col_a, col_b = st.columns(2)
                with col_a: st.plotly_chart(plot_orange_bar(df, "num_terjual_periode", "Nama Pendek", "Terjual (Periode)"), use_container_width=True)
                with col_b: st.plotly_chart(plot_orange_bar(df, "num_omzet_periode", "Nama Pendek", "Omzet (Periode)"), use_container_width=True)
            with t2:
                col_c, col_d = st.columns(2)
                with col_c: st.plotly_chart(plot_orange_bar(df, "num_terjual_total", "Nama Pendek", "Terjual (Total)"), use_container_width=True)
                with col_d: st.plotly_chart(plot_orange_bar(df, "num_omzet_total", "Nama Pendek", "Omzet (Total)"), use_container_width=True)
            with t3:
                col_e, col_f = st.columns(2)
                with col_e: st.plotly_chart(plot_orange_bar(df, "num_growth", "Nama Pendek", "Growth Rate (%)", '.3s'), use_container_width=True)
                with col_f: st.plotly_chart(plot_orange_bar(df, "num_harga", "Nama Pendek", "Harga (Rp)"), use_container_width=True)
            
            # Tabel
            st.divider()
            st.subheader("📋 Data Produk Lengkap")
            cols_drop = [c for c in df.columns if c.startswith('num_')]
            display_df = df.drop(columns=cols_drop)
            display_df = display_df[['Nama Pendek'] + [c for c in display_df.columns if c != 'Nama Pendek']]
            
            st.dataframe(
                display_df,
                column_config={"Link": st.column_config.LinkColumn("Link Produk", display_text="🔗 Buka Link")},
                use_container_width=True
            )

        # --- TAMPILAN MODE: TOKO ---
        else:
            df['Nama Pendek'] = [f"Toko ke-{i+1}" for i in range(len(df))]
            
            # Metrik
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Toko", len(df))
            c2.metric("Avg Rating", f"{df['num_rating'].mean():.1f} ⭐")
            c3.metric("Total Produk", f"{df['num_produk'].sum():,.0f}")
            c4.metric("Top Omzet", f"Rp {df['num_omzet'].max():,.0f}")
            st.divider()

            # Chart
            st.subheader("📊 Analisis Toko")
            t1, t2 = st.tabs(["💰 Omzet & Penjualan", "📦 Produk & Rating"])
            with t1:
                col_a, col_b = st.columns(2)
                with col_a: st.plotly_chart(plot_orange_bar(df, "num_omzet", "Nama Pendek", "Omzet Toko (Periode Ini)"), use_container_width=True)
                with col_b: st.plotly_chart(plot_orange_bar(df, "num_terjual", "Nama Pendek", "Penjualan Toko (Periode Ini)"), use_container_width=True)
            with t2:
                col_c, col_d = st.columns(2)
                with col_c: st.plotly_chart(plot_orange_bar(df, "num_produk", "Nama Pendek", "Jumlah Produk Aktif"), use_container_width=True)
                with col_d: st.plotly_chart(plot_orange_bar(df, "num_rating", "Nama Pendek", "Rating Toko", '.1f'), use_container_width=True)
            
            # Tabel
            st.divider()
            st.subheader("📋 Data Toko Lengkap")
            cols_drop = [c for c in df.columns if c.startswith('num_')]
            display_df = df.drop(columns=cols_drop)
            display_df = display_df[['Nama Pendek'] + [c for c in display_df.columns if c != 'Nama Pendek']]
            
            st.dataframe(
                display_df,
                column_config={"Link": st.column_config.LinkColumn("Detail Toko", display_text="🔗 Cek FastMoss")},
                use_container_width=True
            )

        # Download Button (Umum)
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Excel/CSV",
            data=csv,
            file_name=f"fastmoss_{mode.split()[1]}_{date_val}.csv",
            mime="text/csv",
        )
        
    else:
        st.warning(f"Tidak ada data {mode} ditemukan. Coba cek filter atau cookie.")
