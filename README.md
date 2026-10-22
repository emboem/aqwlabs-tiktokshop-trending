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
- Login tim dengan kata sandi, dan kata sandi admin terpisah untuk mengganti cookie.

## Struktur

```
app/
  fastmoss/signer.py   tanda tangan fm-sign / fm-sig (Python murni, tanpa browser)
  fastmoss/cookies.py  baca/tulis file cookie (format mentah, header, atau cURL)
  fastmoss/client.py   klien HTTP: jeda antar-request, retry, cache, deteksi "terkunci"
  catalog.py           definisi semua menu daftar (kolom, filter, urutan)
  details.py           definisi halaman detail produk/toko/kreator/LIVE/video
  market.py            halaman Tren Pasar
  routes/api.py        API JSON untuk halaman web
  routes/export.py     ekspor Excel/CSV/PDF
  auth.py, settings.py login tim & konfigurasi
web/                   tampilan (HTML + CSS + JS, tanpa build)
config/cookies.txt     ← TEMPAT COOKIE (tidak ikut git)
tests/                 pytest
```

## Menjalankan di komputer sendiri

1. Pasang Python 3.10 atau lebih baru.
2. Isi cookie (lihat bagian berikut).
3. Klik dua kali **`run.bat`**, atau jalankan:
   ```bash
   pip install -r requirements.txt
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
4. Buka <http://localhost:8000>.

## Mengganti cookie FastMoss

Cookie hanya ada di **satu tempat**: `config/cookies.txt`. Ada dua cara menggantinya:

**A. Lewat aplikasi (paling mudah).** Buka menu **Pengaturan & Cookie**, tempel cURL atau cookie, lalu klik Simpan.
Langkah ini butuh kata sandi admin kalau login diaktifkan.

**B. Edit file.** Salin `config/cookies.example.txt` menjadi `config/cookies.txt`, lalu tempel salah satu format ini:
- isi cookie mentah: `fd_tk=...; NEXT_LOCALE=id; ...`
- satu baris header: `Cookie: fd_tk=...; ...`
- perintah cURL utuh

Cara mengambilnya: login di fastmoss.com, buka DevTools (F12) lalu tab **Network**, muat ulang halaman,
klik kanan salah satu request `/api/...`, lalu pilih **Copy → Copy as cURL**.

Perubahan berlaku **tanpa restart**. File dibaca ulang setiap kali isinya berubah.
`config/cookies.txt` sudah masuk `.gitignore`, jadi tidak akan ikut ter-commit.

Kalau muncul pesan *"cookie kedaluwarsa / belum login"*, cookie perlu diganti dengan yang baru.

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
   Folder `config/` dipasang sebagai volume, jadi cookie tetap ada saat container diperbarui
   dan tetap bisa diganti dari halaman Pengaturan.
3. Pasang di belakang **reverse proxy HTTPS** (Caddy, Nginx, atau Cloudflare Tunnel). Jangan buka port 8000 langsung ke internet tanpa HTTPS.
4. Cek kesehatan server: `GET /healthz`.

Pengaturan lain (opsional, lewat `.env`): `FM_REGION`, `FM_MIN_INTERVAL` (jeda antar-request, detik),
`FM_CACHE_TTL` (lama cache, detik), `FM_FREE_ROW_LIMIT`, `FM_EXPORT_MAX_ROWS`, `FM_COOKIE_FILE`.

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
