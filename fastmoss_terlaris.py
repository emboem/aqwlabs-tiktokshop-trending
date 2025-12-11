import requests
import pandas as pd
import time
import json
from datetime import datetime

# ==========================================
# 1. KONFIGURASI HEADERS & COOKIES
# ==========================================
# Diambil dari file fastmoss_terlaris.py (seperti permintaan)
# CATATAN: fm-sign dan cookie memiliki masa berlaku. Jika error, update bagian ini.

HEADERS_CONFIG = {
    "authority": "www.fastmoss.com",
    "accept": "application/json, text/plain, */*",
    "accept-language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "no-cache",
    "lang": "ID_ID",
    "region": "ID",
    "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "source": "pc",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    
    # --- UPDATE BAGIAN INI JIKA EXPIRED ---
    "fm-sign": "16fa6f79d7617ab63b9180aeb907b6bd", 
    "cookie": "NEXT_LOCALE=id; region=ID; utm_country=ID; utm_south=google; utm_id=kw_id_0923_01; utm_lang=id; userTimeZone=Asia%2FJakarta; fp_visid=0c428e01dea23acfe5daff8f5db0e849; _gcl_gs=2.1.k1$i1765341246$u149463969; _gcl_au=1.1.1091888018.1765341251; _ga=GA1.1.86921883.1765341251; gg_client_id=86921883.1765341251; _clck=1vkm0hs%5E2%5Eg1q%5E0%5E2170; _fbp=fb.1.1765341262233.460796550836126988; _tt_enable_cookie=1; _ttp=01KC38KWNN831BY9E87TZ33273_.tt.1; fd_tk=3e275cb3799bba9d7a56995ef346c97a; _rdt_uuid=1765341252879.3992635e-f762-4357-93f5-b07da426c2bd; _gcl_aw=GCL.1765341677.EAIaIQobChMIpa3zzZiykQMV_uwWBR31pyjPEAAYAiAAEgLLvPD_BwE; _ga_GD8ST04HB5=GS2.1.s1765341250$o1$g1$t1765341783$j9$l0$h220945282; _ga_J8P3E5KDGJ=GS2.1.s1765341251$o1$g1$t1765341783$j10$l0$h2714796; _clsk=1cg0sb8%5E1765341785037%5E9%5E0%5Ewww.clarity.ms%2Feus-e%2Fcollect; ttcsid_CJOP1H3C77UDO397C3M0=1765341304178::S84Ydd31UVDP12PgMAa2.1.1765341867468.0; ttcsid=1765341304176::9C1hgvp22b9pqo7ZzUBF.1.1765341867471.0; ttcsid_CJMMQFRC77U1G7J3JGP0=1765341305708::HLRuEW8twVbkUKIJYXKv.1.1765341867471.0; _uetsid=7ff5cb70d58111f0a836a985b4652589|124paud|2|g1q|0|2170; _uetvid=7ff62600d58111f0ac53af3c8f32e7e1|1q6zulx|1765341784970|9|1|bat.bing.com/p/insights/c/l"
}

