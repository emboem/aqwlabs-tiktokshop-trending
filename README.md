# FastMoss Lite v2

Aplikasi web untuk tim, untuk analisis **TikTok Shop** dengan data dari [FastMoss](https://www.fastmoss.com).
Isinya mengikuti menu FastMoss: produk, kreator, toko, LIVE, video, iklan, tren pasar, dan halaman detail
untuk tiap produk, toko, kreator, LIVE, dan video. Semua tabel bisa diekspor ke **Excel / CSV / PDF**.

> Aplikasi ini **tidak membuka data berbayar**. Yang tampil hanya data yang memang dibuka FastMoss
> untuk paket akun yang dipasang. Akun gratis cukup melihat 5 baris teratas dan sebagian bagian tampil
> "Terkunci". Kalau akun yang dipasang berlangganan, datanya otomatis tampil sesuai paket akun itu.

---

## Fitur

| Kelompok | Isi |
|---|---|
| **Tren Pasar** | Denyut Pasar, Panorama Kategori (produk terlaris/viral, sebaran harga, sub-kategori), Strategi Pemasaran |
| **Produk** | Cari Produk, Produk Terlaris, Produk Baru Laris, Produk Populer, Produk dari Video Viral |
| **Kreator** | Cari Kreator, Pertumbuhan Pengikut, Kreator Penjual Terlaris, Terverifikasi, Paling Disukai, Potensial |
| **Toko** | Cari Toko, Toko Terlaris, Toko Populer |
| **LIVE** | Cari Siaran LIVE, LIVE Terlaris, Produk Laris di LIVE, Kreator LIVE Terlaris |
| **Video** | Cari Video, Musik Populer, Hashtag Populer, Video AI Terlaris |
| **Iklan** | Cari Iklan, Iklan Seeding, Pengiklan Teratas, Wawasan Hashtag, Tren Kata Kunci, Tren Kategori Produk |
| **Agensi** | Peringkat Agensi (CAP), Cari Agensi |
| **Detail** | Produk · Toko · Kreator · LIVE · Video: ringkasan, grafik tren, tabel turunan (kreator, video, LIVE, produk serupa, dan lainnya) |

Fitur lain:
- **Lompat cepat**: tempel link FastMoss atau TikTok, ID, `@username`, atau kata kunci di kotak atas, lalu langsung masuk ke halaman yang sesuai.
- Filter lengkap per menu (rentang waktu harian/mingguan/bulanan/7/28/90 hari, kategori 3 tingkat, filter lanjutan) dan urutan sesuai FastMoss.
- Pilihan **negara** (Indonesia, Malaysia, Thailand, Vietnam, Filipina, AS, dan lainnya). Mata uang menyesuaikan.
- Mode **terang/gelap**, nyaman di HP.
- Ekspor **Excel / CSV / PDF** di setiap tabel.
- **Multi-akun**: pasang beberapa akun FastMoss (mis. gratis + berlangganan), tiap orang memilih akunnya sendiri.
- Login tim dengan kata sandi, dan kata sandi admin terpisah untuk mengganti cookie.

## Struktur

```
app/
  fastmoss/signer.py   tanda tangan fm-sign / fm-sig (Python murni, tanpa browser)
  fastmoss/cookies.py  baca/tulis file cookie (format mentah, header, atau cURL)
  fastmoss/client.py   klien HTTP: jeda antar-request, retry, cache, deteksi "terkunci"
  accounts.py          multi-akun: satu file cookie = satu akun, pilihan akun per request
  catalog.py           definisi semua menu daftar (kolom, filter, urutan)
  details.py           definisi halaman detail produk/toko/kreator/LIVE/video
  market.py            halaman Tren Pasar
  routes/api.py        API JSON untuk halaman web
  routes/export.py     ekspor Excel/CSV/PDF
  auth.py, settings.py login tim & konfigurasi
web/                   tampilan (HTML + CSS + JS, tanpa build)
config/cookies_akun_N.txt  ← TEMPAT COOKIE, satu file per akun (tidak ikut git)
tests/                 pytest
```

## Menjalankan di komputer sendiri

1. Pasang Python 3.10 atau lebih baru.
2. Isi cookie akun (lihat bagian *Akun & cookie FastMoss*).
3. Klik dua kali **`run.bat`**, atau jalankan:
   ```bash
   pip install -r requirements.txt
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
4. Browser terbuka otomatis ke <http://localhost:8000>. Alamat `0.0.0.0:8000` yang muncul di log server **bukan** alamat untuk dibuka di browser.

## Akun & cookie FastMoss (multi-akun)

Satu akun FastMoss = **satu file** di folder `config/`:

```
config/cookies_akun_1.txt   ← mis. akun gratis
config/cookies_akun_2.txt   ← mis. akun berlangganan
config/cookies_akun_3.txt   ← dst. (nomor bebas, urut dari kecil)
```

Baris `# nama: ...` di dalam file adalah nama akun yang tampil di aplikasi. Tiap akun punya cache dan status paket
sendiri, jadi data akun gratis dan akun berlangganan tidak tercampur.

**Memilih akun.** Kalau ada 2 akun atau lebih, di bilah atas muncul pilihan akun. Setiap orang memilih sendiri,
dan pilihannya disimpan di browser masing-masing, jadi tidak mengubah pilihan anggota tim lain.
Yang belum memilih memakai `FM_DEFAULT_ACCOUNT` (atau akun bernomor terkecil).

**Mengisi / mengganti cookie** (dua cara):

- **A. Lewat aplikasi (paling mudah).** Buka **Pengaturan & Cookie** → pada tabel akun klik **Isi cookie** / **Ganti cookie**
  (atau klik label "Belum ada cookie" / "Cookie bermasalah" di bilah atas) → tempel teksnya **apa adanya**, klik **Pilih file…**,
  atau seret file .txt ke kotak → **Simpan & uji**. Sebelum disimpan, aplikasi menampilkan format yang terbaca, jumlah cookie,
  dan apakah sesi login (`fd_tk`) ada. Tombol **+ Tambah slot akun** membuat file akun baru. Butuh kata sandi admin kalau login diaktifkan.
- **B. Edit file.** Buka `config/cookies_akun_N.txt` (atau salin `config/cookies.example.txt` dengan nama itu), lalu tempel
  di bawah baris `# nama:` salah satu format ini:
  - isi cookie mentah: `fd_tk=...; NEXT_LOCALE=id; ...`
  - satu baris header: `Cookie: fd_tk=...; ...`
  - perintah cURL utuh — "Copy as cURL (cmd)" Windows yang penuh tanda `^` maupun "(bash)", tempel apa adanya
  - juga dikenali: "Copy as PowerShell", "Copy as fetch (Node.js)", ekspor JSON ekstensi cookie, tabel cookie DevTools

Cara mengambil cookie: login di fastmoss.com dengan akun yang mau dipasang, buka DevTools (F12) lalu tab **Network**,
muat ulang halaman, klik kanan salah satu request `/api/...`, lalu pilih **Copy → Copy as cURL**.

Perubahan berlaku **tanpa restart**. File dibaca ulang setiap kali isinya berubah.
Semua `config/cookies*.txt` sudah masuk `.gitignore` (kecuali contoh), jadi tidak akan ikut ter-commit.
Nilai cookie tidak pernah dikirim ke browser; halaman Pengaturan hanya menampilkan statusnya.

Dari versi sebelumnya (satu file `config/cookies.txt`): saat aplikasi dijalankan, file itu otomatis dipindah
menjadi `config/cookies_akun_1.txt`.

Kalau muncul pesan *"cookie kedaluwarsa / belum login"*, cookie akun itu perlu diganti dengan yang baru.

## Menyebarkan ke tim (deploy)

1. Salin `.env.example` menjadi `.env`, lalu **wajib** isi:
   - `APP_PASSWORD`: kata sandi tim untuk masuk aplikasi
   - `ADMIN_PASSWORD`: kata sandi untuk mengganti cookie (opsional; kalau kosong, sama dengan `APP_PASSWORD`)
   - `SECRET_KEY`: string acak yang panjang, misalnya hasil `python -c "import secrets;print(secrets.token_urlsafe(48))"`
2. Jalankan dengan **Docker**:
   ```bash
   docker build -t fastmoss-lite .
   docker run -d --name fastmoss-lite -p 8000:8000 --env-file .env \
     -v $(pwd)/config:/app/config fastmoss-lite
   ```
   Folder `config/` dipasang sebagai volume, jadi semua file akun tetap ada saat container diperbarui
   dan tetap bisa diganti / ditambah dari halaman Pengaturan.
3. Pasang di belakang **reverse proxy HTTPS** (Caddy, Nginx, atau Cloudflare Tunnel). Jangan buka port 8000 langsung ke internet tanpa HTTPS.
4. Cek kesehatan server: `GET /healthz`.

Pengaturan lain (opsional, lewat `.env`): `FM_REGION`, `FM_MIN_INTERVAL` (jeda antar-request, detik),
`FM_CACHE_TTL` (lama cache, detik), `FM_FREE_ROW_LIMIT`, `FM_EXPORT_MAX_ROWS`,
`FM_COOKIE_DIR` (folder file akun, bawaan `config`), `FM_DEFAULT_ACCOUNT` (akun bawaan, mis. `1`).

## Kebijakan data terkunci

FastMoss membalas data yang dikunci paket dengan beberapa cara. Semuanya **dibuang**, tidak ditampilkan:

| Balasan FastMoss | Arti | Yang dilakukan aplikasi |
|---|---|---|
| `MAG_AUTH_*` (mis. 3016, 3024) | terkunci paket, kadang disertai data contoh palsu | tampil "Terkunci paket FastMoss" |
| `code 200` + `is_mock = 1` | data contoh/palsu | tampil "Terkunci" (bukan data asli) |
| `MSG_30001` | belum login / cookie kedaluwarsa | minta ganti cookie |

Untuk akun gratis, aplikasi hanya meminta halaman 1 dan menampilkan 5 baris teratas, sama seperti tampilan FastMoss.
Data harian "kemarin" yang belum diperbarui FastMoss (biasanya sebelum siang) otomatis diganti ke hari sebelumnya, dan ada keterangannya di halaman.

## Pengembangan

```bash
pip install -r requirements.txt
python -m pytest -q
uvicorn app.main:app --reload --port 8000
```

Untuk menambah atau mengubah menu cukup edit `app/catalog.py`. Untuk halaman detail, edit `app/details.py`.
Tampilan web membaca definisi itu dari `/api/catalog`, jadi tidak perlu mengubah JS.
