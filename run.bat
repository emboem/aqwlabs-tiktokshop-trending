@echo off
REM Jalankan FastMoss Lite di komputer ini (http://localhost:8000)
cd /d "%~dp0"
if not exist config\cookies_akun_*.txt if not exist config\cookies.txt (
  echo [!] Belum ada file akun. Salin config\cookies.example.txt menjadi config\cookies_akun_1.txt lalu isi cookie FastMoss.
)
python -m pip install -q -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