# ==========================================
# 2. DATABASE KATEGORI (Dari fastmoss_kode_kategori.txt)
# ==========================================
# Struktur data ini disusun agar bisa dipilih secara bertingkat
CATEGORY_TREE = [
    {
        "label": "Perawatan & Kecantikan", "value": "14",
        "children": [
            {"label": "Perawatan Tangan, Kaki & Kuku", "value": "849032", "children": [
                {"label": "Masker Tangan & Kaki", "value": "601454"},
                {"label": "Foot Odour Control", "value": "601456"},
                {"label": "Lotion Tangan, Krim & Scrub", "value": "601480"},
                {"label": "Cuci tangan", "value": "601508"},
                {"label": "Nail Art & Nail Polish", "value": "601591"},
                {"label": "Alat Manicure & Pedicure", "value": "700790"},
                {"label": "Paket Nail Art", "value": "824336"},
                {"label": "Perawatan Kuku", "value": "977672"},
                {"label": "Hand Sanitizer", "value": "1004552"},
                {"label": "Penghilang Cat Kuku/Kuteks", "value": "1004680"},
                {"label": "Nail Art Decoration & Accessories", "value": "852112"}
            ]},
            {"label": "Perawatan Mata & Telinga", "value": "849544", "children": [
                {"label": "Cairan Lensa & Tetes Mata", "value": "601461"},
                {"label": "Lensa Kontak", "value": "601462"},
                {"label": "Peralatan Perawatan Lensa Kontak", "value": "601463"},
                {"label": "Sleep Mask", "value": "601737"},
                {"label": "Kacamata Baca", "value": "874760"},
                {"label": "Obat Tetes Telinga", "value": "874888"},
                {"label": "Produk Penghilang Kotoran Telinga", "value": "875016"},
                {"label": "Penyumbat Telinga", "value": "875144"},
                {"label": "Colored Contact Lens ", "value": "854160"}
            ]},
            {"label": "Perawatan & Penataan Rambut", "value": "848904", "children": [
                {"label": "Sampo & Kondisioner", "value": "601469"},
                {"label": "Mousse & Gel", "value": "601513"},
                {"label": "Pewarna Rambut", "value": "601516"},
                {"label": "Alat Styling Heatless", "value": "700789"},
                {"label": "Produk untuk Rambut Rontok", "value": "806160"},
                {"label": "Perawatan Rambut/Perawatan Kulit Kepala", "value": "981512"},
                {"label": "Bubuk Penata Rambut", "value": "1004168"},
                {"label": "Hair Brushes & Combs", "value": "851984"}
            ]},
            {"label": "Perawatan Kewanitaan", "value": "849800", "children": [
                {"label": "Cairan Vagina", "value": "601475"},
                {"label": "Kebersihan Kewanitaan", "value": "601476"},
                {"label": "Handuk Sanitasi", "value": "601477"},
                {"label": "Krim & Semprotan Menopause", "value": "805648"},
                {"label": "Tampon", "value": "875528"},
                {"label": "Menstrual Cup", "value": "875784"},
                {"label": "Deodoran Area Intim", "value": "1004296"}
            ]},
            {"label": "Keperluan Mandi & Perawatan Tubuh", "value": "849160", "children": [
                {"label": "Peralatan Perawatan Tubuh", "value": "601490"},
                {"label": "Cream & Lotion Tubuh", "value": "601492"},
                {"label": "Sabun & Sabun Mandi", "value": "601493"},
                {"label": "Bedak Talek", "value": "601494"},
                {"label": "Krim Penghilang Rambut, Wax, & Cukur", "value": "601495"},
                {"label": "Deodoran & Antiperspiran", "value": "601498"},
                {"label": "Lulur & Peel Badan", "value": "601506"},
                {"label": "Perawatan Payudara", "value": "601511"},
                {"label": "Krim Pelangsing Tubuh", "value": "601686"},
                {"label": "Alat Pijat Manual", "value": "700785"},
                {"label": "Aksesori Mandi", "value": "853512"},
                {"label": "Masker Tubuh", "value": "873608"},
                {"label": "Minyak Tubuh & Pijat", "value": "873736"},
                {"label": "Sunscreen & Sun Care", "value": "873864"},
                {"label": "Minyak Pencokelat Kulit & Bahan Pencokelat Kulit Mandiri", "value": "978056"},
                {"label": "Perawatan Leher", "value": "1003784"}
            ]},
            {"label": "Perawatan Pria", "value": "849288", "children": [
                {"label": "Keperluan Mandi & Perawatan Tubuh", "value": "601520"},
                {"label": "Makeup", "value": "601565"},
                {"label": "Skincare", "value": "601627"},
                {"label": "Busa Cukur & Aftershave", "value": "601644"},
                {"label": "Perawatan Rambut", "value": "601681"},
                {"label": "Pisau Cukur", "value": "700791"},
                {"label": "Set Alat Cukur", "value": "1004808"},
                {"label": "Aksesori Pencukur Manual", "value": "1004936"}
            ]},
            {"label": "Makeup & Parfum", "value": "848648", "children": [
                {"label": "Set Makeup", "value": "601529"},
                {"label": "Lipstick & Lip Gloss", "value": "601534"},
                {"label": "Alat Makeup", "value": "601537"},
                {"label": "Blemish Balm dan Colour Control", "value": "601550"},
                {"label": "Semprotan Fixer Rias", "value": "601552"},
                {"label": "Concealer & Foundation", "value": "601554"},
                {"label": "Bronzer & Highlighter", "value": "601555"},
                {"label": "Makeup Base dan Primer", "value": "601556"},
                {"label": "Bedak", "value": "601558"},
                {"label": "Blusher", "value": "601560"},
                {"label": "Riasan Tubuh", "value": "601582"},
                {"label": "Parfum", "value": "601583"},
                {"label": "Mascara", "value": "601585"},
                {"label": "Pensil & Gel Alis", "value": "601586"},
                {"label": "Eyeliner & Lipliner", "value": "601587"},
                {"label": "Pulas Mata", "value": "601588"},
                {"label": "Makeup Remover", "value": "601618"},
                {"label": "Tato Temporer", "value": "824592"},
                {"label": "Bulu Mata Palsu & Perekat", "value": "824720"},
                {"label": "Mesin & Paket Tato", "value": "993672"},
                {"label": "Penghilang Tato", "value": "1004424"},
                {"label": "Makeup Mirrors", "value": "852752"},
                {"label": "Makeup Brushes", "value": "852880"},
                {"label": "Makeup Blenders & Sponges", "value": "853008"},
                {"label": "Cotton Swabs", "value": "853136"},
                {"label": "Powder Puffs", "value": "853264"},
                {"label": "Eyelash Curlers", "value": "853392"},
                {"label": "Lash Enhancers & Primers", "value": "853520"}
            ]},
            {"label": "Skincare", "value": "848776", "children": [
                {"label": "Perawatan Bibir", "value": "601595"},
                {"label": "Facial Sunscreen & Sun Care", "value": "601602"},
                {"label": "Toner", "value": "601608"},
                {"label": "Pembersih Wajah", "value": "601609"},
                {"label": "Krim Pijat Wajah", "value": "601610"},
                {"label": "Kit Perawatan Kulit", "value": "601611"},
                {"label": "Face Scrub & Peel", "value": "601613"},
                {"label": "Moisturiser & Mist", "value": "601615"},
                {"label": "Face Mask", "value": "601616"},
                {"label": "Serum & Essence", "value": "601619"},
                {"label": "Perawatan Mata", "value": "601646"},
                {"label": "Perawatan Hidung", "value": "601653"},
                {"label": "Alat Skincare", "value": "601733"},
                {"label": "Perawatan Jerawat", "value": "873480"}
            ]},
            {"label": "Peralatan Perawatan", "value": "849416", "children": [
                {"label": "Perangkat Pijat", "value": "601660"},
                {"label": "Perangkat Kecantikan Tubuh", "value": "601664"},
                {"label": "Alat Pembentuk Alis Elektrik", "value": "601669"},
                {"label": "Perangkat Kecantikan Wajah", "value": "601672"},
                {"label": "Aksesoris", "value": "601677"},
                {"label": "Alat Penghilang Rambut", "value": "824464"},
                {"label": "Kursi Pijat", "value": "848016"},
                {"label": "Alat Cukur Listrik", "value": "873992"},
                {"label": "Sikat Gigi Elektrik", "value": "874120"},
                {"label": "Oral Irrigator", "value": "874248"},
                {"label": "Pengering Rambut", "value": "874376"},
                {"label": "Pengeriting & Pelurus Rambut", "value": "874504"},
                {"label": "Pemangkas & Gunting Rambut", "value": "874632"},
                {"label": "Nose & Ear Hair Trimmers", "value": "854032"}
            ]},
            {"label": "Perawatan Hidung & Mulut", "value": "849672", "children": [
                {"label": "Pemutih Gigi", "value": "601690"},
                {"label": "Kit Perawatan Mulut", "value": "601692"},
                {"label": "Semprotan Mulut", "value": "601693"},
                {"label": "Obat Kumur", "value": "601694"},
                {"label": "Pasta Gigi", "value": "601696"},
                {"label": "Sikat Gigi", "value": "601697"},
                {"label": "Benang Gigi & Tusuk Gigi", "value": "601698"},
                {"label": "Pembersih Lidah", "value": "824208"},
                {"label": "Perawatan Gigi Tiruan", "value": "875272"},
                {"label": "Pembersihan Hidung", "value": "875400"},
                {"label": "Aksesori Ortodontis", "value": "978184"}
            ]},
            {"label": "Perawatan Pribadi Khusus", "value": "981128", "children": [
                {"label": "Koyok", "value": "700662"},
                {"label": "Ice Pack", "value": "856328"},
                {"label": "Popok Dewasa", "value": "981256"},
                {"label": "Antinyamuk", "value": "981384"},
                {"label": "Perlak", "value": "1005064"}
            ]},
            {"label": "Perfume", "value": "856208", "children": [
                {"label": "Men's Perfume", "value": "855696"},
                {"label": "Unisex Perfume", "value": "855824"},
                {"label": "Women's Perfume", "value": "855952"},
                {"label": "Perfume Sets", "value": "856080"}
            ]}
        ]
    },
    {
        "label": "Pakaian & Pakaian Dalam Wanita", "value": "2",
        "children": [
            {"label": "Pakaian Dalam Wanita", "value": "842888", "children": [
                {"label": "Knicker", "value": "601247"},
                {"label": "Shapewear", "value": "601259"},
                {"label": "Bra", "value": "601262"},
                {"label": "Stoking", "value": "844552"},
                {"label": "Pakaian Dalam Termal", "value": "844680"},
                {"label": "Aksesoris Bra", "value": "844936"},
                {"label": "Lingerie", "value": "845192"},
                {"label": "Kaus kaki", "value": "845448"},
                {"label": "Bralette", "value": "845576"},
                {"label": "Set Pakaian Dalam", "value": "845704"}
            ]},
            {"label": "Bawahan Wanita", "value": "842376", "children": [
                {"label": "Rok", "value": "601264"},
                {"label": "Celana Pendek", "value": "601266"},
                {"label": "Legging", "value": "601274"},
                {"label": "Jeans", "value": "601276"},
                {"label": "Celana Panjang", "value": "601277"},
                {"label": "Skirt Pants & Skorts", "value": "854928"}
            ]},
            {"label": "Atasan Wanita", "value": "842248", "children": [
                {"label": "Blus & Kemeja", "value": "601265"},
                {"label": "Jaket & Mantel", "value": "601267"},
                {"label": "Mantel Sepinggang", "value": "601282"},
                {"label": "Pakaian Rajut", "value": "601284"},
                {"label": "Hoodie & Jumper", "value": "601295"},
                {"label": "T-shirt", "value": "601302"},
                {"label": "Rompi, Atasan Tank & Tube", "value": "843400"},
                {"label": "Bodysuit", "value": "843528"},
                {"label": "Kaus Polo", "value": "961032"}
            ]},
            {"label": "Gaun Wanita", "value": "842504", "children": [
                {"label": "Baju Pengantin", "value": "601270"},
                {"label": "Gaun Formal", "value": "601271"},
                {"label": "Gaun Kasual", "value": "601281"},
                {"label": "Gaun Pengiring Pengantin Wanita", "value": "961672"}
            ]},
            {"label": "Setelan & Overall Wanita", "value": "842760", "children": [
                {"label": "Overall", "value": "601280"},
                {"label": "Setelan", "value": "601291"},
                {"label": "Setelan Resmi", "value": "601296"},
                {"label": "Set Pakaian Couple", "value": "844040"},
                {"label": "Set Pakaian Keluarga", "value": "844296"}
            ]},
            {"label": "Baju Tidur dan Baju Santai Wanita", "value": "843016", "children": [
                {"label": "Hansop", "value": "803216"},
                {"label": "Piyama", "value": "845832"},
                {"label": "Kimono Mandi & Rias", "value": "845960"},
                {"label": "Gaun Malam", "value": "846088"}
            ]},
            {"label": "Pakaian Khusus Wanita", "value": "842632", "children": [
                {"label": "Kostum & Aksesoris", "value": "843656"},
                {"label": "Pakaian Kerja & Seragam", "value": "843784"},
                {"label": "Baju Tradisional", "value": "843912"}
            ]}
        ]
    },
    {
        "label": "Kesehatan", "value": "25",
        "children": [
            {"label": "Suplemen Makanan", "value": "700646", "children": [
                {"label": "Manajemen Berat Badan", "value": "700647"},
                {"label": "Suplemen Kecantikan", "value": "700648"},
                {"label": "Suplemen Kebugaran", "value": "700649"},
                {"label": "Suplemen Kesehatan", "value": "700650"}
            ]},
            {"label": "Obat Alternatif &Pengobatan", "value": "950792", "children": [
                {"label": "Pengobatan Alternatif", "value": "805520"},
                {"label": "Jamu", "value": "950920"},
                {"label": "Akupunktur", "value": "951048"},
                {"label": "Minyak Esensial untuk Aromaterapi", "value": "951176"}
            ]},
            {"label": "Suplai Medis", "value": "924424", "children": [
                {"label": "Tidur & Mendengkur", "value": "805776"},
                {"label": "Alat Bantu Pernapasan & Aksesorinya", "value": "805904"},
                {"label": "Berhenti Merokok", "value": "806032"},
                {"label": "Tisu Basah Disinfektan", "value": "824848"},
                {"label": "Alat Tes Kehamilan", "value": "875656"},
                {"label": "Masker Medis", "value": "924680"},
                {"label": "Bathroom Scale", "value": "924808"},
                {"label": "Perlengkapan Pertolongan Pertama", "value": "924936"},
                {"label": "Monitor & Tes Kesehatan", "value": "925064"},
                {"label": "Kursi Roda", "value": "925192"},
                {"label": "Kawat Gigi & Dukungan", "value": "925320"},
                {"label": "Alat Bantu Dengar", "value": "925448"},
                {"label": "Termometer", "value": "926216"},
                {"label": "Masker PPE", "value": "947208"},
                {"label": "Alat Bantu Obat", "value": "950664"},
                {"label": "Peralatan Laboratorium", "value": "1003656"},
                {"label": "Tongkat Jalan", "value": "1003912"},
                {"label": "Electric Stimulators", "value": "1004040"}
            ]},
            {"label": "Obat OTC & Pengobatan", "value": "949384", "children": [
                {"label": "Pereda Nyeri", "value": "949512"},
                {"label": "Batuk &Pilek", "value": "949640"},
                {"label": "Pencernaan &Mual", "value": "949768"},
                {"label": "Eksim, Psoriasis, Perawatan Rosasea", "value": "949896"},
                {"label": "Allergy, Sinus & Asthma", "value": "950024"},
                {"label": "Obat Bayi & Anak", "value": "950152"},
                {"label": "Bekas Luka &Stretchmarks", "value": "950280"},
                {"label": "Antijamur", "value": "950408"},
                {"label": "Luka", "value": "950536"}
            ]},
            {"label": "Kesehatan Seksual", "value": "924552", "children": [
                {"label": "Kondom", "value": "925576"},
                {"label": "Pelumas", "value": "925704"},
                {"label": "Penambah Performa", "value": "925960"}
            ]}
        ]
    },
    {
        "label": "Aksesoris Fashion", "value": "8",
        "children": [
            {"label": "Jam Tangan & Aksesoris", "value": "905480", "children": [
                {"label": "Jam Tangan Pria", "value": "605251"},
                {"label": "Jam Tangan Wanita", "value": "605254"},
                {"label": "Jam Tangan Couple", "value": "605257"},
                {"label": "Aksesoris Jam Tangan", "value": "700795"},
                {"label": "Jam Tangan Unisex", "value": "907144"}
            ]},
            {"label": "Perhiasan & Aksesori Kustom", "value": "905608", "children": [
                {"label": "Anting-Anting", "value": "605268"},
                {"label": "Gelang Kaki", "value": "605272"},
                {"label": "Cincin", "value": "605273"},
                {"label": "Gelang", "value": "605274"},
                {"label": "Kalung", "value": "605280"},
                {"label": "Gantungan & Liontin", "value": "907400"},
                {"label": "Perhiasan Tubuh", "value": "907528"},
                {"label": "Gantungan Kunci", "value": "907656"},
                {"label": "Set Perhiasan", "value": "907784"},
                {"label": "Pengatur Ukuran & Pelindung Perhiasan", "value": "995080"}
            ]},
            {"label": "Aksesoris Rambut", "value": "905864", "children": [
                {"label": "Bando", "value": "605271"},
                {"label": "Ikat Rambut & Scrunchie", "value": "908424"},
                {"label": "Jepit & Pin Rambut", "value": "908552"},
                {"label": "Headpiece & Mahkota", "value": "908936"}
            ]},
            {"label": "Aksesoris Pakaian", "value": "905224", "children": [
                {"label": "Penjepit Kerah & Bros", "value": "605281"},
                {"label": "Set Aksesori Fesyen", "value": "605289"},
                {"label": "Selendang & Syal", "value": "905992"},
                {"label": "Sarung Tangan", "value": "906120"},
                {"label": "Topi", "value": "906248"},
                {"label": "Sabuk", "value": "906376"},
                {"label": "Dasi & Dasi Kupu-Kupu", "value": "906504"},
                {"label": "Saputangan", "value": "906632"},
                {"label": "Masker Wajah & Aksesori", "value": "906760"},
                {"label": "Manset", "value": "906888"},
                {"label": "Alat Penutup Telinga", "value": "960392"}
            ]},
            {"label": "Kacamata", "value": "905352", "children": [
                {"label": "Frame & Kacamata", "value": "605302"},
                {"label": "Kacamata Hitam", "value": "605304"},
                {"label": "Kotak Kacamata & Aksesoris", "value": "907016"}
            ]},
            {"label": "Ekstensi Rambut & Wig", "value": "810128", "children": [
                {"label": "Wig Renda Bagian T Rambut Asli", "value": "811536"},
                {"label": "Wig Renda Penuh Rambut Asli", "value": "811664"},
                {"label": "Wig Renda 360 Rambut Asli", "value": "811792"},
                {"label": "Wig Depan Renda Rambut Asli", "value": "811920"},
                {"label": "Wig Penutup Renda Rambut Asli", "value": "812048"},
                {"label": "Wig Renda Kustom Rambut Asli", "value": "812176"},
                {"label": "Wig Rambut Asli 100% Mesin", "value": "812304"},
                {"label": "Ekstensi & Helai Rambut Asli", "value": "812432"},
                {"label": "Wig Renda Kepang Sintetis", "value": "812560"},
                {"label": "Wig Renda Sintetis 100% Mesin", "value": "812688"},
                {"label": "Wig Deoan Renda Sintetis", "value": "812816"},
                {"label": "Ekstensi & Helai Sintetis", "value": "812944"},
                {"label": "Ekstensi Rambut & Aksesori Wig", "value": "846096"},
                {"label": "Wig Renda Alas Sutra Rambut Asli", "value": "908680"},
                {"label": "Wig Kostum Sintetis", "value": "908808"}
            ]},
            {"label": "Kain", "value": "843144", "children": [
                {"label": "Batik", "value": "846216"},
                {"label": "Renda", "value": "846344"},
                {"label": "Katun", "value": "846472"},
                {"label": "Wool", "value": "846600"},
                {"label": "Beludru, Sutra & Satin", "value": "846728"},
                {"label": "Kulit", "value": "846856"},
                {"label": "Poliester", "value": "846984"},
                {"label": "Denim", "value": "847112"},
                {"label": "Kanvas", "value": "847240"},
                {"label": "Kain Pasang", "value": "847368"},
                {"label": "Songket", "value": "847496"}
            ]}
        ]
    },
    {
        "label": "Olahraga & Outdoor", "value": "9",
        "children": [
            {"label": "Peralatan Olahraga Bola", "value": "834952", "children": [
                {"label": "Sepak Bola", "value": "603041"},
                {"label": "Bulu tangkis", "value": "603065"},
                {"label": "Tenis", "value": "603221"},
                {"label": "Biliar & Snoker", "value": "603331"},
                {"label": "Tenis Meja", "value": "603396"},
                {"label": "Voli", "value": "603437"},
                {"label": "Basket", "value": "603524"},
                {"label": "Golf", "value": "603573"},
                {"label": "Squash", "value": "603641"},
                {"label": "Boling", "value": "603646"},
                {"label": "Bisbol", "value": "603652"},
                {"label": "Ragbi", "value": "837128"},
                {"label": "Sepak Bola", "value": "936328"},
                {"label": "Kriket", "value": "936584"},
                {"label": "Bola Tangan Amerika", "value": "967944"},
                {"label": "Bola Tangan", "value": "968072"},
                {"label": "Futsal", "value": "968200"},
                {"label": "Hoki", "value": "968328"},
                {"label": "Bola Jaring", "value": "968456"},
                {"label": "Polo", "value": "968584"},
                {"label": "Sofbol", "value": "968712"}
            ]},
            {"label": "Pakaian Olahraga & Outdoor", "value": "834568", "children": [
                {"label": "Jersey", "value": "603042"},
                {"label": "Celana Jogger", "value": "603704"},
                {"label": "Tracksuit", "value": "603705"},
                {"label": "Luaran & Hoodie Olahraga", "value": "603706"},
                {"label": "Bra Olahraga", "value": "603729"},
                {"label": "Baju Renang Anak", "value": "804104"},
                {"label": "Jas Hujan untuk Olahraga", "value": "811152"},
                {"label": "Pakaian Dalam Termal Olahraga", "value": "811280"},
                {"label": "Kaos Olahraga", "value": "835720"},
                {"label": "Rompi Olahraga", "value": "835848"},
                {"label": "Celana Pendek Olahraga", "value": "835976"},
                {"label": "Legging Olahraga", "value": "836104"},
                {"label": "Baju Olahraga Anak", "value": "836232"},
                {"label": "Pakaian Tari & Kostum Tari", "value": "963592"},
                {"label": "Rok Olahraga", "value": "963720"},
                {"label": "Gaun Olahraga", "value": "963976"},
                {"label": "Rash guard", "value": "1001224"},
                {"label": "Pakaian Dalam Olahraga", "value": "1001352"}
            ]},
            {"label": "Peralatan Bersantai & Rekreasi Luar Ruangan", "value": "835592", "children": [
                {"label": "Yoga & Pilates", "value": "603084"},
                {"label": "Lintasan & Lapangan", "value": "603247"},
                {"label": "Tinju & Seni Bela Diri", "value": "603288"},
                {"label": "Judo", "value": "603295"},
                {"label": "Gulat", "value": "603301"},
                {"label": "Nunchucks", "value": "603304"},
                {"label": "Taekwondo", "value": "603317"},
                {"label": "Panahan", "value": "603389"},
                {"label": "Berkuda", "value": "603477"},
                {"label": "Skateboard ", "value": "603493"},
                {"label": "Dart", "value": "603605"},
                {"label": "Memancing", "value": "603818"},
                {"label": "Rekreasi Dalam Ruangan", "value": "700740"},
                {"label": "Pagar", "value": "700741"},
                {"label": "Bersepeda ", "value": "838408"},
                {"label": "Sepatu Roda", "value": "939912"},
                {"label": "Balet & Tari", "value": "968840"},
                {"label": "Karate", "value": "968968"},
                {"label": "Mendaki", "value": "969096"},
                {"label": "Airsoft", "value": "969224"},
                {"label": "Cheerleading", "value": "969352"},
                {"label": "Senam", "value": "969480"},
                {"label": "Aerobik", "value": "969608"},
                {"label": "Olahraga Cakram", "value": "969736"},
                {"label": "Paintball", "value": "969864"},
                {"label": "Lari", "value": "969992"},
                {"label": "Terjun Payung", "value": "970120"},
                {"label": "Trilomba", "value": "970248"},
                {"label": "Balapan", "value": "970376"},
                {"label": "E-sports", "value": "970504"},
                {"label": "Berburu", "value": "999944"}
            ]},
            {"label": "Peralatan Olahraga Air", "value": "835080", "children": [
                {"label": "Berselancar ", "value": "603131"},
                {"label": "Menyelam", "value": "700781"},
                {"label": "Renang", "value": "837256"},
                {"label": "Berperahu", "value": "837384"},
                {"label": "Kano", "value": "966792"},
                {"label": "Kayak", "value": "966920"},
                {"label": "Selancar Layang", "value": "967048"},
                {"label": "Dayung", "value": "967176"},
                {"label": "Perahu Layar", "value": "967304"},
                {"label": "Paddle Board Berdiri", "value": "967432"},
                {"label": "Ski Air & Wakeboarding", "value": "967560"},
                {"label": "Polo Air", "value": "967688"},
                {"label": "Selancar Angin", "value": "967816"}
            ]},
            {"label": "Sepatu Olahraga", "value": "834696", "children": [
                {"label": "Sepatu Dansa", "value": "603171"},
                {"label": "Sepatu Golf", "value": "603579"},
                {"label": "Sepatu Bisbol", "value": "603744"},
                {"label": "Sepatu Basket", "value": "603748"},
                {"label": "Sepatu Voli", "value": "603750"},
                {"label": "Sepatu Lari", "value": "603751"},
                {"label": "Sepatu Tenis", "value": "603755"},
                {"label": "Sepatu Bulutangkis", "value": "603758"},
                {"label": "Sepatu Bola", "value": "603760"},
                {"label": "Sepatu Hiking", "value": "603856"},
                {"label": "Sepatu air", "value": "811408"},
                {"label": "Sepatu Training & Gym", "value": "836360"},
                {"label": "Sepatu Roda & Sepatu Seluncur Es", "value": "836488"},
                {"label": "Sepatu Olahraga Anak", "value": "836616"},
                {"label": "Sandal Olahraga", "value": "1000584"},
                {"label": "Sepatu Bersepeda", "value": "1000712"},
                {"label": "Sepatu Futsal", "value": "1000840"},
                {"label": "Sepatu Skateboard", "value": "1000968"},
                {"label": "Sepatu Jalan Santai", "value": "1001096"},
                {"label": "Aksesori Sepatu Olahraga", "value": "1001480"}
            ]},
            {"label": "Peralatan Kebugaran", "value": "835336", "children": [
                {"label": "Hula Hoop", "value": "603353"},
                {"label": "Ab Roller", "value": "603355"},
                {"label": "Gym Ball", "value": "603358"},
                {"label": "Lompat Tali", "value": "603375"},
                {"label": "Peralatan Kebugaran dalam Air", "value": "810256"},
                {"label": "Peralatan Latihan Kelincahan", "value": "810384"},
                {"label": "Latihan Beban", "value": "837640"},
                {"label": "Mesin Kebugaran", "value": "837768"},
                {"label": "Pull Up Bar", "value": "837896"},
                {"label": "Matras olahraga", "value": "843408"},
                {"label": "Band Resistensi", "value": "939784"},
                {"label": "Skuter & Naik", "value": "940040"},
                {"label": "Trampolin", "value": "994312"},
                {"label": "Alat Penguat Otot Tangan", "value": "994440"},
                {"label": "Suspension Trainer", "value": "994568"},
                {"label": "Aksesori Mesin Olahraga", "value": "994696"},
                {"label": "Peralatan Latihan Keseimbangan", "value": "999816"}
            ]},
            {"label": "Aksesoris Olahraga & Outdoor", "value": "834824", "children": [
                {"label": "Alat Pengukur Langkah", "value": "603366"},
                {"label": "Topi Olahraga & Outdoor", "value": "603654"},
                {"label": "Tas Olahraga", "value": "603682"},
                {"label": "Perlengkapan Pelindung", "value": "603872"},
                {"label": "Lengan & Alat Pendukung Olahraga", "value": "810512"},
                {"label": "Perlengkapan Pelatih & Wasit", "value": "810640"},
                {"label": "Trofi, Medali, & Piagam", "value": "810768"},
                {"label": "Kapur Tangan", "value": "810896"},
                {"label": "Kacamata Olahraga", "value": "836744"},
                {"label": "Kaus Kaki Olahraga", "value": "836872"},
                {"label": "Jam Sukat & Pengatur waktu", "value": "837000"},
                {"label": "Botol Air Olahraga", "value": "940168"},
                {"label": "Sarung Tangan Olahraga", "value": "965384"},
                {"label": "Headband Olahraga", "value": "965512"},
                {"label": "Wristband Olahraga", "value": "965640"},
                {"label": "Perekat Olahraga", "value": "965768"},
                {"label": "Kantong Sepatu", "value": "965896"},
                {"label": "Jaket & Rompi Pelampung", "value": "966024"},
                {"label": "Topi Renang", "value": "966152"},
                {"label": "Penutup & Masker Wajah", "value": "1000456"}
            ]},
            {"label": "Peralatan Olahraga Musim Dingin", "value": "835208", "children": [
                {"label": "Hoki Es", "value": "603625"},
                {"label": "Ski", "value": "700779"},
                {"label": "Snowboarding", "value": "837512"},
                {"label": "Seluncur Es", "value": "966280"},
                {"label": "Curling", "value": "966408"},
                {"label": "Kereta Luncur", "value": "966536"},
                {"label": "Sepatu Salju", "value": "966664"}
            ]},
            {"label": "Peralatan Berkemah & Mendaki", "value": "835464", "children": [
                {"label": "Pisau & Perlengkapan Bertahan Hidup", "value": "603835"},
                {"label": "Alat Masak untuk Berkemah", "value": "603917"},
                {"label": "Tempat Tidur Gantung", "value": "603952"},
                {"label": "Pencahayaan Berkemah", "value": "603970"},
                {"label": "Kantong Tidur & Tempat Tidur", "value": "604054"},
                {"label": "Kompas", "value": "604059"},
                {"label": "Teropong & Teleskop", "value": "604065"},
                {"label": "Tenda & Aksesoris", "value": "700782"},
                {"label": "Tongkat Pendakian", "value": "838024"},
                {"label": "Tikar & Keranjang Piknik", "value": "838152"},
                {"label": "Furnitur Berkemah", "value": "838280"},
                {"label": "Filter, Pemurni, & Penyimpanan Air", "value": "1000200"},
                {"label": "alat kebersihan pribadi untuk berkemah", "value": "1000328"}
            ]},
            {"label": "Baju renang, baju selancar, & baju selam", "value": "846224", "children": [
                {"label": "Celana pendek renang", "value": "846352"},
                {"label": "Celana Dalam Pria", "value": "846480"},
                {"label": "Baju Renang Rash Guard", "value": "846608"},
                {"label": "Baju Renang Kompetisi", "value": "846736"},
                {"label": "Bikini", "value": "846864"},
                {"label": "Tankini", "value": "846992"},
                {"label": "Pakaian renang", "value": "847120"},
                {"label": "Pakaian renang One-Piece", "value": "847248"},
                {"label": "Pakaian pantai", "value": "847376"},
                {"label": "Pakaian selam", "value": "811024"}
            ]},
            {"label": "Toko Penggemar", "value": "936712", "children": [
                {"label": "Liga Inggris", "value": "936840"},
                {"label": "Basket", "value": "936968"},
                {"label": "Kriket", "value": "937096"},
                {"label": "Golf", "value": "937224"},
                {"label": "Game", "value": "937352"},
                {"label": "Rugby", "value": "937480"},
                {"label": "Tenis", "value": "937608"}
            ]}
        ]
    },
    {
        "label": "Telepon & Elektronik", "value": "16",
        "children": [
            {"label": "Kamera & Fotografi", "value": "909192", "children": [
                {"label": "Aksesoris Kamera", "value": "601893"},
                {"label": "Kamera Point & Shoo", "value": "910856"},
                {"label": "Kamera Mirrorless", "value": "910984"},
                {"label": "Kamera Action", "value": "911112"},
                {"label": "Perekam Video", "value": "911240"},
                {"label": "Kamera Instan", "value": "911368"},
                {"label": "Kamera Film", "value": "911496"},
                {"label": "DSLR", "value": "911624"},
                {"label": "Kamera & Sistem Keamanan", "value": "911752"},
                {"label": "Lensa Kamera", "value": "911880"},
                {"label": "Drone & Aksesoris", "value": "912008"},
                {"label": "Perawatan Kamera ", "value": "912136"}
            ]},
            {"label": "Aksesori Ponsel", "value": "909064", "children": [
                {"label": "Casing, Pelindung Layar, & Stiker", "value": "601925"},
                {"label": "Baterai Telepon", "value": "601927"},
                {"label": "Tali & Gantungan Telepon", "value": "601936"},
                {"label": "Kabel, Charger & Adaptor", "value": "601937"},
                {"label": "Suku Cadang Ponsel", "value": "909832"},
                {"label": "Aksesoris Selfie", "value": "909960"},
                {"label": "Lensa & Flash Ponsel", "value": "910088"},
                {"label": "Kartu Sim & Aksesoris", "value": "910216"},
                {"label": "Holder & Dudukan Telepon", "value": "910344"},
                {"label": "Perangkat Transmisi", "value": "910472"},
                {"label": "Power Bank", "value": "910728"}
            ]},
            {"label": "Audio & Video", "value": "909320", "children": [
                {"label": "Earphone & Headphone", "value": "601990"},
                {"label": "Speaker", "value": "602029"},
                {"label": "Walkie Talkie", "value": "910600"},
                {"label": "Mikrofon", "value": "912264"},
                {"label": "Proyektor", "value": "912392"},
                {"label": "Sistem Bioskop Rumah", "value": "912520"},
                {"label": "Pemutar MP3 & MP4", "value": "912648"},
                {"label": "Pemutar CD & DVD", "value": "912776"},
                {"label": "Perekam Suara", "value": "912904"},
                {"label": "Radio & Pemutar Kaset", "value": "913032"},
                {"label": "Amplifier & Mixer", "value": "913160"},
                {"label": "AV Receiver", "value": "913288"},
                {"label": "Aksesoris Audio & Video", "value": "913416"}
            ]},
            {"label": "Perangkat Pintar & Dapat Dipakai", "value": "909576", "children": [
                {"label": "Aksesori Cerdas", "value": "602080"},
                {"label": "Jam Tangan Cerdas", "value": "602083"},
                {"label": "Kacamata Pintar", "value": "803728"},
                {"label": "Pelacak Kebugaran", "value": "914056"},
                {"label": "Pelacak GPS", "value": "914184"},
                {"label": "Perangkat VR", "value": "914312"}
            ]},
            {"label": "Ponsel & Tablet", "value": "995976", "children": [
                {"label": "Ponsel", "value": "602097"},
                {"label": "Tablet", "value": "825224"}
            ]},
            {"label": "Aksesori Universal", "value": "978952", "children": [
                {"label": "Penyedot Debu USB", "value": "803856"},
                {"label": "Baterai", "value": "841872"},
                {"label": "Baterai Kancing", "value": "842000"},
                {"label": "Pengisian Daya Baterai Universal", "value": "842128"},
                {"label": "Wi-Fi Saku", "value": "979208"},
                {"label": "Lampu USB & Seluler", "value": "983816"},
                {"label": "Kipas USB & Seluler", "value": "990728"}
            ]},
            {"label": " Game & Konsol ", "value": "909448", "children": [
                {"label": "Konsol Game Rumah", "value": "913544"},
                {"label": "Konsol Game Genggam", "value": "913672"},
                {"label": "Video Game", "value": "913800"},
                {"label": "Aksesoris Konsol", "value": "913928"}
            ]},
            {"label": "Perangkat Edukasi", "value": "909704", "children": [
                {"label": "Pembaca E-book", "value": "914440"},
                {"label": "Kamus Elektronik", "value": "914568"},
                {"label": "Komponen & Aksesori Perangkat Edukasi", "value": "978824"},
                {"label": "Tablet untuk Menulis", "value": "984840"},
                {"label": "Notebook Elektronik", "value": "984968"},
                {"label": "Pena & Perangkat untuk Membaca", "value": "985096"},
                {"label": "Perangkat Pembelajaran Elektronik", "value": "985224"},
                {"label": "Pena Digital & Pena Pintar", "value": "985352"}
            ]},
            {"label": "Aksesori Tablet & Komputer", "value": "984584", "children": [
                {"label": "Cover & Casing Tablet", "value": "991496"},
                {"label": "Pengisi Daya & Adaptor Tablet", "value": "991624"},
                {"label": "Komponen Tablet", "value": "991752"},
                {"label": "Pelindung Layar Tablet", "value": "991880"},
                {"label": "Keyboard Tablet", "value": "992008"},
                {"label": "Dudukan & Alas Tablet", "value": "992136"},
                {"label": "Stilus", "value": "992264"},
                {"label": "Tas & Pembungkus Tablet", "value": "993288"}
            ]}
        ]
    },
    {
        "label": "Perlengkapan Rumah", "value": "10",
        "children": [
            {"label": "Perlengkapan Perayaan & Pesta", "value": "852488", "children": [
                {"label": "Dekorasi Hari Raya", "value": "600009"},
                {"label": "Balon", "value": "600017"},
                {"label": "Semprotan, Confetti, & Streamer", "value": "600019"},
                {"label": "Latar Belakang & Spanduk", "value": "855432"},
                {"label": "Peralatan Makan Sekali Pakai", "value": "855688"},
                {"label": "Topi, Masker, & Aksesori Pesta", "value": "855816"},
                {"label": "Tas & Hadiah Pesta", "value": "855944"},
                {"label": "Dekorasi Kue", "value": "856072"},
                {"label": "Lampion Terbang", "value": "1001736"}
            ]},
            {"label": "Dekorasi Rumah", "value": "852104", "children": [
                {"label": "Patung & Patung Kecil ", "value": "600299"},
                {"label": "Jam Dinding Rumah/Jam Alarm", "value": "600321"},
                {"label": "Stiker Dekoratif", "value": "600338"},
                {"label": "Bingkai Foto", "value": "600341"},
                {"label": "Kait & Rak", "value": "600347"},
                {"label": "Bunga, Tanaman & Buah Dekoratif", "value": "700654"},
                {"label": "Vas & Isian", "value": "700655"},
                {"label": "Potongan Karton Bergambar", "value": "806416"},
                {"label": "Kotak Musik", "value": "806544"},
                {"label": "Permadani", "value": "853896"},
                {"label": "Dekorasi Gantung", "value": "854024"},
                {"label": "Lilin ", "value": "854152"},
                {"label": "Tempat Lilin", "value": "854280"},
                {"label": "Cermin", "value": "854408"},
                {"label": "Magnet Kulkas", "value": "854536"},
                {"label": "Ornamen Fengshui", "value": "854664"},
                {"label": "Dekorasi Keagamaan", "value": "854792"},
                {"label": "Plakat & Papan Petunjuk", "value": "982280"},
                {"label": "Album Foto", "value": "982408"},
                {"label": "Celengan", "value": "984200"},
                {"label": "Kipas Tangan", "value": "984712"},
                {"label": "Poster & Produk Cetak", "value": "1000072"}
            ]},
            {"label": "Perlengkapan Perawatan Rumah", "value": "852232", "children": [
                {"label": "Lap/Kepala Lap", "value": "600378"},
                {"label": "Sarung Tangan Pembersih", "value": "600396"},
                {"label": "Kantong Sampah", "value": "600401"},
                {"label": "Tempat Sampah", "value": "600403"},
                {"label": "Kain Pembersih", "value": "600409"},
                {"label": "Sapu", "value": "600417"},
                {"label": "Karet Pembersih Kaca", "value": "600418"},
                {"label": "Pel", "value": "600423"},
                {"label": "Celemek", "value": "600427"},
                {"label": "Anti Ngengat, Jamur & Lembab", "value": "600458"},
                {"label": "Pengendali Hama & Gulma", "value": "600466"},
                {"label": "Penghilang Formaldehida", "value": "600475"},
                {"label": "Wewangian Rumah ", "value": "600477"},
                {"label": "Pembersih Rumah Tangga", "value": "600812"},
                {"label": "Tisu Toilet & Tisu Basah", "value": "600839"},
                {"label": "Dust Cover", "value": "700665"},
                {"label": "Pelindung Percikan", "value": "817296"},
                {"label": "Ember", "value": "854920"},
                {"label": "Spons & Sabut Gosok", "value": "855048"},
                {"label": "Tisu Dapur & Tisu Basah", "value": "993416"},
                {"label": "Tisu & Serbet & Lap", "value": "993544"},
                {"label": "Penutup Sepatu Sekali Pakai", "value": "994184"}
            ]},
            {"label": "Perlengkapan Kamar Mandi", "value": "851976", "children": [
                {"label": "Sikat & Kop Sedot Toilet", "value": "600405"},
                {"label": "Penutup Kursi Toilet", "value": "600406"},
                {"label": "Dispenser Losion", "value": "600416"},
                {"label": "Tumbler Kamar Mandi", "value": "600430"},
                {"label": "Holder Sikat Gigi", "value": "600436"},
                {"label": "Tirai Mandi & Batangnya", "value": "600439"},
                {"label": "Sabun Cuci Piring", "value": "600447"},
                {"label": "Bak Cuci & Bak Cuci Kaki", "value": "600451"},
                {"label": "Handuk", "value": "810888"},
                {"label": "Gadget Kamar Mandi", "value": "853256"},
                {"label": "Set Kamar Mandi", "value": "853384"},
                {"label": "Keset Kamar Mandi", "value": "853640"},
                {"label": "Shower Cap", "value": "853768"}
            ]},
            {"label": "Perlengkapan Rumah Lainnya", "value": "852616", "children": [
                {"label": "Baju Hujan", "value": "600569"},
                {"label": "Payung", "value": "600570"},
                {"label": "Poncho/Jas Hujan", "value": "600573"},
                {"label": "Sepatu Bot Wellington", "value": "600574"},
                {"label": "Botol Air Panas", "value": "856200"},
                {"label": "Aks. Korek Api Elektrik", "value": "856456"}
            ]},
            {"label": "Home Organizer", "value": "851848", "children": [
                {"label": "Kotak & Tempat Penyimpanan", "value": "600621"},
                {"label": "Keranjang Penyimpanan", "value": "600686"},
                {"label": "Gantungan & Jepitan Baju", "value": "600748"},
                {"label": "Kantong Penyimpanan", "value": "852744"},
                {"label": "Holder & Rak Penyimpanan", "value": "852872"},
                {"label": "Botol & Stoples Penyimpanan", "value": "853000"},
                {"label": "Kait & Rel", "value": "853128"}
            ]},
            {"label": "Alat & Aksesori Laundry", "value": "852360", "children": [
                {"label": "Tas Cuci", "value": "600747"},
                {"label": "Tali Jemuran", "value": "600750"},
                {"label": "Papan Setrika", "value": "600756"},
                {"label": "Rak Pengeringan", "value": "600758"},
                {"label": "Bola & Cakram Laundry", "value": "855176"},
                {"label": "Papan Cuci", "value": "855304"}
            ]}
        ]
    },
    {
        "label": "Makanan & Minuman", "value": "24",
        "children": [
            {"label": "Makanan Ringan", "value": "915336", "children": [
                {"label": "Biskuit, Kue & Wafer", "value": "700553"},
                {"label": "Keripik & Camilan Isi", "value": "700554"},
                {"label": "Cokelat & Camilan Cokelat", "value": "700768"},
                {"label": "Kue Camilan & Roti Pastri", "value": "820368"},
                {"label": "Permen", "value": "921736"},
                {"label": "Biji-bijian", "value": "921864"},
                {"label": "Popcorn", "value": "921992"},
                {"label": "Rumput Laut", "value": "922120"},
                {"label": "Kacang-kacangan", "value": "922248"},
                {"label": "Puding Kustar & Jeli", "value": "922376"},
                {"label": "Makanan Ringan Kering", "value": "922504"},
                {"label": "Mengunyah & Permen Karet", "value": "946952"},
                {"label": "Bar", "value": "947080"},
                {"label": "Set Kado", "value": "963464"},
                {"label": "Plant-based & Gluten Snacks", "value": "851856"}
            ]},
            {"label": "Minuman", "value": "914824", "children": [
                {"label": "Kopi", "value": "700612"},
                {"label": "Makanan Pengganti & Minuman Protein", "value": "819984"},
                {"label": "Pengganti Kopi", "value": "820112"},
                {"label": "Soda & Sparkling Water", "value": "843536"},
                {"label": "Teh", "value": "916488"},
                {"label": "Minuman Cokelat & Malt", "value": "916616"},
                {"label": "Jus & Smoothie", "value": "916744"},
                {"label": "Minuman Bersoda", "value": "916872"},
                {"label": "Air", "value": "917000"},
                {"label": "Minuman Olahraga & Energi", "value": "917256"},
                {"label": "Minuman Non-Alkohol ", "value": "917384"},
                {"label": "Campuran Minuman Bubuk", "value": "917512"},
                {"label": "Topping Minuman", "value": "917640"},
                {"label": "Sirup & Konsentrat", "value": "917768"}
            ]},
            {"label": "Makanan Instan", "value": "914952", "children": [
                {"label": "Mie Instan", "value": "700644"},
                {"label": "Makanan Kalengan, Stoples, & Kemasan", "value": "918280"},
                {"label": "Sayur Acar, Acar & Chutney", "value": "918408"},
                {"label": "Nasi & Bubur Instan", "value": "918536"},
                {"label": "Hotpot Instan", "value": "918664"},
                {"label": "Sereal, Granola & Oat untuk Sarapan", "value": "918792"},
                {"label": "Sarang Burung Walet", "value": "853648"}
            ]},
            {"label": "Makanan Segar & Beku", "value": "915464", "children": [
                {"label": "Pizza & Focaccia", "value": "807312"},
                {"label": "Roti isi & Wrap", "value": "807440"},
                {"label": "Sup & Semur", "value": "807568"},
                {"label": "Pasta & Saus", "value": "807696"},
                {"label": "Deli", "value": "807824"},
                {"label": "Makanan Siap Saji", "value": "807952"},
                {"label": "Daging", "value": "922632"},
                {"label": "Seafood", "value": "922760"},
                {"label": "Alternatif Daging Vegetarian", "value": "922888"},
                {"label": "Roti", "value": "923016"},
                {"label": "Kue & Pai", "value": "923144"},
                {"label": "Kue Kering", "value": "923272"},
                {"label": "Es Krim", "value": "923400"},
                {"label": "Telur", "value": "923528"},
                {"label": "Tahu", "value": "923656"},
                {"label": "Sayuran", "value": "923784"},
                {"label": "Buah", "value": "923912"},
                {"label": "Jamur", "value": "924040"},
                {"label": "Makanan Beku", "value": "924168"},
                {"label": "Daging Olahan & Seafood", "value": "924296"},
                {"label": "Paket Makan", "value": "946824"}
            ]},
            {"label": "Pembuatan Kue", "value": "915208", "children": [
                {"label": "Tepung Roti & Isian Roti", "value": "820240"},
                {"label": "Susu Kental Manis", "value": "820752"},
                {"label": "Penyedap & Ekstrak Makanan", "value": "920584"},
                {"label": "Baking Powder & Soda", "value": "920712"},
                {"label": "Campuran Kue", "value": "920840"},
                {"label": "Tepung Kue", "value": "920968"},
                {"label": "Pewarna Makanan", "value": "921096"},
                {"label": "Frosting, Icing, & Dekorasi", "value": "921224"},
                {"label": "Creamer", "value": "921352"},
                {"label": "Mentega & Margarin", "value": "921480"},
                {"label": "Keju & Keju Bubuk", "value": "921608"},
                {"label": "Krim", "value": "999048"},
                {"label": "Marshmallow", "value": "999176"}
            ]},
            {"label": "Susu & Produk Olahan Susu", "value": "809744", "children": [
                {"label": "Susu UHT", "value": "820496"},
                {"label": "Susu Bubuk", "value": "820624"},
                {"label": "Susu Nabati", "value": "917128"},
                {"label": "Susu Segar", "value": "999304"},
                {"label": "Yoghurt & Produk Fermentasi Susu", "value": "999432"}
            ]},
            {"label": "Beer, Wine & Spirit", "value": "914696", "children": [
                {"label": "Beer", "value": "915592"},
                {"label": "Wine ", "value": "915720"},
                {"label": "Cuka Apel", "value": "915848"},
                {"label": "Minuman Pre-Mixed & Siap Saji", "value": "915976"},
                {"label": "Sake, Soju & Umeshu", "value": "916104"},
                {"label": "Sparkling Wine & Champagne", "value": "916232"},
                {"label": "Spirit", "value": "916360"},
                {"label": "Wine Buah & Wine Musiman", "value": "999560"},
                {"label": "Wine Fortifikasi & Wine Hidangan Penutup", "value": "999688"}
            ]},
            {"label": "Bahan Makanan & Peralatan Memasak Pokok", "value": "915080", "children": [
                {"label": "Beras", "value": "917896"},
                {"label": "Pasta, Mie, & Vermiseli", "value": "918024"},
                {"label": "Kacang-kacangan & Biji-bijian", "value": "918152"},
                {"label": "Minyak", "value": "918920"},
                {"label": "Gula & Pemanis", "value": "919048"},
                {"label": "Bumbu, Rempah & Bumbu", "value": "919176"},
                {"label": "Garam", "value": "919304"},
                {"label": "Saus Masak", "value": "919432"},
                {"label": "Cuka ", "value": "919560"},
                {"label": "Wine untuk Memasak", "value": "919688"},
                {"label": "Stok, Saus & Sup Instan", "value": "919816"},
                {"label": "Kit Pasta & Bumbu Masak", "value": "919944"},
                {"label": "Penambah Rasa", "value": "920072"},
                {"label": "Tepung", "value": "920200"},
                {"label": "Madu & Sirup Maple", "value": "920328"},
                {"label": "Selai, Saus, & Olesan", "value": "920456"},
                {"label": "Makanan yang Dikeringkan", "value": "963336"}
            ]}
        ]
    },
    {
        "label": "Mobil & Sepeda Motor", "value": "23",
        "children": [
            {"label": "Aksesoris Interior Mobil", "value": "930184", "children": [
                {"label": "Dekorasi", "value": "605201"},
                {"label": "Stowing & Tidying", "value": "605213"},
                {"label": "Mount & Holder", "value": "605215"},
                {"label": "Keset Anti Selip", "value": "605219"},
                {"label": "Tikar Mobil", "value": "700684"},
                {"label": "Pewangi Mobil", "value": "842256"},
                {"label": "Alat Keselamatan Darurat", "value": "842384"},
                {"label": "Bantal Leher", "value": "932488"},
                {"label": "Stiker Interior", "value": "932616"},
                {"label": "Rak & Aksesoris Belakang", "value": "932744"},
                {"label": "Moulding Interior", "value": "932872"},
                {"label": "Casing Kunci Mobil", "value": "933000"},
                {"label": "Fastener & Clip", "value": "933128"},
                {"label": "Seat Cushions", "value": "850704"},
                {"label": "Steering Wheel Covers", "value": "850832"},
                {"label": "Steering Locks & Security", "value": "850960"},
                {"label": "Pedals & Gear Sticks", "value": "851088"}
            ]},
            {"label": "Aksesoris Eksterior Mobil", "value": "930056", "children": [
                {"label": "Pelindung Sinar Matahari", "value": "605242"},
                {"label": "Aksesori Antena", "value": "841104"},
                {"label": "Penutup Lumpur & Pelindung Percikan", "value": "841232"},
                {"label": "Tanduk & Aksesori", "value": "841360"},
                {"label": "Trim & Aksesori Krom", "value": "841488"},
                {"label": "Rak", "value": "841616"},
                {"label": "Kit Lipat Cermin Samping", "value": "931464"},
                {"label": "Cover & Shelter Mobil", "value": "931592"},
                {"label": "Stiker Mobil", "value": "931720"},
                {"label": "Warna Jendela", "value": "931848"},
                {"label": "Kaca Film & Perlindungan Matahari", "value": "931976"},
                {"label": "Plat Nomor", "value": "932104"},
                {"label": "Holder Tax Disc Mobil", "value": "932232"},
                {"label": "Strip Reflektif", "value": "932360"},
                {"label": "Decoration", "value": "851216"},
                {"label": "Side Window Deflectors & Visors", "value": "851728"}
            ]},
            {"label": "Suku Cadang Kendaraan", "value": "809488", "children": [
                {"label": "Bodi, Rangka, & Bemper", "value": "813200"},
                {"label": "Wiper & Pencuci Kaca Depan Mobil", "value": "813328"},
                {"label": "Pembuangan & Emisi", "value": "813456"},
                {"label": "Roda, Pelek, & Aksesori", "value": "813584"},
                {"label": "Ban & Aksesori", "value": "813712"},
                {"label": "Sok, Strut, & Suspensi", "value": "813840"},
                {"label": "Radiator, Pendinginan Mesin, & Kontrol Suhu", "value": "813968"},
                {"label": "Drivetrain, Transmisi, & Kopling", "value": "814096"},
                {"label": "Bearing & Seal", "value": "814224"},
                {"label": "Komponen Mesin", "value": "814352"},
                {"label": "Sistem Rem", "value": "814480"},
                {"label": "Sabuk, Selang, & Puli", "value": "814608"},
                {"label": "Sistem Bahan Bakar", "value": "814736"},
                {"label": "Pengapian", "value": "814864"},
                {"label": "Baterai & Aksesori", "value": "814992"}
            ]},
            {"label": "Aksesori Sepeda Motor", "value": "940936", "children": [
                {"label": "Kursi & Sarung Kursi", "value": "815120"},
                {"label": "Gembok & Keamanan", "value": "815248"},
                {"label": "Kotak & Casing", "value": "815376"},
                {"label": "Karpet", "value": "815504"},
                {"label": "Helm", "value": "815632"},
                {"label": "Aksesoris Sepeda Motor", "value": "946184"},
                {"label": "Perlengkapan Pelindung", "value": "946312"},
                {"label": "Penutup & Sarung Sepeda Motor", "value": "1002888"},
                {"label": "Stiker & Lapisan Film Sepeda Motor", "value": "1003400"},
                {"label": "Jackets & Raincoats", "value": "854288"},
                {"label": "Mud Flaps & Splash Guards", "value": "854416"},
                {"label": "Handlebars & Grips", "value": "854544"}
            ]},
            {"label": "Suku Cadang Sepeda Motor", "value": "809616", "children": [
                {"label": "Busi", "value": "815760"},
                {"label": "Pembuangan & Emisi", "value": "815888"},
                {"label": "Lampu", "value": "816016"},
                {"label": "Drivetrain, Transmisi, & Kopling", "value": "816144"},
                {"label": "Sok, Strut, & Suspensi", "value": "816272"},
                {"label": "Ban & Aksesori", "value": "816400"},
                {"label": "Sistem Rem", "value": "816528"},
                {"label": "Baterai & Aksesori", "value": "816656"},
                {"label": "Roda, Pelek, & Aksesori", "value": "816784"},
                {"label": "Kabel & Tabung", "value": "816912"},
                {"label": "Tanduk & Aksesori", "value": "817040"},
                {"label": "Cermin & Aksesori", "value": "817168"},
                {"label": "Filter Sepeda Motor", "value": "945928"},
                {"label": "Frame & Fitting", "value": "946056"},
                {"label": "Oli Sepeda Motor", "value": "1003016"},
                {"label": "Coolant & Pelumas Sepeda Motor", "value": "1003272"}
            ]},
            {"label": "Elektronik Mobil", "value": "929928", "children": [
                {"label": "Kamera Mobil", "value": "842512"},
                {"label": "Sistem Cerdas", "value": "930312"},
                {"label": "CCTV", "value": "930440"},
                {"label": "Sistem & Alarm Keamanan", "value": "930568"},
                {"label": "Aksesoris Elektronik", "value": "930696"},
                {"label": "Pemutar Video untuk Mobil", "value": "930952"},
                {"label": "GPS & Aksesoris", "value": "931080"},
                {"label": "Peralatan Elektrik untuk Mobil", "value": "931208"},
                {"label": "Audio Mobil", "value": "931336"},
                {"label": "FM & Bluetooth Transmitters", "value": "851344"},
                {"label": "USB Chargers", "value": "851472"}
            ]},
            {"label": "Sepeda Motor", "value": "847504", "children": [
                {"label": "Sepeda Motor Manual", "value": "847632"},
                {"label": "Sepeda Motor Matik", "value": "847760"},
                {"label": "Sepeda Motor Listrik", "value": "847888"}
            ]},
            {"label": "Alat Perbaikan Mobil", "value": "940296", "children": [
                {"label": "Pembaca & Pemindai Kode", "value": "941064"},
                {"label": "Alat Diagnostik", "value": "941192"},
                {"label": "Alat Sheet Metal", "value": "941320"},
                {"label": "Alat Perbaikan Aki Mobil", "value": "941448"},
                {"label": "Alat Inspeksi Mobil", "value": "941576"},
                {"label": "Alat Perbaikan Mesin & Transmisi", "value": "941704"},
                {"label": "Alat Perbaikan & Pemasangan Ban", "value": "941832"},
                {"label": "Alat Perakitan & Pembongkaran", "value": "941960"},
                {"label": "Alat Perbaikan Bodi Mobil", "value": "942088"}
            ]},
            {"label": "Lampu Mobil", "value": "940424", "children": [
                {"label": "Lampu Hias", "value": "942216"},
                {"label": "Light Bar & Lampu Kerja", "value": "942344"},
                {"label": "Bohlam Lampu Depan (LED)", "value": "942472"},
                {"label": "Kabel", "value": "942600"},
                {"label": "Cover", "value": "942728"},
                {"label": "Pangkalan", "value": "942856"},
                {"label": "Lampu Indikator", "value": "942984"},
                {"label": "Bohlam Lampu Depan (Xenon)", "value": "943240"},
                {"label": "Bohlam Lampu Depan (Halogen)", "value": "943368"},
                {"label": "Lampu Kabut", "value": "946440"}
            ]},
            {"label": "Quad, Motorhome & Perahu", "value": "940680", "children": [
                {"label": "Suku Cadang & Aksesoris Sepeda Quad", "value": "943496"},
                {"label": "Suku Cadang & Aksesoris Perahu", "value": "943624"},
                {"label": "Suku Cadang & Aksesoris Motor", "value": "943752"},
                {"label": "Suku Cadang Kendaraan Listrik", "value": "943880"},
                {"label": "Suku Cadang Truk", "value": "944008"},
                {"label": "Suku Cadang & Aksesoris Perahu", "value": "944136"},
                {"label": "Transportasi & Penyimpanan", "value": "944264"},
                {"label": "Suku Cadang Mobil Penyelamat", "value": "944392"},
                {"label": "Suku Cadang Snowmobile", "value": "944520"}
            ]},
            {"label": "Pencucian & Perawatan Mobil", "value": "940808", "children": [
                {"label": "Mesin & Aksesoris Pemoles", "value": "944648"},
                {"label": "Cat & Alat Perbaikan Jendela", "value": "944776"},
                {"label": "Perawatan Interior", "value": "944904"},
                {"label": "Aksesoris Cuci Mobil", "value": "945032"},
                {"label": "Water Gun & Snow Foam Lance", "value": "945160"},
                {"label": "Cairan Pembersih & Perawatan", "value": "945288"},
                {"label": "Perbaikan Jendela", "value": "945416"},
                {"label": "Perawatan Cat", "value": "945544"},
                {"label": "Perawatan Mesin", "value": "945672"},
                {"label": "Mesin Cuci Mobil", "value": "945800"},
                {"label": "Oils", "value": "851600"}
            ]}
        ]
    },
    {
        "label": "Pakaian & Pakaian Dalam Pria", "value": "3",
        "children": [
            {"label": "Atasan Pria", "value": "839944", "children": [
                {"label": "Rompi & Gilet", "value": "601194"},
                {"label": "Kemeja", "value": "601195"},
                {"label": "Jaket & Mantel", "value": "601197"},
                {"label": "Hoodie & Jumper", "value": "601213"},
                {"label": "Pakaian Rajut", "value": "601223"},
                {"label": "T-shirt", "value": "601226"},
                {"label": "Rompi", "value": "960648"},
                {"label": "Kaus Polo", "value": "960776"}
            ]},
            {"label": "Bawahan Pria", "value": "840072", "children": [
                {"label": "Celana pendek", "value": "601196"},
                {"label": "Jeans", "value": "601202"},
                {"label": "Celana Panjang", "value": "601218"}
            ]},
            {"label": "Setelan & Overall Pria", "value": "840712", "children": [
                {"label": "Setelan", "value": "601210"},
                {"label": "Setelan Resmi", "value": "601216"},
                {"label": "Overall", "value": "840840"}
            ]},
            {"label": "Baju Tidur dan Baju Santai Pria", "value": "840584", "children": [
                {"label": "Hansop", "value": "803344"},
                {"label": "Piyama", "value": "841864"},
                {"label": "Kimono Mandi & Rias", "value": "841992"},
                {"label": "Piyama Midi", "value": "842120"}
            ]},
            {"label": "Pakaian Khusus Pria", "value": "840328", "children": [
                {"label": "Kostum & Aksesoris", "value": "840968"},
                {"label": "Pakaian Kerja & Seragam", "value": "841096"},
                {"label": "Baju Tradisional", "value": "841224"}
            ]},
            {"label": "Pakaian Dalam Pria", "value": "840456", "children": [
                {"label": "Pakaian Dalam", "value": "841352"},
                {"label": "Rompi", "value": "841480"},
                {"label": "Pakaian Dalam Termal", "value": "841608"},
                {"label": "Kaus kaki", "value": "841736"}
            ]}
        ]
    },
    {
        "label": "Koleksi", "value": "30",
        "children": [
            {"label": "Barang Koleksi Budaya Kontemporer", "value": "809872", "children": [
                {"label": "Porselen Merah", "value": "822800"},
                {"label": "Jianzhan", "value": "822928"},
                {"label": "Gerabah", "value": "823056"},
                {"label": "Kaligrafi Tiongkok", "value": "823184"},
                {"label": "Lukisan Tiongkok", "value": "823312"},
                {"label": "Lukisan Barat", "value": "823440"},
                {"label": "Batu Langka & Ukiran Batu", "value": "823568"},
                {"label": "Sealcutting", "value": "823696"},
                {"label": "Tungku Dupa & Rempah", "value": "823824"}
            ]},
            {"label": "Kartu Koleksi & Aksesori", "value": "810000", "children": [
                {"label": "Kartu Koleksi Nonolahraga", "value": "823952"},
                {"label": "Aksesori Kartu Koleksi", "value": "824080"},
                {"label": "Kartu Koleksi Olahraga", "value": "937864"}
            ]},
            {"label": "Hiburan", "value": "953352", "children": [
                {"label": "Photocard", "value": "843152"},
                {"label": "CD, DVD & Piringan Hitam", "value": "953480"},
                {"label": "Figur Karakter & Patung", "value": "953608"},
                {"label": "Prangko", "value": "953736"},
                {"label": "Mobil Model & Mainan Cetak", "value": "953864"},
                {"label": "Piring", "value": "953992"},
                {"label": "Cetakan & Poster", "value": "954120"}
            ]},
            {"label": "Koleksi Olahraga", "value": "937736", "children": [
                {"label": "Jersey", "value": "937992"},
                {"label": "Foto", "value": "938120"},
                {"label": "Bola", "value": "938248"},
                {"label": "Trofi", "value": "938376"},
                {"label": "Patung", "value": "938504"},
                {"label": "Sarung Tangan", "value": "938632"},
                {"label": "Topi", "value": "938760"},
                {"label": "Sepatu", "value": "938888"},
                {"label": "Buku", "value": "939016"},
                {"label": "Stick Golf", "value": "939144"},
                {"label": "Bendera & Banner", "value": "939272"},
                {"label": "Cetakan & Poster", "value": "939400"},
                {"label": "Majalah", "value": "939528"}
            ]},
            {"label": "Koin & Uang Koleksi", "value": "952712", "children": [
                {"label": "Koin & Emas Batangan", "value": "952840"},
                {"label": "Uang Kertas", "value": "952968"}
            ]}
        ]
    },
    {
        "label": "Mainan & Hobi", "value": "19",
        "children": [
            {"label": "Boneka & Boneka Mainan", "value": "859656", "children": [
                {"label": "Aksesoris Boneka", "value": "604390"},
                {"label": "Boneka Mainan", "value": "700699"},
                {"label": "Boneka", "value": "861448"},
                {"label": "Rumah Boneka & Playset ", "value": "861704"}
            ]},
            {"label": "Mainan Klasik & Baru", "value": "860296", "children": [
                {"label": "Kendaraan Model & Mainan", "value": "700700"},
                {"label": "Boneka & Teater Boneka", "value": "822032"},
                {"label": "Fidget & Mainan Jari", "value": "822672"},
                {"label": "Pretend Play", "value": "869000"},
                {"label": "Mainan Baru & Gag", "value": "869128"},
                {"label": "Tokoh Aksi & Mainan", "value": "869256"},
                {"label": "Mainan Membangun", "value": "869512"},
                {"label": "Mainan Pereda Stres", "value": "869640"},
                {"label": "Yo-yo ", "value": "869768"},
                {"label": "Mainan Kapsul", "value": "869896"},
                {"label": "Spinning Top", "value": "870024"},
                {"label": "Mainan Slime & Squishy", "value": "963080"},
                {"label": "Mahyong", "value": "963208"}
            ]},
            {"label": "Game & Teka-teki", "value": "860168", "children": [
                {"label": "Permainan Lantai", "value": "820880"},
                {"label": "Permainan Tumpuk-menumpuk", "value": "821136"},
                {"label": "Kubus Ajaib", "value": "868232"},
                {"label": "Teka-teki", "value": "868360"},
                {"label": "Dadu", "value": "868488"},
                {"label": "Permainan Papan", "value": "868616"},
                {"label": "Permainan Kartu", "value": "868744"},
                {"label": "Peralatan akrobat ajaib", "value": "868872"}
            ]},
            {"label": "Mainan Elektrik & Remote Control", "value": "860040", "children": [
                {"label": "Alas Dance", "value": "821264"},
                {"label": "Mesin Karaoke", "value": "821392"},
                {"label": "Walkie Talkie", "value": "821520"},
                {"label": "Peliharaan Elektronik", "value": "821648"},
                {"label": "Kamera Digital", "value": "842768"},
                {"label": "Pesawat & Helikopter", "value": "867080"},
                {"label": "Sepeda Motor", "value": "867336"},
                {"label": "Kapal & Kapal Selam", "value": "867464"},
                {"label": "Mobil, Lori & Kereta Api", "value": "867592"},
                {"label": "Hewan", "value": "867720"},
                {"label": "Tank", "value": "867848"},
                {"label": "Robot ", "value": "867976"},
                {"label": "Aksesoris mainan listrik", "value": "868104"}
            ]},
            {"label": "Mainan Edukasi", "value": "859784", "children": [
                {"label": "Detektif & Mata-mata", "value": "821776"},
                {"label": "Flash Card", "value": "821904"},
                {"label": "Seni & Kerajinan", "value": "862472"},
                {"label": "Mainan Matematika", "value": "862728"},
                {"label": "Mainan Sains & Teknologi", "value": "862984"},
                {"label": "Penyortir Bentuk", "value": "863240"},
                {"label": "Mainan Musikal", "value": "863752"},
                {"label": "Tablet & Komputer Mainan", "value": "864136"},
                {"label": "Mainan Pembelajaran Bahasa", "value": "997000"}
            ]},
            {"label": "Olahraga & Outdoor Play", "value": "859912", "children": [
                {"label": "Mainan Eksplorasi Alam", "value": "822160"},
                {"label": "Permainan Kelereng", "value": "822288"},
                {"label": "Gelembung", "value": "822416"},
                {"label": "Pedang Mainan", "value": "822544"},
                {"label": "Mainan Berkendara", "value": "864520"},
                {"label": "Peralatan Taman Bermain", "value": "864776"},
                {"label": "Mainan Rumah-rumahan, Tenda, & Terowongan", "value": "865160"},
                {"label": "Mainan Kolam Renang, Air & Pasir", "value": "865416"},
                {"label": "Mainan Pistol & Peledak", "value": "865672"},
                {"label": "Mainan Olahraga", "value": "866056"},
                {"label": "Flying Toys", "value": "866312"},
                {"label": "Layang-layang & Kincir Angin", "value": "866696"}
            ]},
            {"label": "Alat Musik & Aksesori", "value": "860552", "children": [
                {"label": "Keyboard & Piano", "value": "870152"},
                {"label": "Alat Musik Perkusi", "value": "870280"},
                {"label": "Alat Musik Tiup", "value": "870408"},
                {"label": "Gitar & Alat Musik Senar", "value": "870664"},
                {"label": "Aksesoris Musik", "value": "870792"},
                {"label": "Sintesis elektronik", "value": "870920"},
                {"label": "Tas & Casing Instrumen", "value": "904072"}
            ]},
            {"label": "DIY", "value": "951560", "children": [
                {"label": "Scrapbooking & Stamping", "value": "951688"},
                {"label": "Merajut & Mengait Benang", "value": "951816"},
                {"label": "Meronce Manik-manik & Pembuatan Perhiasan", "value": "951944"},
                {"label": "Menyulam", "value": "952072"},
                {"label": "Perlengkapan Melukis DIY", "value": "952200"},
                {"label": "Perlengkapan DIY Khusus", "value": "952328"},
                {"label": "Prakarya Kulit", "value": "952456"},
                {"label": "Pembuatan Lilin & Sabun", "value": "952584"},
                {"label": "Pembuatan Lencana", "value": "954248"},
                {"label": "Tembikar & Keramik", "value": "954376"},
                {"label": "Kerajinan Kayu DIY", "value": "954504"},
                {"label": "Kerajinan Felt", "value": "954632"}
            ]}
        ]
    },
    {
        "label": "Peralatan Dapur", "value": "11",
        "children": [
            {"label": "Peralatan & Gadget Dapur", "value": "859528", "children": [
                {"label": "Melestarikan Kontainer", "value": "600029"},
                {"label": "Peralatan Buah & Sayuran", "value": "600060"},
                {"label": "Alat Ukur", "value": "600121"},
                {"label": "Korek", "value": "600123"},
                {"label": "Pengatur Waktu Dapur", "value": "600127"},
                {"label": "Peralatan Memasak Daging & Ayam", "value": "600132"},
                {"label": "Ayakan dan Saringan", "value": "600135"},
                {"label": "Yang lain", "value": "600139"},
                {"label": "Peralatan Memasak", "value": "600148"},
                {"label": "Tempat Bumbu", "value": "865288"},
                {"label": "Termometer Dapur", "value": "865544"},
                {"label": "Peralatan Memasak Pasta & Pizza", "value": "865800"},
                {"label": "Peralatan Membuat Es Krim", "value": "865928"},
                {"label": "Peralatan Pengolah Telur", "value": "866184"},
                {"label": "Peralatan Memasak Seafood", "value": "866440"},
                {"label": "Peralatan Pengolah Minuman", "value": "866568"},
                {"label": "Pembuka", "value": "866824"},
                {"label": "Dispenser Minyak", "value": "866952"},
                {"label": "Pengupas & Pemotong", "value": "867208"},
                {"label": "Timbangan Dapur", "value": "863248"}
            ]},
            {"label": "Perlengkapan Minum", "value": "859400", "children": [
                {"label": "Termos Vakum", "value": "600032"},
                {"label": "Barang Pecah Belah", "value": "600036"},
                {"label": "Mug", "value": "600042"},
                {"label": "Aksesoris Perlengkapan Minum", "value": "600047"},
                {"label": "Botol Air", "value": "600048"},
                {"label": "Cangkir & Tatakan", "value": "600095"},
                {"label": "Ketel & Jug", "value": "864904"},
                {"label": "Hip Flask", "value": "865032"}
            ]},
            {"label": "Sendok Garpu & Peralatan Makan", "value": "859272", "children": [
                {"label": "Tatakan Piring & Gelas", "value": "600033"},
                {"label": "Kotak Bekal", "value": "600059"},
                {"label": "Sumpit", "value": "600063"},
                {"label": "Piring", "value": "600064"},
                {"label": "Mangkuk", "value": "600069"},
                {"label": "Garpu", "value": "600070"},
                {"label": "Set Peralatan Makan", "value": "600071"},
                {"label": "Pisau", "value": "600072"},
                {"label": "Sendok", "value": "600073"},
                {"label": "Serbet", "value": "864648"},
                {"label": "Penyangga Perlengkapan Makan", "value": "993800"}
            ]},
            {"label": "Peralatan Bar & Wine", "value": "858888", "children": [
                {"label": "Peralatan Bar", "value": "600075"},
                {"label": "Rak Wine", "value": "600080"},
                {"label": "Set Anggur", "value": "600081"},
                {"label": "Peralatan Pembuat Anggur", "value": "806672"}
            ]},
            {"label": "Peralatan Teh & Kopi", "value": "858504", "children": [
                {"label": "Teko Kopi", "value": "600096"},
                {"label": "Set Cangkir Kopi", "value": "600100"},
                {"label": "Botol Susu", "value": "600102"},
                {"label": "Alat Pemroses Kopi", "value": "600103"},
                {"label": "Penyaring Kopi", "value": "860424"},
                {"label": "Penggiling Kopi Manual", "value": "860680"},
                {"label": "Teko", "value": "860808"},
                {"label": "Set Cangkir Teh", "value": "860936"},
                {"label": "Alat Pemroses Teh", "value": "861064"}
            ]},
            {"label": "Alat Pembuat Roti", "value": "859016", "children": [
                {"label": "Loyang & Cetakan Kue", "value": "600119"},
                {"label": "Peralatan Pembuat Kue", "value": "600152"},
                {"label": "Baking Set", "value": "862600"},
                {"label": "Sarung Tangan Oven", "value": "862856"},
                {"label": "Nampan Pemanggang", "value": "863112"},
                {"label": "Alat Dekorasi", "value": "863368"}
            ]},
            {"label": "Pisau Dapur", "value": "858632", "children": [
                {"label": "Pisau Dapur", "value": "600145"},
                {"label": "Talenan", "value": "600151"},
                {"label": "Pengasah Pisau", "value": "861192"},
                {"label": "Blok & Penyimpanan Pisau", "value": "861320"},
                {"label": "Gunting Dapur", "value": "861576"},
                {"label": "Set Blok Pisau", "value": "861832"}
            ]},
            {"label": "Peralatan Masak", "value": "859144", "children": [
                {"label": "Pot", "value": "600146"},
                {"label": "Set Peralatan Masak", "value": "863624"},
                {"label": "Wajan & Penggorengan", "value": "863880"},
                {"label": "Pengukus", "value": "864008"},
                {"label": "Pressure Cooker", "value": "864264"},
                {"label": "Peralatan Masak Sekali Pakai", "value": "864392"},
                {"label": "Aksesori Alat Masak", "value": "1001864"}
            ]},
            {"label": "Barbecue", "value": "858760", "children": [
                {"label": "Barbecue", "value": "862216"},
                {"label": "Peralatan Barbecue", "value": "862344"}
            ]}
        ]
    },
    {
        "label": "Perbaikan Rumah", "value": "22",
        "children": [
            {"label": "Perlengkapan Taman", "value": "873352", "children": [
                {"label": "Pemanas Teras & Perapian", "value": "802576"},
                {"label": "Kolam Renang, Bak Mandi Air Panas & Perlengkapannya", "value": "802704"},
                {"label": "Bedengan & Penyangga Tanaman", "value": "802960"},
                {"label": "Rumah Kaca & Paket Menanam", "value": "803088"},
                {"label": "Perlengkapan Peternakan Lebah", "value": "899592"},
                {"label": "Perawatan Tanaman", "value": "899720"},
                {"label": "Pengendali Hama", "value": "899848"},
                {"label": "Dekorasi Taman", "value": "899976"},
                {"label": "Penyiraman & Irigasi", "value": "900104"},
                {"label": "Pot & Planter Taman", "value": "900232"},
                {"label": "Bangunan Taman", "value": "900360"},
                {"label": "Benih Bunga & Tanaman", "value": "979976"},
                {"label": "Tanah untuk Berkebun", "value": "980232"},
                {"label": "Tumbuhan & Bunga Segar", "value": "853776"}
            ]},
            {"label": "Perlengkapan Bangunan", "value": "872968", "children": [
                {"label": "Alat Pemasangan Wallpaper", "value": "802832"},
                {"label": "Pemanas, Pendingin & Ventilasi", "value": "896904"},
                {"label": "Pintu, Gerbang & Jendela", "value": "897032"},
                {"label": "Wallpaper & Dekorasi Dinding", "value": "897160"},
                {"label": "Perlengkapan & Alat Melukis", "value": "897288"},
                {"label": "Atap & Lantai", "value": "897416"},
                {"label": "Tangga", "value": "897544"},
                {"label": "Troli", "value": "897672"},
                {"label": "Wall Paint", "value": "853904"}
            ]},
            {"label": "Instalasi Tenaga Surya & Angin", "value": "808208", "children": [
                {"label": "Inverter Daya", "value": "808336"},
                {"label": "Panel Surya", "value": "808464"},
                {"label": "Pengontrol Pengisian Daya & Aksesorinya", "value": "808592"},
                {"label": "Sistem Tenaga Surya", "value": "808720"},
                {"label": "Turbin Angin", "value": "808848"}
            ]},
            {"label": "Lampu & Pencahayaan", "value": "872456", "children": [
                {"label": "Aksesoris Pencahayaan", "value": "893576"},
                {"label": "Bohlam, Tube & Strip", "value": "893704"},
                {"label": "Pencahayaan Indoor", "value": "893832"},
                {"label": "Pencahayaan Portabel", "value": "893960"},
                {"label": "Pencahayaan Outdoor", "value": "894088"},
                {"label": "Pencahayaan Baru", "value": "894216"},
                {"label": "Pencahayaan Profesional", "value": "894344"},
                {"label": "Pencahayaan Komersial", "value": "894472"}
            ]},
            {"label": "Peralatan & Perlengkapan Listrik", "value": "872584", "children": [
                {"label": "Konektor & Terminal", "value": "894600"},
                {"label": "Sakelar & Aksesoris", "value": "894728"},
                {"label": "Relay & Breaker", "value": "894856"},
                {"label": "Catu Daya", "value": "894984"},
                {"label": "Motor, Generator, & Aksesoris", "value": "895112"},
                {"label": "Soket & Aksesoris Listrik", "value": "895240"},
                {"label": "Kawat & Kabel ", "value": "895368"},
                {"label": "Transformer", "value": "895496"},
                {"label": "Penghemat Daya", "value": "983176"}
            ]},
            {"label": "Perlengkapan Dapur", "value": "872712", "children": [
                {"label": "Keran Dapur", "value": "895624"},
                {"label": "Wastafel Dapur", "value": "895752"},
                {"label": "Lemari Dapur", "value": "895880"},
                {"label": "Perangkat Penyaringan Air", "value": "896008"},
                {"label": "Aksesoris Perlengkapan Dapur", "value": "896136"},
                {"label": "Set Perlengkapan Dapur", "value": "896264"}
            ]},
            {"label": "Sistem Rumah Pintar", "value": "872840", "children": [
                {"label": "Kontrol Rumah Pintar", "value": "896392"},
                {"label": "Sistem Kontrol Suhu", "value": "896520"},
                {"label": "Sistem Kontrol Tirai Otomatis", "value": "896648"},
                {"label": "Sensor Gerak Cerdas", "value": "896776"}
            ]},
            {"label": "Perlengkapan Kamar Mandi", "value": "873096", "children": [
                {"label": "Perlengkapan Mandi", "value": "897800"},
                {"label": "Kait & Bar", "value": "897928"},
                {"label": "Wastafel Kamar Mandi", "value": "898056"},
                {"label": "Keran Kamar Mandi", "value": "898184"},
                {"label": "Bidet & Suku Cadang Bidet", "value": "898312"},
                {"label": "Toilet & Suku Cadang Toilet", "value": "898440"},
                {"label": "Cermin Kamar Mandi", "value": "898568"},
                {"label": "Aksesori Perlengkapan Kamar Mandi", "value": "898696"},
                {"label": "Perlengkapan Kamar Mandi", "value": "898824"},
                {"label": "Bathtub", "value": "979336"},
                {"label": "Palang Pengaman & Kursi Kamar Mandi", "value": "979464"}
            ]},
            {"label": "Keamanan & Keselamatan", "value": "873224", "children": [
                {"label": "Alarm Keamanan", "value": "898952"},
                {"label": "Bel Pintu & Interkom", "value": "899080"},
                {"label": "Peralatan Keselamatan Kerja", "value": "899208"},
                {"label": "Kit Darurat", "value": "899464"}
            ]}
        ]
    },
    {
        "label": "Komputer & Peralatan Kantor", "value": "15",
        "children": [
            {"label": "Komputer Desktop, Laptop & Tablet", "value": "824840", "children": [
                {"label": "Laptop", "value": "601756"},
                {"label": "Komputer Desktop", "value": "601836"},
                {"label": "Server", "value": "978568"},
                {"label": "All-in-One Desktops", "value": "854672"}
            ]},
            {"label": "Periferal & Aksesoris", "value": "826760", "children": [
                {"label": "Keyboard", "value": "601760"},
                {"label": "USB Hub & Card Reader", "value": "827016"},
                {"label": "Webcam", "value": "827144"},
                {"label": "Cover & Casing Laptop", "value": "827272"},
                {"label": "Bantalan Pendingin", "value": "827400"},
                {"label": "Dudukan & Alas Laptop", "value": "827528"},
                {"label": "Cover Keyboard & Trackpad", "value": "827656"},
                {"label": "Baterai Laptop", "value": "827784"},
                {"label": "Charger & Adaptor Laptop", "value": "827912"},
                {"label": "Alas Mouse", "value": "828040"}
            ]},
            {"label": "Komponen Desktop & Laptop", "value": "825352", "children": [
                {"label": "Monitor", "value": "601783"},
                {"label": "Kipas & Heatsink", "value": "825480"},
                {"label": "Prosesor", "value": "825608"},
                {"label": "Motherboard", "value": "825736"},
                {"label": "Graphic Card", "value": "825864"},
                {"label": "Unit Catu Daya", "value": "825992"},
                {"label": "RAM", "value": "826120"},
                {"label": "UPS & Stabilizer", "value": "826248"},
                {"label": "Casing PC", "value": "826376"},
                {"label": "Drive Optik", "value": "826504"},
                {"label": "Sound Card", "value": "826632"}
            ]},
            {"label": "Alat Tulis & Perlengkapan Kantor", "value": "831112", "children": [
                {"label": "Alat Tulis & Koreksi", "value": "603002"},
                {"label": "Perlengkapan Penjilidan", "value": "831240"},
                {"label": "Perlengkapan Pemotong", "value": "831368"},
                {"label": "Perlengkapan Sekolah & Pendidikan", "value": "831624"},
                {"label": "Perlengkapan Seni", "value": "831752"},
                {"label": "Notebook & Kertas", "value": "831880"},
                {"label": "Amplop & Perlengkapan Pos", "value": "832008"},
                {"label": "Hadiah & Pembungkus", "value": "832136"},
                {"label": "Perlengkapan Akuntansi", "value": "832264"},
                {"label": "Perlengkapan Penataan & Aksesori Meja", "value": "832392"},
                {"label": "Kartu", "value": "855560"},
                {"label": "Brankas", "value": "899336"},
                {"label": "Kalender & Aksesori", "value": "987912"},
                {"label": "Produk Pengaturan File Kantor", "value": "988040"},
                {"label": "Lencana & Perlengkapan Identifikasi", "value": "988168"},
                {"label": "Label, Pembagi Indeks & Cap", "value": "988296"},
                {"label": "Perlengkapan Pengukuran Kantor", "value": "988552"},
                {"label": "Perlengkapan Presentasi Kantor", "value": "988680"},
                {"label": "Pita, Perekat & Pengencang", "value": "988936"}
            ]},
            {"label": "Penyimpanan Data & Software", "value": "828168", "children": [
                {"label": "Hard Drive", "value": "828296"},
                {"label": "SSD", "value": "828424"},
                {"label": "Network Attached Storage (NAS)", "value": "828552"},
                {"label": "Flash Drive & Kabel OTG", "value": "828680"},
                {"label": "Hard Disk Enclosure & Docking Station", "value": "828808"},
                {"label": "Compact Disc", "value": "828936"},
                {"label": "Software", "value": "829064"}
            ]},
            {"label": "Komponen Network", "value": "829192", "children": [
                {"label": "Modem & Router Wireless", "value": "829320"},
                {"label": "Repeater", "value": "829448"},
                {"label": "Adaptor Wireless & Network Card", "value": "829576"},
                {"label": "Adaptor Powerline", "value": "829704"},
                {"label": "Sakelar Network & PoE", "value": "829832"},
                {"label": "Kabel & Konektor Network", "value": "829960"},
                {"label": "Sakelar KVM", "value": "830088"},
                {"label": "Server Cetak", "value": "830216"}
            ]},
            {"label": "Peralatan Kantor", "value": "830344", "children": [
                {"label": "Mesin Ketik", "value": "830472"},
                {"label": "Perangkat Kontrol Akses & Kehadiran", "value": "830600"},
                {"label": "Penghancur Kertas", "value": "830728"},
                {"label": "Penghitung Uang", "value": "830856"},
                {"label": "Printer & Scanner", "value": "830984"},
                {"label": "Perlengkapan Pencetakan 3D", "value": "985480"},
                {"label": "Mesin Faks", "value": "985608"},
                {"label": "Pemindai Barcode", "value": "986248"},
                {"label": "Peralatan Ritel Pintar", "value": "986504"},
                {"label": "Printer Label", "value": "986888"},
                {"label": "Peralatan Pencetakan Iklan", "value": "987272"},
                {"label": "Kartrid Tinta & Toner", "value": "987528"},
                {"label": "Komponen Peralatan Kantor", "value": "987656"},
                {"label": "Laminator", "value": "987784"},
                {"label": "Perangkat Video & Audio untuk Konferensi", "value": "993160"}
            ]}
        ]
    },
    {
        "label": "Koper & Tas", "value": "7",
        "children": [
            {"label": "Tas Fungsional", "value": "902792", "children": [
                {"label": "Tas Laptop", "value": "601417"},
                {"label": "Tas Rias", "value": "601440"},
                {"label": "Ransel", "value": "601446"},
                {"label": "Tas Bekal", "value": "904200"},
                {"label": "Tas Pendingin", "value": "904328"},
                {"label": "Tas Belanja", "value": "904456"},
                {"label": "Kantong Perlengkapan Mandi", "value": "995208"}
            ]},
            {"label": "Koper & Tas Travel", "value": "902664", "children": [
                {"label": "Tas Perjalanan", "value": "601419"},
                {"label": "Aksesoris Koper", "value": "601449"},
                {"label": "Koper", "value": "903688"},
                {"label": "Tas Bepergian", "value": "903816"},
                {"label": "Holder & Sampul Paspor", "value": "903944"}
            ]},
            {"label": "Tas Pria", "value": "902536", "children": [
                {"label": "Tas Selempang & Bahu", "value": "601429"},
                {"label": "Dompet", "value": "601430"},
                {"label": "Clutch", "value": "601431"},
                {"label": "Tote Bag", "value": "903304"},
                {"label": "Tas Kerja", "value": "903432"},
                {"label": "Bum Bag & Belt Bag", "value": "903560"}
            ]},
            {"label": "Tas Wanita", "value": "902408", "children": [
                {"label": "Tas Selempang & Bahu", "value": "601439"},
                {"label": "Dompet", "value": "601441"},
                {"label": "Clutch & Wristlet", "value": "601444"},
                {"label": "Tas Tangan", "value": "601445"},
                {"label": "Bum Bag & Belt Bag", "value": "903048"},
                {"label": "Tote Bag", "value": "903176"}
            ]},
            {"label": "Aksesoris Tas", "value": "902920", "children": [
                {"label": "Tali & Rantai Tas", "value": "904584"},
                {"label": "Gantungan Tas", "value": "904712"},
                {"label": "Gantungan & Syal Tas", "value": "904840"},
                {"label": "Bag Organizer", "value": "904968"},
                {"label": "Pembersihan & Perawatan", "value": "905096"}
            ]}
        ]
    },
    {
        "label": "Sepatu", "value": "6",
        "children": [
            {"label": "Sepatu Pria", "value": "900616", "children": [
                {"label": "Sepatu Kasual", "value": "601357"},
                {"label": "Sandal & Sandal Jepit", "value": "601364"},
                {"label": "Oxford", "value": "601369"},
                {"label": "Selop", "value": "601374"},
                {"label": "Sepatu Boot", "value": "601376"},
                {"label": "Sepatu Kerja & Sepatu Proyek", "value": "804496"},
                {"label": "Sepatu Formal", "value": "901640"},
                {"label": "Sandal Slip-on & Sepatu Flat", "value": "901768"},
                {"label": "Sandal Mule & Clog", "value": "901896"}
            ]},
            {"label": "Aksesoris Sepatu", "value": "900744", "children": [
                {"label": "Sol & Liner Tumit", "value": "601366"},
                {"label": "Pelindung Jari Kaki di Sepatu & Bot", "value": "804240"},
                {"label": "Hiasan Sepatu", "value": "804368"},
                {"label": "Shoe Horn & Tree", "value": "902024"},
                {"label": "Tali sepatu", "value": "902152"},
                {"label": "Pembersihan & Perawatan", "value": "902280"}
            ]},
            {"label": "Sepatu Wanita", "value": "900488", "children": [
                {"label": "Oxford", "value": "601387"},
                {"label": "Hak Tinggi", "value": "601396"},
                {"label": "Sandal", "value": "601405"},
                {"label": "Sepatu Bot Martin", "value": "601409"},
                {"label": "Sepatu Kerja & Sepatu Proyek", "value": "804624"},
                {"label": "Sepatu Mary Jane", "value": "804752"},
                {"label": "Sepatu Kasual", "value": "900872"},
                {"label": "Flat", "value": "901000"},
                {"label": "Sandal & Sandal Jepit", "value": "901128"},
                {"label": "Slip-On", "value": "901256"},
                {"label": "Sandal Mule & Clog", "value": "901384"}
            ]}
        ]
    },
    {
        "label": "Alat & Perangkat Keras", "value": "21",
        "children": [
            {"label": "Perkakas", "value": "871688", "children": [
                {"label": "Tang Keling", "value": "801168"},
                {"label": "Alat Serbaguna & Aksesorinya", "value": "802064"},
                {"label": "Alat Pemotong", "value": "802192"},
                {"label": "Alat Pertukangan Baru & Pasang Ubin", "value": "802320"},
                {"label": "Alat Tangan Khusus", "value": "802448"},
                {"label": "Pinset Industri", "value": "883208"},
                {"label": "Palu", "value": "883336"},
                {"label": "Pisau", "value": "883464"},
                {"label": "Tang", "value": "883592"},
                {"label": "Gergaji", "value": "883720"},
                {"label": "Gunting", "value": "883848"},
                {"label": "Obeng", "value": "883976"},
                {"label": "Kunci Pas", "value": "884104"},
                {"label": "Pemahat", "value": "884232"},
                {"label": "Sumbu", "value": "884360"},
                {"label": "Kit Alat", "value": "884488"},
                {"label": "Aksesori Perkakas Tangan", "value": "980744"},
                {"label": "Timbangan Industri", "value": "980872"},
                {"label": "Alat Perbaikan Jam Tangan", "value": "981000"}
            ]},
            {"label": "Peralatan Listrik", "value": "871560", "children": [
                {"label": "Perkakas Listrik Khusus", "value": "801296"},
                {"label": "Bor Listrik", "value": "881544"},
                {"label": "Obeng Listrik", "value": "881672"},
                {"label": "Gergaji Listrik", "value": "881800"},
                {"label": "Blower", "value": "881928"},
                {"label": "Penggiling Sudut", "value": "882056"},
                {"label": "Pemoles", "value": "882184"},
                {"label": "Kunci Pas Listrik", "value": "882312"},
                {"label": "Nail Gun", "value": "882440"},
                {"label": "Spray Gun", "value": "882568"},
                {"label": "Heat Gun", "value": "882696"},
                {"label": "Glue Gun", "value": "882824"},
                {"label": "Aksesoris Alat Listrik", "value": "882952"},
                {"label": "Set Alat Listrik", "value": "883080"},
                {"label": "Pencuci Bertekanan", "value": "980360"},
                {"label": "Kompresor Udara", "value": "980616"},
                {"label": "Mesin Router Kayu", "value": "994056"}
            ]},
            {"label": "Peralatan Kebun", "value": "871944", "children": [
                {"label": "Alat Berkebun Khusus", "value": "801424"},
                {"label": "Pendeteksi Logam", "value": "801552"},
                {"label": "Gergaji Mesin", "value": "801680"},
                {"label": "Alat Pembersih Salju", "value": "801808"},
                {"label": "Aksesori Alat Berkebun", "value": "801936"},
                {"label": "Pemangkas Rumput", "value": "885384"},
                {"label": "Leaf Blower & Vacuum", "value": "885512"},
                {"label": "Spade & Shovel", "value": "885640"},
                {"label": "Alat Pemangkasan", "value": "885768"},
                {"label": "Cangkul & Garu", "value": "885896"},
                {"label": "Garpu & Sendok", "value": "886024"},
                {"label": "Sarung Tangan Berkebun & Alat Pelindung Diri", "value": "886152"},
                {"label": "Alat Pembersih Taman", "value": "886280"},
                {"label": "Pemotong Rumput", "value": "979848"}
            ]},
            {"label": "Alat Ukur", "value": "871816", "children": [
                {"label": "Instrumen Optik", "value": "884616"},
                {"label": "Alat Ukur Tekanan", "value": "884744"},
                {"label": "Alat Ukur Suhu", "value": "884872"},
                {"label": "Alat Ukur Tangan", "value": "885000"},
                {"label": "Alat Ukur Fisik", "value": "885128"},
                {"label": "Alat Ukur Listrik", "value": "885256"}
            ]},
            {"label": "Peralatan Solder", "value": "872072", "children": [
                {"label": "Setrika Solder Elektronik", "value": "886408"},
                {"label": "Stasiun Solder", "value": "886536"},
                {"label": "Pengelas", "value": "886664"},
                {"label": "Aksesoris Pengelasan", "value": "886792"}
            ]},
            {"label": "Organizer Perkakas", "value": "872200", "children": [
                {"label": "Tas Perkakas", "value": "886920"},
                {"label": "Casing & Kotak Perkakas", "value": "887048"},
                {"label": "Rak & Bar Perkakas", "value": "887176"}
            ]},
            {"label": "Perangkat keras", "value": "872328", "children": [
                {"label": "Perangkat Perabotan", "value": "887304"},
                {"label": "Perangkat Keras Jendela", "value": "887432"},
                {"label": "Perangkat Keras Pintu ", "value": "887560"},
                {"label": "Perangkat Keras Mekanik", "value": "887688"},
                {"label": "Pengencang & Kait", "value": "887816"},
                {"label": "Tali, Rantai & Pulley", "value": "887944"},
                {"label": "Gembok & Apitan", "value": "888072"},
                {"label": "Perekat, Tape & Sealer", "value": "888200"},
                {"label": "Klem", "value": "888328"},
                {"label": "Produk Pengampelas & Pemoles Akhir", "value": "983048"},
                {"label": "Magnet", "value": "993928"}
            ]},
            {"label": "Pompa & Perpipaan", "value": "980488", "children": [
                {"label": "Pompa, Komponen & Aksesori", "value": "982536"},
                {"label": "Pipa & Fiting", "value": "982664"},
                {"label": "Katup & Komponennya", "value": "982792"}
            ]}
        ]
    },
    {
        "label": "Tekstil & Soft Furnishing", "value": "12",
        "children": [
            {"label": "Seprei", "value": "808328", "children": [
                {"label": "Selimut & Penutup", "value": "600157"},
                {"label": "Seprai & Sarung Bantal", "value": "600165"},
                {"label": "Quilt", "value": "700652"},
                {"label": "Bantal & Bantal Sandaran di Tempat Tidur", "value": "700653"},
                {"label": "Aksesori Tempat Tidur", "value": "807184"},
                {"label": "Set Tempat Tidur", "value": "808584"},
                {"label": "Duvet ", "value": "808840"},
                {"label": "Bedspread", "value": "809096"},
                {"label": "Penutup Kolong", "value": "809352"},
                {"label": "Pad & Topper Matras", "value": "809480"},
                {"label": "Duvet Cover", "value": "809608"},
                {"label": "Kelambu", "value": "809736"},
                {"label": "Tempat Tidur Anak", "value": "809864"},
                {"label": "Karpet & Alas Penyejuk", "value": "994952"}
            ]},
            {"label": "Tekstil Rumah Tangga", "value": "809992", "children": [
                {"label": "Sarung Kursi", "value": "600203"},
                {"label": "Taplak Meja", "value": "600204"},
                {"label": "Karpet, Keset & Permadani", "value": "600221"},
                {"label": "Bantalan, Bantal Duduk, & Sarung Bantal", "value": "700661"},
                {"label": "Sarung Sofa", "value": "810376"},
                {"label": "Tirai", "value": "810504"}
            ]},
            {"label": "Kain & Perlengkapan Jahit", "value": "811016", "children": [
                {"label": "Kit Alat Jahit", "value": "600251"},
                {"label": "Kit Alat Menjahit", "value": "600252"},
                {"label": "Kain", "value": "811144"},
                {"label": "Aksesoris & Haberdashery", "value": "811528"},
                {"label": "Mesin Jahit", "value": "811656"},
                {"label": "Benang", "value": "811784"},
                {"label": "Jarum", "value": "811912"}
            ]}
        ]
    },
    {
        "label": "Peralatan Rumah Tangga", "value": "13",
        "children": [
            {"label": "Peralatan Rumah Tangga Besar", "value": "845064", "children": [
                {"label": "Televisi", "value": "600852"},
                {"label": "Air Conditioner", "value": "849928"},
                {"label": "Pemanas Air", "value": "850056"},
                {"label": "Mesin Cuci & Pengering", "value": "850184"},
                {"label": "Kulkas & Freezer", "value": "850312"},
                {"label": "Range Hood", "value": "850440"},
                {"label": "Oven, Range & Kompor", "value": "850568"},
                {"label": "Pencuci Piring", "value": "850696"},
                {"label": "Komponen & Aksesori Peralatan Besar", "value": "850824"},
                {"label": "Streaming Media Devices", "value": "852368"},
                {"label": "Portable Air Conditioners", "value": "852496"},
                {"label": "Beverage Refrigerators", "value": "852624"}
            ]},
            {"label": "Peralatan Rumah Tangga", "value": "844808", "children": [
                {"label": "Air Purifier", "value": "601090"},
                {"label": "Humidifier", "value": "601092"},
                {"label": "Pemanas", "value": "601095"},
                {"label": "Setrika", "value": "601100"},
                {"label": "Penyedot Debu & Robot Penyapu", "value": "601102"},
                {"label": "Kipas Angin", "value": "601104"},
                {"label": "Suku Cadang Peralatan Rumah Tangga", "value": "601106"},
                {"label": "Steamer Pakaian", "value": "601107"},
                {"label": "Dehumidifier", "value": "601108"},
                {"label": "Pembersih Jendela Listrik", "value": "601116"},
                {"label": "Penggosok Putar Listrik", "value": "801040"},
                {"label": "Pel Listrik", "value": "934152"},
                {"label": "Pengering Pakaian & Sepatu", "value": "934280"},
                {"label": "Pembunuh Nyamuk Elektronik", "value": "934408"},
                {"label": "Mesin Penjawab", "value": "979080"},
                {"label": "Selimut Listrik", "value": "983432"},
                {"label": "Pembersih Serat", "value": "983560"},
                {"label": "Pengering Tangan", "value": "984072"},
                {"label": "Alat Sterilisasi Rumah", "value": "984456"},
                {"label": "Penyemir Sepatu Listrik", "value": "990984"}
            ]},
            {"label": "Kitchen Appliances", "value": "844168", "children": [
                {"label": "Pemanggang Roti", "value": "847624"},
                {"label": "Rice & Pressure Cooker", "value": "847752"},
                {"label": "Pengukus Listrik", "value": "847880"},
                {"label": "Vacuum Sealer", "value": "848008"},
                {"label": "Microwave", "value": "848136"},
                {"label": "Countertop Oven", "value": "848264"},
                {"label": "Ketel Listrik", "value": "848392"},
                {"label": "Juicer & Blender ", "value": "848520"},
                {"label": "Mesin Pemroses Kopi & Aksesoris", "value": "934536"},
                {"label": "Pembuat Roti", "value": "934664"},
                {"label": "Mixer", "value": "934792"},
                {"label": "Filter Air", "value": "934920"},
                {"label": "Pendingin & Dispenser Air", "value": "935048"},
                {"label": "Pengolah Makanan", "value": "935176"},
                {"label": "Fryer", "value": "935304"},
                {"label": "Suku Cadang Peralatan Dapur", "value": "935432"},
                {"label": "Kompor Induksi", "value": "977800"},
                {"label": "Panggangan Listrik", "value": "977928"},
                {"label": "Panci Pemanas Listrik", "value": "978312"},
                {"label": "Peralatan Dapur Khusus", "value": "983304"},
                {"label": "Pembuang Limbah Makanan", "value": "983944"},
                {"label": "Electric & Gas Stoves", "value": "852240"},
                {"label": "Soda Makers", "value": "880016"}
            ]},
            {"label": "Peralatan Komersial", "value": "845320", "children": [
                {"label": "Peralatan Laundry", "value": "850952"},
                {"label": "Peralatan Kebersihan", "value": "851080"},
                {"label": "Kompor Komersial", "value": "851208"},
                {"label": "Peralatan Kipas & Knalpot", "value": "851336"},
                {"label": "Peralatan Pendingin", "value": "851464"},
                {"label": "Peralatan Pengolahan Makanan", "value": "851592"},
                {"label": "Suku Cadang Alat Komersial", "value": "851720"}
            ]}
        ]
    },
    {
        "label": "Perlengkapan Hewan Peliharaan", "value": "17",
        "children": [
            {"label": "Perlengkapan Ikan & Perairan", "value": "819848", "children": [
                {"label": "Obat-obatan & Perlengkapan Kesehatan Ikan", "value": "602165"},
                {"label": "Dekorasi", "value": "819976"},
                {"label": "Pencahayaan", "value": "820104"},
                {"label": "Akuarium & Tangki", "value": "820232"},
                {"label": "Pengatur Suhu", "value": "820360"},
                {"label": "Pengolahan Air", "value": "820488"},
                {"label": "Pompa & Filter", "value": "820616"},
                {"label": "Peralatan Pembersih", "value": "820744"},
                {"label": "Alat Makan", "value": "820872"},
                {"label": "Makanan Hewan Peliharaan Akuarium", "value": "981896"},
                {"label": "Nutrition & Health Care Supplies", "value": "855568"}
            ]},
            {"label": "Perawatan Kesehatan Anjing & Kucing", "value": "818184", "children": [
                {"label": "Cone Leher & Alat Pendukung Pemulihan", "value": "804880"},
                {"label": "Perawatan Kutu & Tungau", "value": "818312"},
                {"label": "Pengobatan", "value": "818440"},
                {"label": "Vitamin & Suplemen", "value": "818568"}
            ]},
            {"label": "Perlengkapan Burung", "value": "821896", "children": [
                {"label": "Layanan Kesehatan Burung", "value": "805008"},
                {"label": "Kandang & Aksesoris", "value": "822024"},
                {"label": "Perlengkapan Perawatan", "value": "822152"},
                {"label": "Mainan", "value": "822280"},
                {"label": "Ayunan & Tempat Bertengger", "value": "822408"},
                {"label": "Alat Bantu Pelatihan", "value": "822536"},
                {"label": "Alat Makan", "value": "822664"},
                {"label": "Makanan Burung", "value": "982024"}
            ]},
            {"label": "Pasir Anjing & Kucing", "value": "815624", "children": [
                {"label": "Sistem Latihan Buang Air", "value": "805136"},
                {"label": "Baki & Kotak Sampah", "value": "815752"},
                {"label": "Popok, Pad & Baki", "value": "815880"},
                {"label": "Kantong Kotoran & Sendok", "value": "816008"},
                {"label": "Penghilang Bau & Noda", "value": "816136"},
                {"label": "Detektor Urin", "value": "816264"}
            ]},
            {"label": "Perlengkapan Perawatan Hewan Ternak & Unggas", "value": "1001992", "children": [
                {"label": "Perlengkapan Kesehatan Hewan Ternak", "value": "805264"},
                {"label": "Perlengkapan Grooming", "value": "1002120"},
                {"label": "Mainan", "value": "1002248"},
                {"label": "Alat Pemberi Pakan", "value": "1002376"},
                {"label": "Tag Telinga", "value": "1002504"},
                {"label": "Kandang & Aksesori", "value": "1002632"},
                {"label": "Makanan", "value": "1002760"},
                {"label": "Carrier & Tali", "value": "1003528"}
            ]},
            {"label": "Perlengkapan Reptil & Amfibi", "value": "821000", "children": [
                {"label": "Perlengkapan Kesehatan Reptil", "value": "805392"},
                {"label": "Dekorasi", "value": "821128"},
                {"label": "Terarium & Perlengkapan Pengiriman", "value": "821256"},
                {"label": "Peralatan Pembersih", "value": "821384"},
                {"label": "Produk Temperatur", "value": "821512"},
                {"label": "Pencahayaan", "value": "821640"},
                {"label": "Alat Makan", "value": "821768"},
                {"label": "Makanan Reptil", "value": "982152"}
            ]},
            {"label": "Makanan Anjing & Kucing", "value": "812168", "children": [
                {"label": "Makanan Anjing", "value": "812296"},
                {"label": "Makanan Anjing", "value": "812424"},
                {"label": "Makanan Kucing", "value": "812552"},
                {"label": "Camilan Kucing", "value": "812680"}
            ]},
            {"label": "Furnitur Anjing & Kucing", "value": "812808", "children": [
                {"label": "Tempat Tidur, Sofa & Keset", "value": "812936"},
                {"label": "Rumah", "value": "813064"},
                {"label": "Kandang & Palet", "value": "813192"},
                {"label": "Scratching Pad & Post", "value": "813320"},
                {"label": "Hammock Kucing", "value": "813448"},
                {"label": "Flap Kucing & Anjing", "value": "813576"},
                {"label": "Tangga & Ramp", "value": "813704"},
                {"label": "Playpen", "value": "813832"}
            ]},
            {"label": "Pakaian Anjing & Kucing", "value": "813960", "children": [
                {"label": "Mantel", "value": "814088"},
                {"label": "Kemeja", "value": "814216"},
                {"label": "Jumper & Hoodie", "value": "814344"},
                {"label": "Jaket Keselamatan", "value": "814472"},
                {"label": "Gaun", "value": "814600"},
                {"label": "Jas Hujan", "value": "814728"},
                {"label": "Sepatu & Pelindung Kaki", "value": "814856"},
                {"label": "Aksesoris Leher", "value": "814984"},
                {"label": "Kacamata", "value": "815112"},
                {"label": "Aksesoris Rambut", "value": "815240"},
                {"label": "Topi", "value": "815368"},
                {"label": "Kostum", "value": "815496"}
            ]},
            {"label": "Perawatan Anjing & Kucing", "value": "816392", "children": [
                {"label": "Shampo & Kondisioner", "value": "816520"},
                {"label": "Aksesoris Mandi", "value": "816648"},
                {"label": "Sisir & Sikat", "value": "816776"},
                {"label": "Pengering Rambut", "value": "816904"},
                {"label": "Tisu Grooming", "value": "817032"},
                {"label": "Gunting Grooming", "value": "817160"},
                {"label": "Grooming Clipper", "value": "817288"},
                {"label": "Styptic Gel & Powder", "value": "817416"},
                {"label": "Perawatan Kuku Hewan", "value": "817544"},
                {"label": "Perawatan Telinga", "value": "817672"},
                {"label": "Perawatan Mulut", "value": "817800"},
                {"label": "Perawatan Mata", "value": "817928"},
                {"label": "Produk Penghilang Bulu", "value": "818056"},
                {"label": "Spray & Kolonye Deodoran", "value": "843280"}
            ]},
            {"label": "Aksesoris Anjing & Kucing", "value": "818696", "children": [
                {"label": "Kalung, Harness & Lead", "value": "818824"},
                {"label": "Alat Pelatihan & Perilaku Hewan", "value": "818952"},
                {"label": "Mainan Anjing", "value": "819080"},
                {"label": "Mainan Kucing", "value": "819208"},
                {"label": "Perlengkapan Makan", "value": "819336"},
                {"label": "Tas & Perlengkapan Perjalanan", "value": "819464"},
                {"label": "Kenangan", "value": "819592"},
                {"label": "Kamera & Monitor", "value": "819720"}
            ]},
            {"label": "Perlengkapan Hewan Kecil", "value": "822792", "children": [
                {"label": "Rumah & Habitat", "value": "822920"},
                {"label": "Mainan", "value": "823048"},
                {"label": "Kalung, Harness & Lead", "value": "823176"},
                {"label": "Perlengkapan Makan", "value": "823304"},
                {"label": "Roda Lari", "value": "823432"},
                {"label": "Perlengkapan Perawatan", "value": "823560"},
                {"label": "Operator", "value": "823688"},
                {"label": "Perlengkapan Kesehatan", "value": "823816"},
                {"label": "Penghilang Bau & Noda", "value": "823944"},
                {"label": "Pakaian Hewan Peliharaan Kecil", "value": "981640"},
                {"label": "Makanan Hewan Peliharaan Kecil", "value": "981768"}
            ]}
        ]
    },
    {
        "label": "Aksesori Perhiasan & Turunannya", "value": "28",
        "children": [
            {"label": "Platinum & Emas Karat", "value": "954888", "children": [
                {"label": "Kalung & Liontin Platinum & Emas Karat", "value": "955528"},
                {"label": "Cincin Platinum & Emas Karat", "value": "955656"},
                {"label": "Gelang & Gelang Kaki Platinum & Emas Karat", "value": "955784"},
                {"label": "Anting Platinum & Emas Karat", "value": "955912"},
                {"label": "Set Perhiasan Platinum & Emas Karat", "value": "956040"},
                {"label": "Aksesori Pakaian Platinum & Emas Karat", "value": "956168"}
            ]},
            {"label": "Berlian", "value": "955272", "children": [
                {"label": "Kalung & Liontin Berlian", "value": "956296"},
                {"label": "Cincin Berlian", "value": "958344"},
                {"label": "Gelang & Gelang Kaki Berlian", "value": "958472"},
                {"label": "Anting Berlian", "value": "958600"},
                {"label": "Set Perhiasan Berlian", "value": "958728"},
                {"label": "Aksesori Pakaian Berlian", "value": "958856"}
            ]},
            {"label": "Emas", "value": "955016", "children": [
                {"label": "Kalung & Liontin Emas", "value": "956424"},
                {"label": "Cincin Emas", "value": "956552"},
                {"label": "Gelang & Gelang Kaki Emas", "value": "956680"},
                {"label": "Anting Emas", "value": "956808"},
                {"label": "Set Perhiasan Emas", "value": "956936"},
                {"label": "Aksesori Pakaian Emas", "value": "957064"},
                {"label": "Dekorasi Emas", "value": "970632"},
                {"label": "Emas Setengah Jadi", "value": "970760"}
            ]},
            {"label": "Perak", "value": "955144", "children": [
                {"label": "Kalung & Liontin Perak", "value": "957192"},
                {"label": "Cincin Perak", "value": "957320"},
                {"label": "Gelang & Gelang Kaki Perak", "value": "957448"},
                {"label": "Anting Perak", "value": "957576"},
                {"label": "Set Perhiasan Perak", "value": "957704"},
                {"label": "Aksesori Pakaian Perak", "value": "957832"},
                {"label": "Dekorasi Perak", "value": "957960"},
                {"label": "Perak Setengah Jadi", "value": "958088"}
            ]},
            {"label": "Batu Permata Artifisial", "value": "964360", "children": [
                {"label": "Kalung & Liontin Batu Permata Artifisial", "value": "958216"},
                {"label": "Cincin Batu Permata Artifisial", "value": "973960"},
                {"label": "Gelang & Gelang Kaki Batu Permata Artifisial", "value": "974088"},
                {"label": "Anting Batu Permata Artifisial", "value": "974216"},
                {"label": "Set Perhiasan Batu Permata Artifisial", "value": "974344"},
                {"label": "Aksesori Pakaian Batu Permata Artifisial", "value": "974472"}
            ]},
            {"label": "Batu Giok", "value": "963848", "children": [
                {"label": "Kalung & Liontin Batu Giok", "value": "958984"},
                {"label": "Cincin Batu Giok", "value": "959112"},
                {"label": "Gelang & Gelang Kaki Batu Giok", "value": "971400"},
                {"label": "Anting Batu Giok", "value": "971528"},
                {"label": "Set Perhiasan Batu Giok", "value": "971656"},
                {"label": "Aksesori Pakaian Batu Giok", "value": "971784"},
                {"label": "Dekorasi Batu Giok", "value": "971912"},
                {"label": "Batu Giok Setengah Jadi", "value": "972040"}
            ]},
            {"label": "Kristal Alam", "value": "955400", "children": [
                {"label": "Kalung & Liontin Kristal Alam", "value": "959240"},
                {"label": "Cincin Kristal Alam", "value": "959368"},
                {"label": "Gelang & Gelang Kaki Kristal Alam", "value": "959496"},
                {"label": "Anting Kristal Alam", "value": "959624"},
                {"label": "Set Perhiasan Kristal Alam", "value": "959752"},
                {"label": "Aksesori Pakaian Kristal Alam", "value": "959880"},
                {"label": "Dekorasi Kristal Alam", "value": "960008"},
                {"label": "Kristal Alam Setengah Jadi", "value": "960136"}
            ]},
            {"label": "Kristal Non-alam", "value": "961800", "children": [
                {"label": "Kalung & Liontin Kristal Non-alam", "value": "964872"},
                {"label": "Cincin Kristal Non-alam", "value": "965000"},
                {"label": "Gelang & Gelang Kaki Kristal Non-alam", "value": "965128"},
                {"label": "Anting Kristal Non-alam", "value": "965256"},
                {"label": "Set Perhiasan Kristal Non-alam", "value": "970888"},
                {"label": "Aksesori Pakaian Kristal Non-alam", "value": "971016"},
                {"label": "Dekorasi Kristal Non-alam", "value": "971144"},
                {"label": "Kristal Non-alam Setengah Jadi", "value": "971272"}
            ]},
            {"label": "Rubi, Safir & Zamrud", "value": "964104", "children": [
                {"label": "Kalung & Liontin Rubi, Safir & Zamrud", "value": "972168"},
                {"label": "Cincin Rubi, Safir & Zamrud", "value": "972296"},
                {"label": "Gelang & Gelang Kaki Rubi, Safir & Zamrud", "value": "972424"},
                {"label": "Anting Rubi, Safir & Zamrud", "value": "972552"},
                {"label": "Set Perhiasan Rubi, Safir & Zamrud", "value": "972680"},
                {"label": "Aksesori Pakaian Rubi, Safir & Zamrud", "value": "972808"},
                {"label": "Rubi, Safir & Zamrud Setengah Jadi", "value": "972936"}
            ]},
            {"label": "Batu Semimulia", "value": "964232", "children": [
                {"label": "Kalung & Liontin Batu Semimulia", "value": "973064"},
                {"label": "Cincin Batu Semimulia", "value": "973192"},
                {"label": "Gelang & Gelang Kaki Batu Semimulia", "value": "973320"},
                {"label": "Anting Batu Semimulia", "value": "973448"},
                {"label": "Set Perhiasan Batu Semimulia", "value": "973576"},
                {"label": "Aksesori Pakaian Batu Semimulia", "value": "973704"},
                {"label": "Batu Semimulia Setengah Jadi", "value": "973832"}
            ]},
            {"label": "Mutiara", "value": "964488", "children": [
                {"label": "Kalung & Liontin Mutiara", "value": "974600"},
                {"label": "Cincin Mutiara", "value": "974728"},
                {"label": "Gelang & Gelang Kaki Mutiara", "value": "974856"},
                {"label": "Anting Mutiara", "value": "974984"},
                {"label": "Set Perhiasan Mutiara", "value": "975112"},
                {"label": "Aksesori Pakaian Mutiara", "value": "975240"},
                {"label": "Dekorasi Mutiara", "value": "975368"},
                {"label": "Mutiara Setengah Jadi", "value": "975496"}
            ]},
            {"label": "Batu Ambar", "value": "964616", "children": [
                {"label": "Kalung & Liontin Batu Ambar", "value": "975624"},
                {"label": "Cincin Batu Ambar", "value": "975752"},
                {"label": "Gelang & Gelang Kaki Batu Ambar", "value": "975880"},
                {"label": "Anting Batu Ambar", "value": "976008"},
                {"label": "Set Perhiasan Batu Ambar", "value": "976136"},
                {"label": "Aksesori Pakaian Batu Ambar", "value": "976264"},
                {"label": "Dekorasi Batu Ambar", "value": "976392"},
                {"label": "Batu Ambar Setengah Jadi", "value": "976520"}
            ]},
            {"label": "Mellite", "value": "964744", "children": [
                {"label": "Kalung & Liontin Mellite", "value": "976648"},
                {"label": "Cincin Mellite", "value": "976776"},
                {"label": "Gelang & Gelang Kaki Mellite", "value": "976904"},
                {"label": "Anting Mellite", "value": "977032"},
                {"label": "Set Perhiasan Mellite", "value": "977160"},
                {"label": "Aksesori Pakaian Mellite", "value": "977288"},
                {"label": "Dekorasi Mellite", "value": "977416"},
                {"label": "Mellite Setengah Jadi", "value": "977544"}
            ]}
        ]
    },
    {
        "label": "Buku, Majalah, & Audio", "value": "26",
        "children": [
            {"label": "Sastra & Seni", "value": "986760", "children": [
                {"label": "Fotografi & Video", "value": "926344"},
                {"label": "Biografi & Memoar ", "value": "926472"},
                {"label": "Sastra", "value": "926856"},
                {"label": "Fiksi", "value": "987016"},
                {"label": "Seni Pertunjukan", "value": "987144"},
                {"label": "Musik", "value": "987400"},
                {"label": "Seni Film & Televisi", "value": "989064"},
                {"label": "Melukis & Desain", "value": "989192"}
            ]},
            {"label": "Ekonomi & Manajemen", "value": "989320", "children": [
                {"label": "Bisnis & Manajemen", "value": "926600"},
                {"label": "Ekonomi", "value": "989448"},
                {"label": "Keuangan & Investasi", "value": "989576"}
            ]},
            {"label": "Buku Anak & Bayi", "value": "989704", "children": [
                {"label": "Sastra & Seni untuk Anak", "value": "926728"},
                {"label": "Buku Pembelajaran Anak Usia Dini & Bayi", "value": "989832"},
                {"label": "Buku Aktivitas", "value": "989960"},
                {"label": "Buku Bergambar", "value": "990088"},
                {"label": "Kemanusiaan & Ilmu Sosial untuk Anak", "value": "997128"},
                {"label": "Sains & Teknologi untuk Anak", "value": "997256"}
            ]},
            {"label": "Edukasi & Sekolah", "value": "992904", "children": [
                {"label": "Buku Pelajaran", "value": "926984"},
                {"label": "Bahasa & Kamus", "value": "929160"},
                {"label": "Buku Konseling", "value": "993032"}
            ]},
            {"label": "Kemanusiaan & Ilmu Sosial", "value": "927112", "children": [
                {"label": "Psikologi & Hubungan", "value": "927496"},
                {"label": "Agama & Filsafat", "value": "927624"},
                {"label": "Politik, Hukum & Ilmu Sosial", "value": "927752"},
                {"label": "Sejarah & Budaya", "value": "928008"},
                {"label": "Karier & Self-Help ", "value": "928136"},
                {"label": "Pengasuhan & Keluarga", "value": "928264"}
            ]},
            {"label": "Ilmu & Teknologi", "value": "990216", "children": [
                {"label": "Ilmu Hayati", "value": "927880"},
                {"label": "Medis", "value": "928904"},
                {"label": "Komputer & Jaringan", "value": "929544"},
                {"label": "Arsitektur", "value": "990856"},
                {"label": "Pertanian, Perhutanan & Perikanan", "value": "991112"},
                {"label": "Teknologi Industri", "value": "991240"}
            ]},
            {"label": "Gaya Hidup & Hobi", "value": "992392", "children": [
                {"label": "Resep & Memasak", "value": "928392"},
                {"label": "Kerajinan & DIY", "value": "928520"},
                {"label": "Kesehatan, Kebugaran & Diet", "value": "928648"},
                {"label": "Perjalanan & Peta", "value": "929032"},
                {"label": "Komik & Manga", "value": "929288"},
                {"label": "Horoskop", "value": "929416"},
                {"label": "Mode & Kecantikan", "value": "992520"},
                {"label": "Pendidikan Persalinan & Antenatal", "value": "992648"},
                {"label": "Olahraga & Kebugaran", "value": "992776"}
            ]},
            {"label": "Majalah & Surat Kabar", "value": "985736", "children": [
                {"label": "Bisnis", "value": "985864"},
                {"label": "Gaya hidup", "value": "986120"},
                {"label": "Fashion", "value": "986376"},
                {"label": "Remaja", "value": "986632"}
            ]},
            {"label": "Video & Musik", "value": "997384", "children": [
                {"label": "Kaset", "value": "997512"},
                {"label": "CD & DVD", "value": "997640"},
                {"label": "Vinil", "value": "997768"}
            ]}
        ]
    },
    {
        "label": "Bayi & Persalinan", "value": "18",
        "children": [
            {"label": "Perawatan & Kesehatan Bayi", "value": "879112", "children": [
                {"label": "Perawatan Kulit Bayi", "value": "602296"},
                {"label": "Perawatan Rambut & Sabun", "value": "602317"},
                {"label": "Pemangkas Rambut Bayi", "value": "602608"},
                {"label": "Pengering Rambut Bayi", "value": "602622"},
                {"label": "Pensanitasi Tangan Bayi", "value": "602672"},
                {"label": "Deterjen", "value": "602673"},
                {"label": "Perawatan Hidung & Mulut", "value": "602676"},
                {"label": "Sterilisasi Pakaian Bayi", "value": "602678"},
                {"label": "Dispenser Obat", "value": "818832"},
                {"label": "Timbangan", "value": "819088"},
                {"label": "Alat Pengukur Tinggi & Keliling", "value": "819472"},
                {"label": "Pembasmi Serangga & Hama", "value": "842640"},
                {"label": "Dot, Teether, & Mainan Kunyah Tumbuh Gigi", "value": "891912"},
                {"label": "Bak Mandi Bayi & Kursi Mandi", "value": "892168"},
                {"label": "Handuk & Topi Mandi", "value": "892296"},
                {"label": "Perlengkapan Mandi Bayi", "value": "892424"},
                {"label": "Wewangian", "value": "892552"},
                {"label": "Alat Perawatan Bayi", "value": "892680"},
                {"label": "Tisu Basah & Dudukan", "value": "892808"},
                {"label": "Popok", "value": "929672"},
                {"label": "Vitamin & Suplemen Bayi", "value": "947592"},
                {"label": "Pencetak Bentuk Tangan & Kaki Bayi", "value": "997896"}
            ]},
            {"label": "Aksesori Fashion Bayi", "value": "961928", "children": [
                {"label": "Perhiasan Kostum Bayi", "value": "602301"},
                {"label": "Kacamata hitam", "value": "817424"},
                {"label": "Celemek Makan & Lap Liur Bayi", "value": "890760"},
                {"label": "Sarung Tangan Bayi", "value": "962056"},
                {"label": "Syal Bayi", "value": "962184"},
                {"label": "Topi & Tutup Kepala Bayi", "value": "962312"},
                {"label": "Penutup Telinga Bayi", "value": "962440"},
                {"label": "Masker Wajah Bayi", "value": "962568"},
                {"label": "Aksesori Rambut Bayi", "value": "962696"},
                {"label": "Set Kado", "value": "998536"},
                {"label": "Tas Keperluan Bayi", "value": "998920"}
            ]},
            {"label": "Keselamatan Bayi", "value": "878600", "children": [
                {"label": "Kunci & Tali Pengaman", "value": "602532"},
                {"label": "Perlindungan Sengatan Listrik", "value": "602533"},
                {"label": "Pelindung Tepi & Sudut", "value": "602534"},
                {"label": "Pembatas & Pelindung Tempat Tidur", "value": "602536"},
                {"label": "Monitor", "value": "602538"},
                {"label": "Kelambu Nyamuk", "value": "891144"},
                {"label": "Gerbang & Pintu", "value": "891272"}
            ]},
            {"label": "Nursing & Pemberian Makan", "value": "877832", "children": [
                {"label": "Pengolah Makanan", "value": "602707"},
                {"label": "Botol Bayi & Aksesorinya", "value": "700704"},
                {"label": "Peralatan Bayi", "value": "700707"},
                {"label": "Pembersih Botol Bayi", "value": "819728"},
                {"label": "Kotak dan Rak Pengering Botol Bayi", "value": "842896"},
                {"label": "Penghangat & Pendingin & Pensteril Botol Bayi", "value": "890376"},
                {"label": "Bantalan Payudara ", "value": "890504"},
                {"label": "Selimut Nursing", "value": "890632"},
                {"label": "Dot", "value": "890888"},
                {"label": "Pompa ASI & Aksesorinya", "value": "933640"},
                {"label": "Penyimpanan & Penataan Susu Formula & Susu", "value": "962952"},
                {"label": "Bantal Menyusui", "value": "998024"}
            ]},
            {"label": "Furnitur Bayi", "value": "878216", "children": [
                {"label": "Selimut Bayi/Selimut Pembungkus", "value": "602734"},
                {"label": "Bouncer, Jumper, & Ayunan", "value": "602760"},
                {"label": "Dipan & Tempat Tidur", "value": "602761"},
                {"label": "Kursi Bayi", "value": "700706"},
                {"label": "Baby Walker", "value": "891016"},
                {"label": "Kursi Pelatihan Toilet & Kursi Toilet", "value": "893448"},
                {"label": "Meja untuk Mengganti Popok", "value": "998280"},
                {"label": "Meja Bayi", "value": "998408"}
            ]},
            {"label": "Pakaian & Sepatu Bayi", "value": "877320", "children": [
                {"label": "Sepatu", "value": "602787"},
                {"label": "Bodysuit & One-piece", "value": "700694"},
                {"label": "Celana Pof, Pelapis Popok, & Pakaian Dalam", "value": "817552"},
                {"label": "Hoodie & Pakaian Olahraga", "value": "817680"},
                {"label": "Jumper", "value": "817808"},
                {"label": "Baju Renang", "value": "888456"},
                {"label": "Kaus Kaki & Stoking", "value": "888584"},
                {"label": "Bawahan", "value": "888712"},
                {"label": "Set Kado", "value": "888968"},
                {"label": "Gaun", "value": "889096"},
                {"label": "Atasan", "value": "889224"},
                {"label": "Jaket & Mantel", "value": "889352"},
                {"label": "Baju Tidur", "value": "889480"},
                {"label": "Kostum", "value": "998152"}
            ]},
            {"label": "Perlengkapan Bayi untuk Travel", "value": "877576", "children": [
                {"label": "Kereta Bayi dan Kursi Dorong", "value": "700705"},
                {"label": "Gendongan Bayi", "value": "889608"},
                {"label": "Aksesoris Kursi Dorong", "value": "889736"},
                {"label": "Baby Seat untuk Kendaraan", "value": "889864"},
                {"label": "Aksesoris Baby Seat untuk Kendaraan", "value": "889992"},
                {"label": "Nappy Bag", "value": "890120"},
                {"label": "Harness & Rein Anak", "value": "890248"},
                {"label": "Sabuk Pengaman & Aksesorinya", "value": "998792"}
            ]},
            {"label": "Perlengkapan Kehamilan", "value": "880008", "children": [
                {"label": "Pakaian Dalam Bersalin", "value": "700710"},
                {"label": "Pakaian & Aksesori Ibu Hamil dan Menyusui", "value": "700718"},
                {"label": "Alat Pemantau Kehamilan", "value": "819600"},
                {"label": "Pakaian Nursing", "value": "892936"},
                {"label": "Bantal Bersalin", "value": "893064"},
                {"label": "Sabuk Pendukung Kehamilan", "value": "893192"},
                {"label": "Perawatan Kulit Bersalin", "value": "893320"},
                {"label": "Vitamin & Suplemen Bersalin", "value": "947720"},
                {"label": "Sabuk Pengaman untuk Ibu Hamil & Aksesorinya", "value": "998664"},
                {"label": "Milk Formula for Pregnant & Lactating Women", "value": "855056"}
            ]},
            {"label": "Mainan Bayi", "value": "878984", "children": [
                {"label": "Cermin", "value": "817936"},
                {"label": "Bola", "value": "818064"},
                {"label": "Kursi Pengaman Anak & Mainan Kereta Dorong", "value": "818192"},
                {"label": "Papan Panjat dalam Ruang & Rumah-rumahan", "value": "818448"},
                {"label": "Mainan Elektronik & Remote Control untuk Bayi", "value": "818576"},
                {"label": "Mainan Rumah-rumahan Bayi", "value": "818704"},
                {"label": "Mainan Patung & Model", "value": "819856"},
                {"label": "Playgym & Playmat", "value": "891400"},
                {"label": "Playpen", "value": "891528"},
                {"label": "Mainan Mandi", "value": "891656"},
                {"label": "Mainan Bersuara untuk Bayi", "value": "891784"},
                {"label": "Mainan Edukasi Usia Dini & Mainan Pintar", "value": "892040"},
                {"label": "Olahraga & Outdoor Play Bayi", "value": "960904"},
                {"label": "Boneka & Mainan Berisi Busa", "value": "961160"},
                {"label": "Mainan Roly-Poly", "value": "961288"},
                {"label": "Kuda & Hewan Ayun", "value": "961416"},
                {"label": "Set Kado", "value": "961544"}
            ]},
            {"label": "Susu Formula & Makanan Bayi", "value": "879496", "children": [
                {"label": "Minuman", "value": "819344"},
                {"label": "Susu Formula Bayi", "value": "843024"},
                {"label": "Susu Formula Pertumbuhan", "value": "933768"},
                {"label": "Makanan Bayi, Pure & Sereal", "value": "933896"},
                {"label": "Makanan Ringan", "value": "934024"}
            ]}
        ]
    },
    {
        "label": "Furnitur", "value": "20",
        "children": [
            {"label": "Furnitur Indoor", "value": "871048", "children": [
                {"label": "Sofa", "value": "604468"},
                {"label": "Lemari/Rak", "value": "604497"},
                {"label": "Sekat Ruangan", "value": "806800"},
                {"label": "Meja Rias", "value": "806928"},
                {"label": "Rak Mantel", "value": "807056"},
                {"label": "Meja & Desk", "value": "875912"},
                {"label": "Kursi", "value": "876040"},
                {"label": "Stool & Bangku", "value": "876168"},
                {"label": "Tempat Tidur", "value": "876296"},
                {"label": "Kasur", "value": "876424"},
                {"label": "Lemari & Kabinet", "value": "876680"},
                {"label": "Lemari pakaian", "value": "876936"},
                {"label": "Set Furnitur Indoor", "value": "877064"},
                {"label": "Rak TV & Meja Samping Tempat Tidur", "value": "877192"},
                {"label": "Rangka & Kepala Tempat Tidur", "value": "979720"}
            ]},
            {"label": "Furnitur Outdoor", "value": "871176", "children": [
                {"label": "Sofa Outdoor", "value": "877448"},
                {"label": "Kursi Outdoor", "value": "877704"},
                {"label": "Payung Teras ", "value": "877960"},
                {"label": "Ayunan Teras", "value": "878088"},
                {"label": "Set Furnitur Outdoor", "value": "878344"},
                {"label": "Meja Outdoor", "value": "878472"},
                {"label": "Stool & Bangku", "value": "878728"},
                {"label": "Langgayan Outdoor", "value": "878856"}
            ]},
            {"label": "Furnitur Anak", "value": "871304", "children": [
                {"label": "Tempat Tidur", "value": "879240"},
                {"label": "Sofa", "value": "879368"},
                {"label": "Kursi", "value": "879624"},
                {"label": "Stool & Bangku", "value": "879752"},
                {"label": "Lemari", "value": "879880"},
                {"label": "Set Furnitur", "value": "880136"},
                {"label": "Meja & Desk", "value": "880264"},
                {"label": "Lemari pakaian", "value": "880392"},
                {"label": "Meja Samping Tempat Tidur", "value": "880520"},
                {"label": "Kasur", "value": "880648"},
                {"label": "Langgayan & Rak", "value": "933512"}
            ]},
            {"label": "Furnitur Komersial", "value": "871432", "children": [
                {"label": "Furnitur Salon", "value": "880904"},
                {"label": "Furnitur Hotel", "value": "881032"},
                {"label": "Furnitur Sekolah", "value": "881160"},
                {"label": "Furnitur Restoran", "value": "881288"},
                {"label": "Furnitur Kantor", "value": "881416"}
            ]}
        ]
    },
    {
        "label": "Fashion Anak", "value": "4",
        "children": [
            {"label": "Pakaian Anak Laki-Laki", "value": "802312", "children": [
                {"label": "Kostum & Aksesori", "value": "802440"},
                {"label": "Pakaian Dalam", "value": "802568"},
                {"label": "Pakaian tidur", "value": "802696"},
                {"label": "Atasan", "value": "802952"},
                {"label": "Mantel & Jaket", "value": "803080"},
                {"label": "Bawahan", "value": "803208"},
                {"label": "Setelan Resmi & Setelan", "value": "803336"},
                {"label": "Kaus kaki", "value": "803464"},
                {"label": "Seragam Sekolah", "value": "803600"}
            ]},
            {"label": "Pakaian Anak Perempuan", "value": "803592", "children": [
                {"label": "Seragam Sekolah", "value": "803472"},
                {"label": "Kostum & Aksesori", "value": "803720"},
                {"label": "Pakaian Dalam", "value": "803848"},
                {"label": "Pakaian tidur", "value": "803976"},
                {"label": "Atasan", "value": "804232"},
                {"label": "Mantel & Jaket", "value": "804360"},
                {"label": "Bawahan", "value": "804488"},
                {"label": "Setelan Resmi & Setelan", "value": "804616"},
                {"label": "Gaun", "value": "804744"},
                {"label": "Rok", "value": "804872"},
                {"label": "Kaus kaki", "value": "805000"},
                {"label": "Celana ketat", "value": "960264"}
            ]},
            {"label": "Alas Kaki Anak Laki-Laki", "value": "805128", "children": [
                {"label": "Sepatu Boot", "value": "805256"},
                {"label": "Sandal", "value": "805384"},
                {"label": "Trainer", "value": "805512"},
                {"label": "Selop", "value": "805640"},
                {"label": "Sepatu Formal", "value": "805768"},
                {"label": "Sepatu Flat", "value": "805896"}
            ]},
            {"label": "Alas Kaki Anak Perempuan", "value": "806024", "children": [
                {"label": "Sepatu Boot", "value": "806152"},
                {"label": "Sandal & Sandal Jepit", "value": "806280"},
                {"label": "Trainer", "value": "806408"},
                {"label": "Selop", "value": "806536"},
                {"label": "Sepatu Flat", "value": "806664"}
            ]},
            {"label": "Aksesori Fashion Anak", "value": "806792", "children": [
                {"label": "Tas & Koper", "value": "806920"},
                {"label": "Topi Anak", "value": "807048"},
                {"label": "Kacamata", "value": "807176"},
                {"label": "Aksesoris Rambut", "value": "807304"},
                {"label": "Sarung Tangan", "value": "807432"},
                {"label": "Sabuk", "value": "807560"},
                {"label": "Syal & Selendang Anak", "value": "807688"},
                {"label": "Jam Tangan", "value": "807816"},
                {"label": "Perhiasan & Aksesori Kostum Anak-Anak", "value": "807944"},
                {"label": "Alat Penutup Telinga", "value": "808072"},
                {"label": "Dasi & Dasi Kupu-Kupu", "value": "954760"},
                {"label": "Masker Wajah", "value": "960520"}
            ]}
        ]
    },
    {
        "label": "Fashion Muslim", "value": "5",
        "children": [
            {"label": "Hijab", "value": "601304", "children": [
                {"label": "Ciput", "value": "601305"},
                {"label": "Hijab Instan", "value": "601306"},
                {"label": "Hijab Persegi", "value": "601307"},
                {"label": "Syal Pasmina", "value": "601308"},
                {"label": "Khimar", "value": "601309"},
                {"label": "Cadar", "value": "803984"}
            ]},
            {"label": "Busana Muslim Wanita", "value": "601310", "children": [
                {"label": "Tunik", "value": "601313"},
                {"label": "Kemeja Kasual", "value": "601314"},
                {"label": "Rok", "value": "601316"},
                {"label": "Celana Kulot dan Palazzo", "value": "601317"},
                {"label": "Legging", "value": "601319"},
                {"label": "Kaftan", "value": "601322"},
                {"label": "Abaya", "value": "601323"},
                {"label": "Jumpsuit", "value": "601324"},
                {"label": "Setelan Pakaian", "value": "935688"},
                {"label": "Gaun", "value": "935816"},
                {"label": "Jubah", "value": "935944"},
                {"label": "Gamis", "value": "936072"},
                {"label": "Setelan Pakaian Pasangan", "value": "996616"},
                {"label": "Setelan Pakaian Keluarga", "value": "996744"},
                {"label": "Turtlenecks & Inners", "value": "854800"}
            ]},
            {"label": "Pakaian Muslim Pria", "value": "601325", "children": [
                {"label": "Atasan", "value": "601326"},
                {"label": "Jubah", "value": "601327"},
                {"label": "Celana Panjang", "value": "601329"}
            ]},
            {"label": "Pakaian & Alat Ibadah", "value": "601348", "children": [
                {"label": "Sarung", "value": "601330"},
                {"label": "Peci", "value": "601349"},
                {"label": "Perangkat Sholat", "value": "601350"},
                {"label": "Sajadah", "value": "601351"},
                {"label": "Tasbih", "value": "813072"},
                {"label": "Mukena", "value": "838792"},
                {"label": "Rompi Sholat", "value": "839688"}
            ]},
            {"label": "Outer", "value": "601331", "children": [
                {"label": "Waistcoat", "value": "601332"},
                {"label": "Kardigan", "value": "601333"},
                {"label": "Jaket", "value": "601334"},
                {"label": "Mantel", "value": "601335"},
                {"label": "Jas Hujan", "value": "996872"}
            ]},
            {"label": "Pakaian Muslim Anak", "value": "601339", "children": [
                {"label": "Hijab Anak", "value": "601340"},
                {"label": "Pakaian Muslim Anak Perempuan", "value": "601341"},
                {"label": "Pakaian Muslim Anak Laki-Laki", "value": "601342"}
            ]},
            {"label": "Aksesoris Islami", "value": "601343", "children": [
                {"label": "Pin Hijab", "value": "601344"},
                {"label": "Handsock", "value": "601345"},
                {"label": "Kaus kaki", "value": "601346"}
            ]},
            {"label": "Pakaian Olahraga Muslim", "value": "838920", "children": [
                {"label": "Pakaian Renang Muslim", "value": "601347"},
                {"label": "Baju Olahraga Muslim", "value": "839048"}
            ]},
            {"label": "Perlengkapan Umroh", "value": "839176", "children": [
                {"label": "Set Kemeja Putih", "value": "839304"},
                {"label": "Paket Umroh", "value": "839432"},
                {"label": "Pakaian Ihram", "value": "839560"}
            ]}
        ]
    },
    {
        "label": "Pre-Owned", "value": "31",
        "children": [
            {"label": "Collectible Trading Cards", "value": "856976", "children": [
                {"label": "Non-Sports Trading Cards Graded Singles", "value": "857872"},
                {"label": "Trading Cards Accessories", "value": "858000"},
                {"label": "Sports Trading Cards Graded Singles", "value": "858128"},
                {"label": "Non-Sports Trading Card Packs & Boxes", "value": "863376"},
                {"label": "Non-Sports Trading Card Breaks", "value": "863504"},
                {"label": "Sports Trading Cards Packs & Boxes", "value": "863632"},
                {"label": "Sports Trading Card Breaks", "value": "863760"}
            ]},
            {"label": "Fashion Accessories", "value": "857104", "children": [
                {"label": "Belts", "value": "858256"},
                {"label": "Gloves", "value": "858384"},
                {"label": "Hats", "value": "858512"},
                {"label": "Costume Jewellery & Accessories", "value": "858640"},
                {"label": "Frames & Glasses", "value": "858768"},
                {"label": "Sunglasses", "value": "858896"},
                {"label": "Hair Accessories", "value": "859024"}
            ]},
            {"label": "Watches", "value": "865296", "children": [
                {"label": "Smart Watches ", "value": "859152"},
                {"label": "Quartz Watches", "value": "865424"},
                {"label": "Manual Watches", "value": "865552"},
                {"label": "Automatic Watches", "value": "865680"},
                {"label": "Watch Accessories", "value": "865808"}
            ]},
            {"label": "Luggage & Travel", "value": "864656", "children": [
                {"label": "Luggage", "value": "859280"},
                {"label": "Luggage Accessories", "value": "859408"},
                {"label": "Travel Bags", "value": "864784"},
                {"label": "Toiletry Bags", "value": "864912"}
            ]},
            {"label": "Bags", "value": "857232", "children": [
                {"label": "Bag Accessories", "value": "859536"},
                {"label": "Messenger Bags", "value": "859664"},
                {"label": "Shoulder Bags", "value": "859792"},
                {"label": "Professional & Technology Bags", "value": "859920"},
                {"label": "Small Leather Goods", "value": "860048"},
                {"label": "Crossbody Bags", "value": "863888"},
                {"label": "Mini Bags", "value": "864016"},
                {"label": "Tote Bags", "value": "864144"},
                {"label": "Clutches & Wristlets", "value": "864272"},
                {"label": "Backpacks", "value": "864400"},
                {"label": "Belt Bags", "value": "864528"},
                {"label": "Top Handle Bags", "value": "871440"},
                {"label": "Bucket Bags", "value": "871568"}
            ]},
            {"label": "Menswear", "value": "857488", "children": [
                {"label": "Men's Bottoms", "value": "860176"},
                {"label": "Men's Suits & Overalls", "value": "860304"},
                {"label": "Men's Tops", "value": "860432"},
                {"label": "Men's Swimwear & Beachwear", "value": "860560"},
                {"label": "Men's Jackets & Coats", "value": "860688"},
                {"label": "Men's Jumpers, Cardigans & Hoodies", "value": "860816"},
                {"label": "Men's Sportswear", "value": "860944"}
            ]},
            {"label": "Footwear", "value": "857360", "children": [
                {"label": "Men's Dress Shoes", "value": "861072"},
                {"label": "High Heels", "value": "861200"},
                {"label": "Sneakers", "value": "861328"},
                {"label": "Women's Flats", "value": "861456"},
                {"label": "Footwear Accessories", "value": "861584"},
                {"label": "Sandals", "value": "865040"},
                {"label": "Boots", "value": "865168"}
            ]},
            {"label": "Womenswear", "value": "857616", "children": [
                {"label": "Women's Bottoms", "value": "861712"},
                {"label": "Women's Dresses", "value": "861840"},
                {"label": "Women's Suits & Overalls", "value": "861968"},
                {"label": "Women's Tops", "value": "862096"},
                {"label": "Women's Lingerie, Nightwear & Loungewear", "value": "862224"},
                {"label": "Women's Swimwear & Beachwear", "value": "862352"},
                {"label": "Women's Jackets & Coats", "value": "862480"},
                {"label": "Women's Jumpers, Cardigans & Hoodies", "value": "862608"},
                {"label": "Women's Sportswear", "value": "862736"}
            ]},
            {"label": "Refurbished Phones & Electronics", "value": "857744", "children": [
                {"label": "Mobile Phones", "value": "862864"},
                {"label": "Tablets", "value": "862992"}
            ]}
        ]
    },
    {
        "label": "Produk Virtual", "value": "27",
        "children": [
            {"label": "Telekomunikasi", "value": "996360", "children": [
                {"label": "Isi Ulang Paket Seluler", "value": "834440"},
                {"label": "Data Seluler", "value": "996104"}
            ]}
        ]
    }
]

