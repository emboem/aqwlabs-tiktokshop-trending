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
# 3. KELAS SCRAPER
# ==========================================
class FastMossScraper:
    def __init__(self):
        self.base_url = "https://www.fastmoss.com/api/goods/saleRank"
        self.headers = HEADERS_CONFIG

    def get_best_sellers(self, page=1, pagesize=10, time_config=None, category_config=None):
        params = {
            "page": page,
            "pagesize": pagesize,
            "order": "1,2",
            "region": "ID",
            "_time": int(time.time()),
            "date_type": time_config['type'],
            "date_value": time_config['value']
        }

        if category_config:
            if category_config.get('l1'): params["l1_cid"] = category_config['l1']
            if category_config.get('l2'): params["l2_cid"] = category_config['l2']
            if category_config.get('l3'): params["l3_cid"] = category_config['l3']

        try:
            response = requests.get(self.base_url, headers=self.headers, params=params, timeout=15)
            if response.status_code == 200:
                data_json = response.json()
                if data_json.get("code") == 200:
                    return data_json.get("data", {}).get("rank_list", [])
            return []
        except Exception as e:
            return []

    def parse_products(self, products_list):
        parsed_data = []
        for item in products_list:
            # 1. Amankan Shop Info
            shop_info = item.get("shop_info", {})
            shop_name = shop_info.get("name", "-") if isinstance(shop_info, dict) else "-"

            # 2. Bersihkan Angka Penting
            price_raw = item.get('real_price', 0)
            growth_raw = item.get('sold_count_inc_rate', 0)
            
            price_val = clean_currency_to_float(price_raw)
            growth_val = clean_currency_to_float(growth_raw)

            # Kategori
            cat_list = item.get("all_category_name", [])
            cat_string = " > ".join(cat_list) if cat_list else "-"

            product_data = {
                # --- DATA DISPLAY (TEXT) ---
                "Judul Produk": item.get("title"),
                "Harga Real": price_raw, 
                "Kategori": cat_string,
                "Toko": shop_name,
                "Terjual (Periode Ini)": item.get("sold_count_show"),
                "Omzet (Periode Ini)": item.get("sale_amount_show"),
                "Total Terjual (Seumur Hidup)": item.get("total_sold_count_show"),
                "Total Omzet (Seumur Hidup)": item.get("total_sale_amount_show"),
                "Link": item.get("detail_url"), # URL Asli
                "Growth Rate": f"{growth_val * 100:.1f}%",
                
                # --- DATA NUMERIK (UNTUK CHART) ---
                "num_terjual_periode": clean_currency_to_float(item.get("sold_count", 0)),
                "num_omzet_periode": clean_currency_to_float(item.get("sale_amount", 0)),
                "num_terjual_total": clean_currency_to_float(item.get("total_sold_count", 0)),
                "num_omzet_total": clean_currency_to_float(item.get("total_sale_amount", 0)),
                "num_growth": growth_val * 100,
                "num_harga": price_val
            }
            parsed_data.append(product_data)
        return parsed_data

# ==========================================
# 4. TAMPILAN WEB (STREAMLIT)
# ==========================================

st.set_page_config(page_title="AQWAM LAB TOOLS", layout="wide")
st.title("🕵️ Tiktokshop Trending Product")
st.subheader("Mengambil Data Produk Terlaris di Tiktokshop dari FastMoss")

# --- SIDEBAR: KONFIGURASI ---
with st.sidebar:
    st.header("⚙️ Konfigurasi Filter")

    # Filter Waktu
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

    # Filter Kategori
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

    # Jumlah Halaman
    st.subheader("3. Opsi Scraping")
    max_pages = st.number_input("Jumlah Halaman (max 10)", min_value=1, max_value=10, value=1)
    start_btn = st.button("🚀 Mulai Scraping", type="primary")

# --- FUNGSI PEMBUAT CHART WARNA ORANYE ---
def plot_orange_bar(df, x_col, title, format_text='.2s'):
    ORANGE_COLOR = '#ff6b18' 
    chart_data = df.sort_values(by=x_col, ascending=True).tail(15)
    
    fig = px.bar(
        chart_data,
        x=x_col,
        y="Nama Pendek",
        orientation='h',
        title=title,
        text_auto=format_text,
        hover_data=["Judul Produk", "Toko", "Harga Real"],
        color_discrete_sequence=[ORANGE_COLOR] 
    )
    
    fig.update_layout(
        yaxis={'categoryorder':'total ascending', 'title': ''},
        xaxis={'title': ''},
        showlegend=False,
        height=500
    )
    fig.update_traces(textposition='outside') 
    return fig

