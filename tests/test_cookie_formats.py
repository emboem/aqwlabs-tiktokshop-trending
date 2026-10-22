"""Deteksi format cookie otomatis — semua nilai di sini palsu."""
from app.fastmoss.cookies import cookie_get, detect_cookie, parse_cookie_text

WANT = {"NEXT_LOCALE": "id", "fd_tk": "tok123", "_ga": "GA1.1.99", "utm": "a%2Fb|c"}


def as_dict(cookie: str) -> dict:
    return dict(x.split("=", 1) for x in cookie.split("; ")) if cookie else {}


def test_curl_windows_cmd_caret():
    # bentuk persis "Copy as cURL (cmd)" Chrome: ^ di akhir baris, ^" pembuka/penutup, ^%^2 dan ^| di nilai
    text = (
        'curl ^"https://www.fastmoss.com/api/goods/V2/search?page=1^&region=ID^" ^\n'
        '  -H ^"accept: application/json, text/plain, */*^" ^\n'
        '  -b ^"NEXT_LOCALE=id; fd_tk=tok123; _ga=GA1.1.99; utm=a^%^2Fb^|c^" ^\n'
        '  -H ^"fm-sign: abc^" ^\n'
        '  -H ^"user-agent: Mozilla/5.0^"\n'
    )
    cookie, fmt = detect_cookie(text)
    assert fmt == "cURL Windows (cmd)" and as_dict(cookie) == WANT


def test_curl_cmd_two_blocks_takes_first_and_header_form():
    one = '-H ^"cookie: NEXT_LOCALE=id; fd_tk=tok123; _ga=GA1.1.99; utm=a^%^2Fb^|c^" ^\n'
    text = f'curl ^"https://x/api/a^" ^\n  {one}\n\n\ncurl ^"https://x/api/b^" ^\n  -b ^"fd_tk=LAIN^"\n'
    assert as_dict(parse_cookie_text(text)) == WANT


def test_curl_bash_and_double_quote():
    bash = "curl 'https://x/api' \\\n  -H 'accept: */*' \\\n  -b 'NEXT_LOCALE=id; fd_tk=tok123; _ga=GA1.1.99; utm=a%2Fb|c'"
    assert detect_cookie(bash) == ("NEXT_LOCALE=id; fd_tk=tok123; _ga=GA1.1.99; utm=a%2Fb|c", "cURL bash")
    dq = 'curl.exe "https://x/api" -H "Cookie: fd_tk=tok123; q=\\"x\\""'
    assert cookie_get(parse_cookie_text(dq), "fd_tk") == "tok123"


def test_powershell_fetch_json_table():
    ps = ('$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession\n'
          '$session.Cookies.Add((New-Object System.Net.Cookie("NEXT_LOCALE", "id", "/", "www.fastmoss.com")))\n'
          '$session.Cookies.Add((New-Object System.Net.Cookie("fd_tk", "tok123", "/", ".fastmoss.com")))')
    assert detect_cookie(ps) == ("NEXT_LOCALE=id; fd_tk=tok123", "PowerShell")

    fetch = 'fetch("https://x/api", {\n  "headers": {\n    "accept": "*/*",\n    "cookie": "fd_tk=tok123; a=1"\n  }\n});'
    assert detect_cookie(fetch) == ("fd_tk=tok123; a=1", "fetch / Node.js")

    js = '[{"domain":".fastmoss.com","name":"fd_tk","value":"tok123"},{"domain":".google.com","name":"NID","value":"x"}]'
    assert detect_cookie(js) == ("fd_tk=tok123", "JSON ekstensi cookie")

    table = "Name\tValue\tDomain\nfd_tk\ttok123\t.fastmoss.com\nNEXT_LOCALE\tid\twww.fastmoss.com"
    assert detect_cookie(table) == ("fd_tk=tok123; NEXT_LOCALE=id", "tabel DevTools")


def test_header_block_and_raw():
    block = "accept: */*\nreferer: https://www.fastmoss.com/id/\ncookie: fd_tk=tok123; a=1\nuser-agent: Mozilla"
    assert detect_cookie(block) == ("fd_tk=tok123; a=1", "blok header")
    panel = "cookie\nfd_tk=tok123; a=1\nreferer\nhttps://x"
    assert detect_cookie(panel) == ("fd_tk=tok123; a=1", "blok header")
    assert detect_cookie("fd_tk=tok123;a=1;fd_tk=dobel; junk") == ("fd_tk=tok123; a=1", "cookie mentah")
    assert detect_cookie("# komentar saja\n") == ("", "")
    assert detect_cookie("curl 'https://x/api' -H 'accept: */*'")[0] == ""