# ==========================================
# 3. KELAS SCRAPER UTAMA
# ==========================================

class FastMossScraper:
    def __init__(self):
        self.base_url = "https://www.fastmoss.com/api/goods/saleRank"
        self.headers = HEADERS_CONFIG

    def get_best_sellers(self, page=1, pagesize=10, time_config=None, category_config=None):
        """
        Mengambil data produk terlaris.
        :param time_config: Dictionary berisi {'date_type', 'date_value'}
        :param category_config: Dictionary berisi {'l1_cid', 'l2_cid', 'l3_cid'}
        """
        params = {
            "page": page,
            "pagesize": pagesize,
            "order": "1,2", # Default sorting
            "region": "ID",
            "_time": int(time.time()),
            # Parameter Waktu
            "date_type": time_config['type'],
            "date_value": time_config['value']
        }

        # Menambahkan Kategori secara Dinamis
        if category_config:
            if category_config.get('l1'): params["l1_cid"] = category_config['l1']
            if category_config.get('l2'): params["l2_cid"] = category_config['l2']
            if category_config.get('l3'): params["l3_cid"] = category_config['l3']

        try:
            print(f"[*] Mengambil data Halaman {page}...")
            print(f"    URL Param: {params}")
            
            response = requests.get(self.base_url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data_json = response.json()
                if data_json.get("code") == 200:
                    return data_json.get("data", {}).get("rank_list", [])
                else:
                    print(f"[!] API Error Message: {data_json.get('msg')}")
                    return []
            else:
                print(f"[!] HTTP Error: {response.status_code}")
                return []
        except Exception as e:
            print(f"[!] Connection Error: {e}")
            return []

    def parse_products(self, products_list):
        parsed_data = []
        for item in products_list:
            shop_info = item.get("shop_info", {})
            
            # Membersihkan kategori menjadi string
            cat_list = item.get("all_category_name", [])
            cat_string = " > ".join(cat_list) if cat_list else "-"

            product_data = {
                "Judul Produk": item.get("title"),
                "Kategori Full": cat_string,
                "Harga Real": item.get("real_price"),
                "Total Terjual (Periode Ini)": item.get("sold_count_show"),
                "Omzet (Periode Ini)": item.get("sale_amount_show"),
                "Total Terjual (Seumur Hidup)": item.get("total_sold_count_show"),
                "Total Omzet (Seumur Hidup)": item.get("total_sale_amount_show"),
                "Nama Toko": shop_info.get("name"),
                "ID Toko": shop_info.get("seller_id"),
                "Link Produk": item.get("detail_url"),
                "Growth Rate": item.get("sold_count_inc_rate_show"),
                "Tanggal Rilis": item.get("launch_time")
            }
            parsed_data.append(product_data)
        return parsed_data

# ==========================================
# 4. FUNGSI INTERAKSI USER (CLI MENU)
# ==========================================

def get_user_time_config():
    print("\n--- PILIH FILTER WAKTU ---")
    print("1. Harian (Daily)")
    print("2. Mingguan (Weekly)")
    print("3. Bulanan (Monthly)")
    
    choice = input("Masukkan pilihan (1/2/3): ")
    
    date_type = ""
    date_value = ""
    
    if choice == "1":
        date_type = "1"
        date_value = input("Masukkan Tanggal (Format YYYY-MM-DD, cth: 2025-12-10): ")
    elif choice == "2":
        date_type = "2"
        date_value = input("Masukkan Minggu (Format YYYY-WW, cth: 2025-49): ")
    elif choice == "3":
        date_type = "3"
        date_value = input("Masukkan Bulan (Format YYYY-MM, cth: 2025-11): ")
    else:
        print("Pilihan salah, default ke Harian hari ini.")
        date_type = "1"
        date_value = datetime.now().strftime("%Y-%m-%d")
        
    return {"type": date_type, "value": date_value}

def select_from_list(items, level_name):
    print(f"\n--- PILIH KATEGORI {level_name} ---")
    print("0. Lewati / Ambil Semua di level ini")
    for idx, item in enumerate(items):
        print(f"{idx + 1}. {item['label']}")
    
    try:
        choice = int(input(f"Pilih nomor {level_name}: "))
        if choice == 0:
            return None, None
        selected_item = items[choice - 1]
        return selected_item, selected_item.get('children', None)
    except:
        return None, None

def get_user_category_config():
    cat_config = {"l1": None, "l2": None, "l3": None}
    current_label = "Semua Kategori"
    
    # Level 1
    selected_l1, children_l1 = select_from_list(CATEGORY_TREE, "LEVEL 1 (UTAMA)")
    if selected_l1:
        cat_config['l1'] = selected_l1['value']
        current_label = selected_l1['label']
        
        # Level 2 (Jika ada children)
        if children_l1:
            selected_l2, children_l2 = select_from_list(children_l1, "LEVEL 2 (SUB)")
            if selected_l2:
                cat_config['l2'] = selected_l2['value']
                current_label += f" > {selected_l2['label']}"
                
                # Level 3 (Jika ada children)
                if children_l2:
                    selected_l3, _ = select_from_list(children_l2, "LEVEL 3 (SUB-SUB)")
                    if selected_l3:
                        cat_config['l3'] = selected_l3['value']
                        current_label += f" > {selected_l3['label']}"
    
    print(f"\n[INFO] Kategori Terpilih: {current_label}")
    print(f"[INFO] Kode CID: {cat_config}")
    return cat_config

# ==========================================
# 5. EKSEKUSI PROGRAM UTAMA
# ==========================================

if __name__ == "__main__":
    print("=========================================")
    print("   FASTMOSS ULTIMATE FLEXIBLE SCRAPER    ")
    print("=========================================\n")
    
    # 1. Setup Scraper
    scraper = FastMossScraper()
    
    # 2. Input User: Waktu
    time_cfg = get_user_time_config()
    
    # 3. Input User: Kategori
    cat_cfg = get_user_category_config()
    
    # 4. Input User: Jumlah Halaman
    try:
        max_pages = int(input("\nBerapa halaman data yang ingin diambil? (per halaman 10 data): "))
    except:
        max_pages = 1
        
    all_products = []
    
    # 5. Mulai Scraping Loop
    print("\n[START] Memulai proses scraping...")
    for i in range(1, max_pages + 1):
        raw_data = scraper.get_best_sellers(page=i, time_config=time_cfg, category_config=cat_cfg)
        
        if raw_data:
            clean_data = scraper.parse_products(raw_data)
            all_products.extend(clean_data)
            print(f"   -> Berhasil mendapatkan {len(clean_data)} produk dari halaman {i}")
            
            # Jeda waktu 5 detik (Sesuai permintaan)
            if i < max_pages:
                print("   [WAIT] Menunggu 5 detik agar aman...")
                time.sleep(5)
        else:
            print("   [STOP] Tidak ada data ditemukan atau terjadi error.")
            break
            
    # 6. Simpan Hasil
    if all_products:
        df = pd.DataFrame(all_products)
        
        # Nama file dinamis
        time_str = time_cfg['value'].replace("-", "")
        cat_id_str = f"{cat_cfg['l1'] or 'All'}-{cat_cfg['l2'] or '0'}-{cat_cfg['l3'] or '0'}"
        filename = f"FastMoss_{time_str}_CID_{cat_id_str}.xlsx"
        
        print("\n=== PREVIEW DATA (3 Teratas) ===")
        print(df[["Judul Produk", "Kategori Full", "Total Terjual (Periode Ini)"]].head(3))
        
        df.to_excel(filename, index=False)
        print(f"\n[SUCCESS] Data berhasil disimpan ke: {filename}")
    else:
        print("\n[FAILED] Tidak ada data yang berhasil diambil.")