# --- MAIN AREA: HASIL ---
if start_btn:
    scraper = FastMossScraper()
    time_config = {"type": date_type, "value": date_val}
    cat_config = {"l1": l1_val, "l2": l2_val, "l3": l3_val}
    
    all_data = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(1, max_pages + 1):
        status_text.text(f"Mengambil halaman {i} dari {max_pages}...")
        raw_data = scraper.get_best_sellers(page=i, time_config=time_config, category_config=cat_config)
        if raw_data:
            clean_data = scraper.parse_products(raw_data)
            all_data.extend(clean_data)
        progress_bar.progress(i / max_pages)
        time.sleep(1)
        
    status_text.text("Selesai!")
    
    if all_data:
        df = pd.DataFrame(all_data)
        df['Nama Pendek'] = [f"Produk ke-{i+1}" for i in range(len(df))]
        
        # 1. Metrik Utama
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Produk", len(df))
        col2.metric("Total Toko", df['Toko'].nunique())
        col3.metric("Avg Harga", f"Rp {df['num_harga'].mean():,.0f}")
        col4.metric("Top Omzet", f"Rp {df['num_omzet_periode'].max():,.0f}")
        
        st.divider()

        # 2. Visualisasi Diagram (Tabs)
        st.subheader("📊 Analisis Data (Top 15 Produk)")
        tab1, tab2, tab3 = st.tabs(["📅 Periode Ini", "♾️ Seumur Hidup", "📈 Growth & Harga"])
        
        with tab1:
            st.markdown("#### Performa Periode Ini")
            col_a, col_b = st.columns(2)
            with col_a:
                st.plotly_chart(plot_orange_bar(df, "num_terjual_periode", "Total Terjual (Periode Ini)"), use_container_width=True)
            with col_b:
                st.plotly_chart(plot_orange_bar(df, "num_omzet_periode", "Omzet (Periode Ini)"), use_container_width=True)
                
        with tab2:
            st.markdown("#### Performa Seumur Hidup (Total)")
            col_c, col_d = st.columns(2)
            with col_c:
                st.plotly_chart(plot_orange_bar(df, "num_terjual_total", "Total Terjual (Seumur Hidup)"), use_container_width=True)
            with col_d:
                st.plotly_chart(plot_orange_bar(df, "num_omzet_total", "Total Omzet (Seumur Hidup)"), use_container_width=True)

        with tab3:
            st.markdown("#### Growth Rate & Harga")
            col_e, col_f = st.columns(2)
            with col_e:
                st.plotly_chart(plot_orange_bar(df, "num_growth", "Growth Rate (%)", format_text='.3s'), use_container_width=True)
            with col_f:
                st.plotly_chart(plot_orange_bar(df, "num_harga", "Harga Real Produk (Rp)"), use_container_width=True)

        st.divider()

        # 3. Data Tabel dengan LINK KLIK
        st.subheader("📋 Data Lengkap")
        cols_to_drop = ["num_terjual_periode", "num_omzet_periode", "num_terjual_total", "num_omzet_total", "num_growth", "num_harga"]
        display_df = df.drop(columns=cols_to_drop)
        cols = ['Nama Pendek'] + [c for c in display_df.columns if c != 'Nama Pendek']
        display_df = display_df[cols]
        
        # --- KONFIGURASI LINK DI SINI ---
        st.dataframe(
            display_df,
            column_config={
                "Link": st.column_config.LinkColumn(
                    "Link Produk",         # Nama Header Kolom
                    help="Klik untuk membuka produk di tab baru",
                    display_text="🔗 Buka Link" # Teks pengganti URL yang panjang
                )
            },
            use_container_width=True
        )
        
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Excel/CSV",
            data=csv,
            file_name=f"fastmoss_{date_val}.csv",
            mime="text/csv",
        )
        
    else:
        st.warning("Tidak ada data ditemukan.")
