@echo off
REM Jalankan FastMoss Lite di komputer ini. Buka di browser: http://localhost:8000
REM (0.0.0.0 di log server = "terima koneksi dari mana saja", BUKAN alamat untuk dibuka di browser)
cd /d "%~dp0"
if not exist config\cookies_akun_*.txt if not exist config\cookies.txt (
  echo [!] Belum ada file akun. Salin config\cookies.example.txt menjadi config\cookies_akun_1.txt lalu isi cookie FastMoss.
)
python -m pip install -q --disable-pip-version-check -r requirements.txt
echo.
echo  ============================================================
echo   FastMoss Lite - buka di browser:  http://localhost:8000
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do for /f "tokens=*" %%b in ("%%a") do echo   Dari komputer lain di jaringan yang sama:  http://%%b:8000
echo   Tutup jendela ini (atau tekan Ctrl+C) untuk menghentikan.
echo  ============================================================
echo.
REM buka browser otomatis begitu server siap
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "for($i=0;$i -lt 60;$i++){try{Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/healthz -TimeoutSec 1 | Out-Null; Start-Process 'http://localhost:8000'; break}catch{Start-Sleep -Milliseconds 500}}"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
