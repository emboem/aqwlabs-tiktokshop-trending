/* FastMoss Lite v2 — aplikasi satu halaman (tanpa framework). */
"use strict";

// ============================================================ util
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const S = { me: null, catalog: null, account: null, accounts: [], acc: "", region: "ID", options: {}, countries: [], token: 0 };
try { S.region = localStorage.getItem("fml.region") || "ID"; } catch (_) { /* tanpa storage */ }
try { S.acc = localStorage.getItem("fml.account") || ""; } catch (_) { /* tanpa storage */ }
// Akun FastMoss pilihan pengguna ini — dikirim di setiap request (server memakai cookie akun itu).
const accHeaders = () => (S.acc ? { "X-FM-Account": S.acc } : {});

function dig(obj, path) {
  if (!path) return undefined;
  let cur = obj;
  for (const p of String(path).split(".")) {
    if (cur == null) return undefined;
    cur = cur[p];
  }
  return cur;
}

function toast(msg, ms = 3200) {
  const t = document.createElement("div");
  t.className = "toast";
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), ms);
}

async function api(path, params = {}, opts = {}) {
  const u = new URL(path, location.origin);
  for (const [k, v] of Object.entries(params)) if (v !== "" && v != null) u.searchParams.set(k, v);
  if (!opts.noRegion) u.searchParams.set("region", S.region);
  const r = await fetch(u, {
    method: opts.method || "GET",
    headers: { ...accHeaders(), ...(opts.body ? { "Content-Type": "application/json" } : {}) },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    credentials: "same-origin",
  });
  if (r.status === 401 && !opts.allow401) {
    S.me = { role: null, auth_required: true };
    renderLogin();
    throw new Error("Silakan masuk dulu.");
  }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.detail || `Gagal (HTTP ${r.status})`);
  return j;
}

// ============================================================ format angka
const CUR = { ID: "Rp", MY: "RM", TH: "฿", VN: "₫", PH: "₱", SG: "S$", US: "$", GB: "£", MX: "MX$", BR: "R$",
  JP: "¥", KR: "₩", DE: "€", FR: "€", IT: "€", ES: "€", IE: "€", SA: "SAR ", AE: "AED ", CA: "C$", AU: "A$" };
const nfC = new Intl.NumberFormat("id-ID", { notation: "compact", maximumFractionDigits: 2 });
const nfF = new Intl.NumberFormat("id-ID", { maximumFractionDigits: 2 });
const cur = () => CUR[S.region] || "";

function toNum(v) {
  if (typeof v === "number") return Number.isFinite(v) ? v : null;
  if (typeof v === "string" && /^-?\d+(\.\d+)?$/.test(v.trim())) return parseFloat(v);
  return null;
}
const blank = (v) => v == null || v === "" || (Array.isArray(v) && !v.length);
function fmtNum(v) {
  const n = toNum(v);
  if (n == null) return blank(v) ? "–" : esc(v);
  return Math.abs(n) >= 100000 ? nfC.format(n) : nfF.format(n);
}
function fmtMoney(v) {
  const n = toNum(v);
  if (n == null) return blank(v) ? "–" : esc(v);
  const a = Math.abs(n);
  return cur() + (a >= 100000 ? nfC.format(n) : a >= 1000 ? nfF.format(Math.round(n)) : nfF.format(n));
}
// Satuan waktu berbahasa Mandarin yang kadang lolos dari FastMoss ("23.9小时") → Indonesia.
const CJK_MAP = { "小时": " jam", "分钟": " menit", "秒": " detik", "天": " hari" };
const CJK_UNIT = /小时|分钟|秒|天/;
const cjkUnits = (s) => s.replace(/(\d)\.(\d)/g, "$1,$2").replace(/小时|分钟|秒|天/g, (m) => CJK_MAP[m]);
// FastMoss kadang mengirim persen sebagai teks ("9.15%" atau "-3,88%") → seragamkan ke format id-ID.
function pctText(s) {
  const m = /^\s*([-+]?\d+(?:[.,]\d+)?)\s*%\s*$/.exec(s);
  if (!m) return null;
  const n = parseFloat(m[1].replace(",", "."));
  const t = `${nfF.format(n)}%`;
  return n < 0 ? `<span class="down">${esc(t)}</span>` : esc(t);
}
function fmtPct(v) {
  if (blank(v) || v === "-") return "–";
  const s = typeof v === "number" ? `${nfF.format(v)}%` : String(v);
  return s.trim().startsWith("-") ? `<span class="down">${esc(s)}</span>` : esc(s);
}
function fmtGrowth(v) {
  if (blank(v) || v === "-") return "–";
  const s = typeof v === "number" ? `${nfF.format(v)}%` : String(v);
  const neg = s.trim().startsWith("-");
  return `<span class="${neg ? "down" : "up"}">${neg ? "▼" : "▲"} ${esc(s.replace(/^[-+]/, ""))}</span>`;
}
function fmtTs(v, withTime = true) {
  const n = toNum(v);
  const iso = n == null && typeof v === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(v);
  if (n == null && !iso) return blank(v) ? "–" : esc(String(v).slice(0, withTime ? 16 : 10));
  const d = iso ? new Date(v) : new Date(n * (n < 1e12 ? 1000 : 1));
  return esc(d.toLocaleString("id-ID", withTime ? { dateStyle: "medium", timeStyle: "short" } : { dateStyle: "medium" }));
}
function fmtDur(v) {
  const n = toNum(v);
  if (n == null) return blank(v) ? "–" : esc(v);
  const s = Math.round(n), hh = Math.floor(s / 3600), mm = Math.floor((s % 3600) / 60), ss = s % 60;
  return hh ? `${hh} jam ${mm} mnt` : mm ? `${mm} mnt ${ss} dtk` : `${ss} dtk`;
}
function tags(v) {
  if (blank(v)) return "–";
  const arr = Array.isArray(v) ? v : [v];
  return arr.slice(0, 3).map((x) => `<span class="tag">${esc(typeof x === "object" ? (x.name || x.c_name || JSON.stringify(x)) : x)}</span>`).join("");
}
function prettyKey(k) {
  return String(k).replace(/_/g, " ").replace(/\b(cnt|count)\b/g, "jumlah").replace(/^./, (c) => c.toUpperCase());
}

// Bagian tanpa definisi kolom digambar otomatis: buang field teknis (ID, gambar, tautan, kode mata uang)
// supaya tidak muncul sebagai "angka" (mis. UID 7252574471821984774 -> "7.252.574,47 T").
const NOISE_KEY = /(^|_)(id|uid|sid|ids|region|currency|currency_unit|currency_code|avatar|cover|img|image|icon|url|oss|uri|sort)$|^is_|^(test|header)$/i;
function noiseValue(v) {
  return typeof v === "string" && (/^https?:\/\//.test(v) || /~tplv|^tt_|\/tos-/.test(v) || /^\d{15,}$/.test(v));
}
function autoFields(obj, limit) {
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) return [];
  return Object.entries(obj)
    .filter(([k, v]) => !k.endsWith("_show") && v != null && v !== "" && typeof v !== "object" && typeof v !== "boolean"
      && !NOISE_KEY.test(k) && !noiseValue(v))
    .slice(0, limit)
    .map(([k, v]) => ({ k, label: prettyKey(k), show: obj[`${k}_show`], num: toNum(v) != null }));
}

// Label grafik yang dikirim FastMoss sebagai kunci terjemahan (mis. "common.goods.product_card").
const LABEL_ID = {
  product_card: "Kartu produk", shop_account: "Akun toko", affiliate: "Afiliasi (kreator)",
  adTraffic: "Trafik iklan", otherTraffic: "Trafik organik", video: "Video", live: "LIVE", others: "Lainnya", other: "Lainnya",
  female: "Perempuan", male: "Laki-laki", unknown: "Tidak diketahui",
  early_morning: "Dini hari", morning: "Pagi", afternoon: "Siang–sore", evening: "Malam", night: "Malam",
  "WEST JAVA": "Jawa Barat", "EAST JAVA": "Jawa Timur", "CENTRAL JAVA": "Jawa Tengah", JAKARTA: "DKI Jakarta",
  BANTEN: "Banten", YOGYAKARTA: "DI Yogyakarta", "NORTH SUMATRA": "Sumatera Utara", "SOUTH SUMATRA": "Sumatera Selatan",
  "WEST SUMATRA": "Sumatera Barat", RIAU: "Riau", LAMPUNG: "Lampung", "SOUTH SULAWESI": "Sulawesi Selatan",
  BALI: "Bali", "EAST KALIMANTAN": "Kalimantan Timur", "WEST KALIMANTAN": "Kalimantan Barat",
  "SOUTH KALIMANTAN": "Kalimantan Selatan", ACEH: "Aceh",
};
function labelText(v) {
  let s = Array.isArray(v) ? v.join(", ") : String(v ?? "");
  s = s.replace(/\.name$/, "");
  if (/^[a-z]+(\.[A-Za-z_]+)+$/.test(s)) s = s.split(".").pop();
  return LABEL_ID[s] || LABEL_ID[s.toUpperCase()] || s;
}

const DETAIL_KINDS = new Set(["product", "shop", "creator", "live", "video"]);
const ROUND = new Set(["creator"]);

function spark(list, x, y) {
  if (!Array.isArray(list) || list.length < 2) return "–";
  const vals = list.map((p) => toNum(dig(p, y)) ?? 0);
  const w = 96, hgt = 28, min = Math.min(...vals), max = Math.max(...vals), span = max - min || 1;
  const pts = vals.map((v, i) => `${(i / (vals.length - 1)) * w},${hgt - 3 - ((v - min) / span) * (hgt - 6)}`).join(" ");
  const tip = list.map((p, i) => `${dig(p, x) ?? i}: ${nfF.format(vals[i])}`).join("\n");
  return `<svg class="spark" width="${w}" height="${hgt}" viewBox="0 0 ${w} ${hgt}" role="img" aria-label="Tren"><title>${esc(tip)}</title>`
    + `<polyline fill="none" stroke="var(--chart)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" points="${pts}"/></svg>`;
}

function entity(col, row) {
  const title = dig(row, col.key);
  const img = col.img ? dig(row, col.img) : "";
  const sub = col.sub ? dig(row, col.sub) : "";
  const id = col.id ? dig(row, col.id) : "";
  const ext = col.url ? dig(row, col.url) : "";
  const t = blank(title) ? "(tanpa judul)" : (Array.isArray(title) ? title.join(", ") : title);
  let head;
  if (col.link && id) head = `<a class="t" href="#/detail/${col.link}/${esc(id)}" title="${esc(t)}">${esc(t)}</a>`;
  else if (ext) head = `<a class="t" href="${esc(ext)}" target="_blank" rel="noopener" title="${esc(t)}">${esc(t)}</a>`;
  else head = `<span class="t" title="${esc(t)}">${esc(t)}</span>`;
  const pic = col.img ? (img ? `<img src="${esc(img)}" alt="" loading="lazy" referrerpolicy="no-referrer">` : `<span class="ph"></span>`) : "";
  const subTxt = blank(sub) ? "" : `<span class="s">${esc(col.sub_prefix || "")}${esc(Array.isArray(sub) ? sub.join(", ") : sub)}</span>`;
  return `<div class="ent ${ROUND.has(col.link) ? "round" : ""}">${pic}<div class="box">${head}${subTxt}</div></div>`;
}

function cell(col, row) {
  const v = dig(row, col.key);
  switch (col.type) {
    case "entity": return entity(col, row);
    case "num": return fmtNum(v);
    case "money": return fmtMoney(v);
    case "pct": return /inc_rate|growth/.test(col.key) ? fmtGrowth(v) : fmtPct(v);
    case "tags": return tags(v);
    case "date": return toNum(v) != null && toNum(v) > 1e8 ? fmtTs(v, false) : (blank(v) ? "–" : esc(String(v).slice(0, 10)));
    case "ts": return fmtTs(v);
    case "dur": return fmtDur(v);
    case "bool": return String(v) === "1" || v === true || String(v) === "true" ? `<span class="pill brand">Ya</span>` : "–";
    case "spark": return spark(dig(row, col.key), col.x, col.y);
    case "props": return Array.isArray(v) && v.length
      ? esc(v.map((p) => p?.prop_value ?? p?.value ?? p).filter((x) => !blank(x)).join(" / ")) : "–";
    default: if (typeof v === "string" && pctText(v)) return pctText(v);
      if (typeof v === "string" && CJK_UNIT.test(v)) return esc(cjkUnits(v));
      return blank(v) ? "–" : esc(Array.isArray(v) ? v.join(", ") : (typeof v === "object" ? JSON.stringify(v) : v));
  }
}
const isLeft = (c) => ["entity", "tags", "text", "price", "props"].includes(c.type);

function sortValue(col, row) {
  const v = dig(row, col.key);
  const n = toNum(v);
  if (n != null) return n;
  if (typeof v === "string") {
    const m = v.replace(/\./g, "").replace(",", ".").match(/-?\d+(\.\d+)?/);
    if (m && /%$/.test(v.trim())) return parseFloat(m[0]);
    return v.toLowerCase();
  }
  return Array.isArray(v) ? v.length : -Infinity;
}

// ============================================================ tabel
function tableHTML(cols, rows, opt = {}) {
  if (!rows.length) return `<div class="empty">Tidak ada data untuk filter ini.</div>`;
  const off = opt.offset || 0;
  const head = cols.map((c, i) => `<th class="${isLeft(c) ? "l" : ""} ${opt.sortIdx === i ? "sorted" : ""}" data-i="${i}" title="Urutkan">`
    + `${esc(c.label)}<span class="arrow">${opt.sortIdx === i ? (opt.sortDir > 0 ? "▲" : "▼") : "↕"}</span></th>`).join("");
  const body = rows.map((r, ri) => `<tr><td class="rank">${off + ri + 1}</td>`
    + cols.map((c) => `<td class="${isLeft(c) ? "l" : ""} num">${cell(c, r)}</td>`).join("") + `</tr>`).join("");
  return `<div class="table-wrap"><table class="data"><thead><tr><th class="l" style="cursor:default">#</th>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

// tabel yang bisa diurutkan di sisi klien (urutan baris yang sedang tampil)
function mountTable(el, cols, rows, opt = {}) {
  let sortIdx = -1, sortDir = -1;
  const draw = () => {
    let data = rows;
    if (sortIdx >= 0) {
      const c = cols[sortIdx];
      data = [...rows].sort((a, b) => {
        const x = sortValue(c, a), y = sortValue(c, b);
        return (x > y ? 1 : x < y ? -1 : 0) * sortDir;
      });
    }
    el.innerHTML = tableHTML(cols, data, { ...opt, sortIdx, sortDir });
    $$("th[data-i]", el).forEach((th) => th.addEventListener("click", () => {
      const i = +th.dataset.i;
      if (sortIdx === i) sortDir = -sortDir; else { sortIdx = i; sortDir = -1; }
      draw();
    }));
  };
  draw();
}

function autoCols(rows) {
  if (!rows || !rows.length) return [];
  return autoFields(rows[0], 14).map((f) => ({ label: f.label, type: f.num ? "num" : "text", key: f.k }));
}

// ============================================================ banner status
function statusBanner(res, retry) {
  if (!res || res.status === "ok") return "";
  if (res.status === "locked") {
    return `<div class="banner lock"><span class="ico">🔒</span><div><b>Terkunci paket FastMoss.</b> ${esc(res.message || "")}`
      + `<div class="faint" style="margin-top:4px">Aplikasi tidak membuka data berbayar — tampil otomatis bila akun FastMoss yang dipasang berlangganan.</div></div></div>`;
  }
  if (res.status === "auth") {
    return `<div class="banner bad"><span class="ico">⚠️</span><div><b>Cookie FastMoss bermasalah.</b> ${esc(res.message || "")} `
      + `<a href="#/settings?edit=${encodeURIComponent(S.acc)}" style="text-decoration:underline">Ganti cookie</a></div></div>`;
  }
  return `<div class="banner bad"><span class="ico">⚠️</span><div><b>Gagal memuat data.</b> ${esc(res.message || "")}`
    + (retry ? ` <button class="btn sm" data-retry>Coba lagi</button>` : "") + `</div></div>`;
}

function lockedRowsNote(res) {
  if (!res || !res.limit) return "";
  const total = res.total ? ` dari total ${nfF.format(res.total)} data` : "";
  return `<div class="locked-rows">🔒 Akun FastMoss gratis hanya menampilkan ${res.limit} baris teratas${total}. `
    + `Baris berikutnya terkunci — upgrade paket FastMoss untuk melihat semuanya.</div>`;
}

// ============================================================ opsi filter
async function getOptions(source) {
  const key = `${S.region}:${source}`;
  if (!S.options[key]) {
    S.options[key] = api(`/api/options/${source}`).then((j) => j.options || {}).catch(() => ({}));
  }
  return S.options[key];
}

// ============================================================ unduh ekspor
async function download(url) {
  toast("Menyiapkan berkas…", 1800);
  try {
    const r = await fetch(url, { credentials: "same-origin", headers: accHeaders() });
    if (!r.ok) {
      const j = await r.json().catch(() => ({}));
      throw new Error(j.detail || `HTTP ${r.status}`);
    }
    const blob = await r.blob();
    const cd = r.headers.get("content-disposition") || "";
    const m = cd.match(/filename\*=UTF-8''([^;]+)/);
    const name = m ? decodeURIComponent(m[1]) : "fastmoss";
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  } catch (e) {
    toast(`Ekspor gagal: ${e.message}`);
  }
}
function exportButtons(base) {
  return ["xlsx", "csv", "pdf"].map((f) => `<button class="btn sm" data-export="${base}${base.includes("?") ? "&" : "?"}format=${f}&region=${S.region}">`
    + `${{ xlsx: "Excel", csv: "CSV", pdf: "PDF" }[f]}</button>`).join("");
}
function bindExports(el) {
  $$("[data-export]", el).forEach((b) => b.addEventListener("click", () => download(b.dataset.export)));
}

// ============================================================ router
function parseHash() {
  const raw = location.hash.slice(1) || "/";
  const [path, qs] = raw.split("?");
  return { parts: path.split("/").filter(Boolean), q: Object.fromEntries(new URLSearchParams(qs || "")) };
}
function go(path, q = {}) {
  const qs = new URLSearchParams(Object.entries(q).filter(([, v]) => v !== "" && v != null)).toString();
  const next = `#${path}${qs ? `?${qs}` : ""}`;
  if (location.hash === next) route(); else location.hash = next;
}
window.addEventListener("hashchange", route);

async function boot() {
  applyTheme();
  try {
    S.me = await api("/api/me", {}, { noRegion: true, allow401: true });
  } catch (e) {
    $("#app").innerHTML = `<div class="login"><div class="card"><h2>Server tidak terjangkau</h2><p class="muted">${esc(e.message)}</p></div></div>`;
    return;
  }
  if (S.me.auth_required && !S.me.role) return renderLogin();
  await start();
}

async function start() {
  S.catalog = await api("/api/catalog", {}, { noRegion: true });
  await loadAccounts();
  renderShell();
  route();
  loadAccount();
  getOptions("country").then((o) => {
    S.countries = o.list || o.country || [];
    renderRegion();
  });
}

async function loadAccounts(force = false) {
  try {
    const r = await api("/api/accounts", force ? { refresh: 1 } : {}, { noRegion: true });
    S.accounts = r.accounts || [];
    if (!S.accounts.some((a) => a.id === S.acc)) S.acc = r.current || r.default || "";
  } catch (_) { S.accounts = []; }
  renderAccounts();
  return S.accounts;
}
function setAccount(id) {
  S.acc = String(id);
  try { localStorage.setItem("fml.account", S.acc); } catch (_) { /* */ }
  S.account = null;
  renderAccounts();
  loadAccount();
  route();
}

async function loadAccount(force = false) {
  try {
    S.account = await api("/api/account", force ? { refresh: 1 } : {});
  } catch (_) { S.account = null; }
  renderPlan();
  return S.account;
}

function route() {
  if (!S.catalog) return;
  const { parts, q } = parseHash();
  S.token++;
  $("#sb")?.classList.remove("open");
  const page = parts[0] || "";
  markNav(location.hash.split("?")[0] || "#/");
  const el = $("#content");
  window.scrollTo(0, 0);
  if (page === "m" && parts[1]) return pageList(el, parts[1], q);
  if (page === "market" && parts[1]) return pageMarket(el, parts[1], q);
  if (page === "detail" && parts[1] && parts[2]) return pageDetail(el, parts[1], parts[2], q);
  if (page === "settings") return pageSettings(el, q);
  return pageHome(el);
}

// ============================================================ tema
function applyTheme() {
  let t = "";
  try { t = localStorage.getItem("fml.theme") || ""; } catch (_) { /* */ }
  if (t) document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme;
}
function toggleTheme() {
  const dark = document.documentElement.dataset.theme
    ? document.documentElement.dataset.theme === "dark"
    : matchMedia("(prefers-color-scheme: dark)").matches;
  try { localStorage.setItem("fml.theme", dark ? "light" : "dark"); } catch (_) { /* */ }
  applyTheme();
  route();
}

// ============================================================ login
function renderLogin() {
  $("#app").innerHTML = `<div class="login"><form class="card" id="login">
      <div class="brand" style="padding:0 0 18px"><div class="brand-mark">F</div><div><div class="brand-name">FastMoss Lite</div>
      <div class="brand-sub">Analisis TikTok Shop untuk tim</div></div></div>
      <div class="field"><label for="pw">Kata sandi tim</label><input id="pw" class="input" type="password" autocomplete="current-password" required autofocus></div>
      <div id="loginErr" class="down" style="min-height:20px;margin:8px 0;font-size:13px"></div>
      <button class="btn primary" style="width:100%;justify-content:center">Masuk</button>
      <p class="faint" style="font-size:12px;margin:14px 0 0">Minta kata sandi ke admin tim. Sesi tersimpan ${14} hari di perangkat ini.</p>
    </form></div>`;
  $("#login").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const r = await api("/api/login", {}, { method: "POST", body: { password: $("#pw").value }, noRegion: true, allow401: true });
      S.me = { role: r.role, auth_required: true };
      await start();
    } catch (err) { $("#loginErr").textContent = err.message; }
  });
}

// ============================================================ kerangka
function navItem(href, label) {
  return `<a class="nav-item" href="${href}"><span class="nav-dot"></span>${esc(label)}</a>`;
}
function renderShell() {
  const c = S.catalog;
  const groups = c.groups.map((g) => {
    let items;
    if (g === "Tren Pasar") items = c.market.map((p) => navItem(`#/market/${p.key}`, p.title)).join("");
    else items = c.menus.filter((m) => m.group === g).map((m) => navItem(`#/m/${m.key}`, m.title)).join("");
    return items ? `<div class="nav-group"><div class="nav-title">${esc(g)}</div>${items}</div>` : "";
  }).join("");
  let collapsed = false;
  try { collapsed = localStorage.getItem("fml.nav") === "0"; } catch (_) { /* */ }
  $("#app").innerHTML = `<div class="shell${collapsed ? " nav-collapsed" : ""}">
    <aside class="sidebar" id="sb">
      <a class="brand" href="#/"><div class="brand-mark">F</div><div><div class="brand-name">FastMoss Lite</div><div class="brand-sub">TikTok Shop Intelligence</div></div></a>
      ${navItem("#/", "Beranda")}
      ${groups}
      <div class="nav-group"><div class="nav-title">Sistem</div>${navItem("#/settings", "Pengaturan & Cookie")}</div>
    </aside>
    <div class="scrim" id="scrim"></div>
    <div class="main">
      <header class="topbar">
        <button class="btn ghost menu-btn" id="menuBtn" aria-controls="sb" aria-label="Sembunyikan / tampilkan menu" title="Sembunyikan / tampilkan menu">☰</button>
        <form id="quick" class="quick" role="search">
          <svg class="quick-ico" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="m20 20-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <input class="input" id="quickIn" type="search" enterkeyhint="search" autocomplete="off" aria-label="Cari"
            placeholder="${isNarrow() ? "Cari produk / tempel link" : "Cari produk, atau tempel link / ID produk, toko, kreator, video"}"
            title="Ketik kata kunci produk, atau tempel link / ID produk, toko, kreator, video — lalu tekan Enter">
          <kbd class="quick-key hide-sm" title="Tekan / untuk mencari">/</kbd>
        </form>
        <div class="spacer"></div>
        <select class="select" id="acct" title="Akun FastMoss yang dipakai"></select>
        <select class="select" id="region" title="Negara"></select>
        <span id="plan" class="hide-sm"></span>
        <button class="btn ghost" id="themeBtn" title="Ganti tema">◐</button>
        ${S.me && S.me.auth_required ? `<button class="btn ghost" id="logoutBtn" title="Keluar">Keluar</button>` : ""}
      </header>
      <main class="content" id="content"></main>
    </div></div>`;
  $("#menuBtn").addEventListener("click", toggleNav);
  $("#scrim").addEventListener("click", () => $("#sb").classList.remove("open"));
  $("#themeBtn").addEventListener("click", toggleTheme);
  $("#logoutBtn")?.addEventListener("click", async () => {
    await api("/api/logout", {}, { method: "POST", noRegion: true }).catch(() => {});
    S.me.role = null;
    renderLogin();
  });
  $("#quick").addEventListener("submit", (e) => { e.preventDefault(); quickJump($("#quickIn").value.trim()); });
  renderAccounts();
  renderRegion();
  renderPlan();
}

// HP/tablet: menu samping melayang (buka-tutup); komputer: menu bisa disembunyikan & diingat
const isNarrow = () => matchMedia("(max-width: 960px)").matches;
function toggleNav() {
  if (isNarrow()) { $("#sb").classList.toggle("open"); return; }
  const off = $(".shell").classList.toggle("nav-collapsed");
  try { localStorage.setItem("fml.nav", off ? "0" : "1"); } catch (_) { /* */ }
  window.dispatchEvent(new Event("resize"));   // grafik ikut melebar/menyempit
}
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") $("#sb")?.classList.remove("open");
  const typing = /^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName) || e.target.isContentEditable;
  if (e.key === "/" && !typing && !e.ctrlKey && !e.metaKey && !e.altKey && $("#quickIn")) { e.preventDefault(); $("#quickIn").focus(); }
});

const planShort = (a) => (!a.cookie?.exists ? "belum ada cookie" : !a.logged_in ? "cookie bermasalah" : a.is_free ? "gratis" : "berlangganan");
function renderAccounts() {
  const sel = $("#acct");
  if (!sel) return;
  sel.hidden = S.accounts.length < 2;
  sel.innerHTML = S.accounts.map((a) => `<option value="${esc(a.id)}" ${a.id === S.acc ? "selected" : ""}>${esc(a.label)}${String(a.label).toLowerCase().includes(planShort(a)) ? "" : ` · ${planShort(a)}`}</option>`).join("");
  sel.onchange = () => setAccount(sel.value);
}

function markNav(hash) {
  $$(".nav-item").forEach((a) => a.classList.toggle("active", a.getAttribute("href") === hash));
}

function renderRegion() {
  const sel = $("#region");
  if (!sel) return;
  const list = S.countries.length ? S.countries : [{ v: "ID", l: "Indonesia" }];
  sel.innerHTML = list.map((o) => `<option value="${esc(o.v)}" ${o.v === S.region ? "selected" : ""}>${esc(o.l)}</option>`).join("");
  sel.onchange = () => {
    S.region = sel.value;
    try { localStorage.setItem("fml.region", S.region); } catch (_) { /* */ }
    route();
  };
}

function renderPlan() {
  const el = $("#plan");
  if (!el) return;
  const a = S.account;
  if (!a) { el.innerHTML = `<a href="#/settings" class="pill bad">Cookie belum siap</a>`; return; }
  const fix = `#/settings?edit=${encodeURIComponent(a.id || S.acc)}`;
  if (!a.cookie?.exists) { el.innerHTML = `<a href="${fix}" class="pill" title="Klik untuk mengisi cookie">Belum ada cookie</a>`; return; }
  if (!a.logged_in) { el.innerHTML = `<a href="${fix}" class="pill bad" title="Klik untuk mengganti cookie">Cookie bermasalah</a>`; return; }
  el.innerHTML = `<a href="#/settings" class="pill ${a.is_free ? "lock" : "ok"}" title="${esc(a.nickname || "")}">${a.is_free ? "🔒 " : "★ "}${esc(a.plan || "Akun FastMoss")}</a>`;
}

function quickJump(text) {
  if (!text) return;
  const pats = [
    [/e-commerce\/detail\/(\d+)/, "product"], [/shop-marketing\/detail\/(\d+)/, "shop"],
    [/influencer\/detail\/(\d+)/, "creator"], [/live\/detail\/(\d+)/, "live"],
    [/media-source\/video\/(\d+)/, "video"], [/\/product\/(\d{12,})/, "product"], [/\/video\/(\d{12,})/, "video"],
  ];
  for (const [re, kind] of pats) {
    const m = text.match(re);
    if (m) return go(`/detail/${kind}/${m[1]}`);
  }
  if (/^\d{15,}$/.test(text)) return go(`/detail/product/${text}`);
  if (/^@/.test(text)) return go("/m/creator-search", { words: text.slice(1) });
  return go("/m/product-search", { words: text });
}

// ============================================================ beranda
function pageHome(el) {
  const c = S.catalog;
  const tiles = c.groups.map((g) => {
    const items = g === "Tren Pasar"
      ? c.market.map((p) => ({ href: `#/market/${p.key}`, t: p.title, d: p.desc }))
      : c.menus.filter((m) => m.group === g).map((m) => ({ href: `#/m/${m.key}`, t: m.title, d: m.desc }));
    return `<h2 style="font-size:15px;margin:26px 0 10px">${esc(g)}</h2><div class="menu-tiles">`
      + items.map((i) => `<a class="card tile" href="${i.href}"><div class="t">${esc(i.t)}</div><div class="d">${esc(i.d)}</div></a>`).join("")
      + `</div>`;
  }).join("");
  el.innerHTML = `<div class="page-head"><div><div class="crumb">Beranda</div><h1>Selamat datang 👋</h1>
      <p>Data TikTok Shop dari FastMoss — produk, toko, kreator, LIVE, video, iklan, dan tren pasar. Mata uang mengikuti negara terpilih.</p></div></div>
    <div id="homeAcc"></div>${tiles}`;
  const acc = $("#homeAcc", el);
  const draw = () => {
    const a = S.account;
    if (!a) { acc.innerHTML = statusBanner({ status: "auth", message: "Belum ada cookie FastMoss yang terpasang." }); return; }
    if (!a.logged_in) { acc.innerHTML = statusBanner({ status: "auth", message: a.message }); return; }
    acc.innerHTML = a.is_free
      ? `<div class="banner lock"><span class="ico">🔒</span><div><b>Akun FastMoss gratis terpasang (${esc(a.nickname || "")}).</b>
         Data diambil apa adanya sesuai paket: tiap peringkat menampilkan ${c.free_row_limit} baris teratas di halaman 1, dan fitur berbayar ditandai terkunci.
         Ganti cookie dengan akun berlangganan untuk membuka semuanya.</div></div>`
      : `<div class="banner info"><span class="ico">★</span><div><b>Akun FastMoss berlangganan terpasang (${esc(a.nickname || "")}).</b> ${esc(a.plan || "")}${a.expire_at ? ` · berlaku s/d ${fmtTs(a.expire_at, false)}` : ""}</div></div>`;
  };
  draw();
  if (!S.account) loadAccount().then(draw);
}

// ============================================================ kontrol filter
function weekToInput(v) { const m = /^(\d{4})-(\d{1,2})$/.exec(v || ""); return m ? `${m[1]}-W${m[2].padStart(2, "0")}` : ""; }
function inputToWeek(v) { const m = /^(\d{4})-W(\d{2})$/.exec(v || ""); return m ? `${m[1]}-${m[2]}` : ""; }

function optionList(opts, key) {
  if (!opts) return [];
  return opts[key] || [];
}

function selectHTML(param, label, list, value, extra = "") {
  return `<div class="field"><label>${esc(label)}</label><select class="select" data-param="${esc(param)}" ${extra}>`
    + `<option value="">Semua</option>` + list.map((o) => `<option value="${esc(o.v)}" ${String(o.v) === String(value ?? "") ? "selected" : ""}>${esc(o.l)}</option>`).join("")
    + `</select></div>`;
}

/**
 * Gambar kontrol menu ke `wrap` (baris utama) & `adv` (filter lanjutan).
 * `state` diubah langsung; `apply()` dipanggil saat pengguna memilih.
 */
async function mountControls(controls, state, wrap, adv, apply, applied = {}) {
  const sources = [...new Set(controls.filter((c) => c.source).map((c) => c.source))];
  const loaded = Object.fromEntries(await Promise.all(sources.map(async (s) => [s, await getOptions(s)])));
  const parts = { main: [], adv: [] };
  for (const c of controls) {
    let html = "";
    if (c.kind === "text") {
      html = `<div class="field grow"><label>${esc(c.label)}</label><input class="input" data-param="${esc(c.param)}" value="${esc(state[c.param] || "")}" placeholder="Ketik lalu Enter"></div>`;
    } else if (c.kind === "select") {
      const val = state[c.param] ?? c.default;
      html = `<div class="field"><label>${esc(c.label)}</label><select class="select" data-param="${esc(c.param)}">`
        + c.options.map(([v, l]) => `<option value="${esc(v)}" ${String(v) === String(val) ? "selected" : ""}>${esc(l)}</option>`).join("") + `</select></div>`;
    } else if (c.kind === "period") {
      const dt = String(state.date_type || c.default || 1);
      const val = state.date_value || applied.date_value || "";
      const input = dt === "2" ? `<input class="input" type="week" data-period="2" value="${esc(weekToInput(val))}">`
        : dt === "3" ? `<input class="input" type="month" data-period="3" value="${esc(val)}">`
          : `<input class="input" type="date" data-period="1" value="${esc(val)}">`;
      html = `<div class="field"><label>${esc(c.label)}</label><div class="period"><div class="seg">`
        + c.options.map(([v, l]) => `<button type="button" data-dt="${v}" class="${String(v) === dt ? "on" : ""}">${esc(l)}</button>`).join("")
        + `</div>${input}</div></div>`;
    } else if (c.kind === "date") {
      const val = state[c.params[0]] || applied[c.params[0]] || "";
      html = `<div class="field"><label>${esc(c.label)}</label><input class="input" type="date" data-date="${esc(c.params.join(","))}" value="${esc(val)}"></div>`;
    } else if (c.kind === "category") {
      const tree = optionList(loaded[c.source], "category");
      let list = tree, cells = "";
      c.levels.forEach((lv, i) => {
        if (i > 0 && !list.length) return;
        const v = state[lv] || "";
        cells += selectHTML(lv, ["Kategori", "Sub-kategori", "Kategori detail"][i] || lv, list, v, `data-cat="${i}"`);
        const picked = list.find((o) => String(o.v) === String(v));
        list = picked && picked.sub ? picked.sub : [];
      });
      html = cells;
    } else if (c.kind === "dynselect") {
      html = selectHTML(c.param, c.label, optionList(loaded[c.source], c.key), state[c.param]);
    }
    parts[c.advanced ? "adv" : "main"].push(html);
  }
  wrap.insertAdjacentHTML("afterbegin", parts.main.join(""));
  if (adv) adv.innerHTML = parts.adv.join("");
  const scope = [wrap, adv].filter(Boolean);
  const each = (sel, fn) => scope.forEach((s) => $$(sel, s).forEach(fn));

  each("select[data-param]", (s) => s.addEventListener("change", () => {
    state[s.dataset.param] = s.value;
    if (s.dataset.cat != null) {
      const ctl = controls.find((c) => c.kind === "category");
      ctl.levels.slice(+s.dataset.cat + 1).forEach((lv) => delete state[lv]);
    }
    apply();
  }));
  each("input[data-param]", (i) => i.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { state[i.dataset.param] = i.value.trim(); apply(); }
  }));
  each("input[data-param]", (i) => i.addEventListener("change", () => { state[i.dataset.param] = i.value.trim(); }));
  each("[data-dt]", (b) => b.addEventListener("click", () => {
    state.date_type = b.dataset.dt;
    delete state.date_value;
    apply();
  }));
  each("input[data-period]", (i) => i.addEventListener("change", () => {
    state.date_value = i.dataset.period === "2" ? inputToWeek(i.value) : i.value;
    apply();
  }));
  each("input[data-date]", (i) => i.addEventListener("change", () => {
    i.dataset.date.split(",").forEach((p) => { state[p] = i.value; });
    apply();
  }));
  return parts.adv.length;
}

// ============================================================ halaman daftar (menu)
async function pageList(el, key, q) {
  const menu = S.catalog.menus.find((m) => m.key === key);
  if (!menu) { el.innerHTML = `<div class="empty">Menu tidak ditemukan.</div>`; return; }
  const token = S.token;
  const state = { ...q };
  const page = Math.max(1, parseInt(q.page || "1", 10));
  const free = S.account ? S.account.is_free : true;
  const apply = () => { delete state.page; go(`/m/${key}`, state); };

  el.innerHTML = `<div class="page-head"><div><div class="crumb">${esc(menu.group)}</div><h1>${esc(menu.title)}</h1><p>${esc(menu.desc)}</p></div></div>
    <div class="card"><div class="filters" id="flt">
        ${menu.sorts.length ? `<div class="field"><label>Urutkan</label><select class="select" id="sortSel">${menu.sorts.map(([v, l]) => `<option value="${esc(v)}" ${String(state.order || menu.sorts[0][0]) === v ? "selected" : ""}>${esc(l)}</option>`).join("")}</select></div>` : ""}
        <div class="field" style="min-width:auto;flex-direction:row;gap:8px;align-items:flex-end">
          <button class="btn primary" id="applyBtn">Terapkan</button>
          <button class="btn" id="advBtn" style="display:none">Filter lanjutan</button>
          <button class="btn ghost" id="resetBtn">Atur ulang</button>
        </div>
      </div><div class="adv" id="adv"></div></div>
    <div id="msg"></div>
    <div class="card table-card"><div class="table-tools"><div class="info" id="info"><span class="spinner"></span> Memuat data…</div><div class="spacer" style="flex:1"></div>
      ${!free ? `<select class="select" id="pagesSel" title="Jumlah halaman yang diekspor" style="height:30px"><option value="1">Ekspor 1 halaman</option><option value="5">5 halaman</option><option value="10">10 halaman</option><option value="50">Maks.</option></select>` : ""}
      <span id="exp"></span></div>
      <div id="tbl">${skeletonRows()}</div><div id="foot"></div><div class="pager" id="pager"></div></div>`;

  $("#applyBtn", el).addEventListener("click", () => {
    $$("input[data-param]", el).forEach((i) => { state[i.dataset.param] = i.value.trim(); });
    apply();
  });
  $("#resetBtn", el).addEventListener("click", () => go(`/m/${key}`));
  $("#sortSel", el)?.addEventListener("change", (e) => { state.order = e.target.value; apply(); });

  const qs = new URLSearchParams(Object.entries(q).filter(([k]) => k !== "page"));
  const expBase = () => `/api/export/list/${key}?${qs.toString()}${$("#pagesSel", el) ? `&pages=${$("#pagesSel", el).value}` : ""}`;
  const drawExp = () => { $("#exp", el).innerHTML = exportButtons(expBase()); bindExports($("#exp", el)); };
  drawExp();
  $("#pagesSel", el)?.addEventListener("change", drawExp);

  const dataP = api(`/api/list/${key}`, q).catch((e) => ({ status: "error", message: e.message, rows: [] }));
  const nAdv = await mountControls(menu.controls, state, $("#flt", el), $("#adv", el), apply);
  if (token !== S.token) return;
  if (nAdv) {
    const btn = $("#advBtn", el);
    const active = menu.controls.filter((c) => c.advanced && state[c.param]).length;
    btn.style.display = "";
    btn.textContent = `Filter lanjutan${active ? ` (${active})` : ""}`;
    if (active) $("#adv", el).classList.add("open");
    btn.addEventListener("click", () => $("#adv", el).classList.toggle("open"));
  }

  const res = await dataP;
  if (token !== S.token) return;
  // isi nilai periode/tanggal bawaan yang dipakai server
  const pin = $("input[data-period]", el);
  if (pin && !pin.value && res.params?.date_value) pin.value = pin.dataset.period === "2" ? weekToInput(res.params.date_value) : res.params.date_value;
  $$("input[data-date]", el).forEach((i) => { if (!i.value) i.value = res.params?.[i.dataset.date.split(",")[0]] || ""; });

  $("#msg", el).innerHTML = (res.fallback ? `<div class="banner info"><span class="ico">ℹ️</span><div>${esc(res.message)}</div></div>` : "") + statusBanner(res, true);
  $("[data-retry]", el)?.addEventListener("click", () => route());
  if (res.status !== "ok") {
    $("#info", el).textContent = "Data tidak tersedia.";
    $("#tbl", el).innerHTML = `<div class="empty">${res.status === "locked" ? "🔒 Terkunci paket FastMoss." : "Tidak ada data."}</div>`;
    return;
  }
  const bits = [];
  if (res.total != null) bits.push(`${nfF.format(res.total)} data di FastMoss`);
  bits.push(`menampilkan ${res.rows.length} baris`);
  if (res.params?.date_value) bits.push(`periode ${res.params.date_value}`);
  if (res.update_at) bits.push(`diperbarui ${typeof res.update_at === "number" ? fmtTs(res.update_at) : esc(res.update_at)}`);
  if (res.cached) bits.push("dari cache");
  $("#info", el).innerHTML = bits.join(" · ");
  mountTable($("#tbl", el), menu.columns, res.rows, { offset: (page - 1) * menu.pagesize });
  $("#foot", el).innerHTML = lockedRowsNote(res);

  const lastPage = res.total ? Math.ceil(res.total / menu.pagesize) : null;
  const canNext = !res.limit && res.rows.length >= menu.pagesize && (!lastPage || page < lastPage);
  $("#pager", el).innerHTML = `<span class="muted" style="font-size:12.5px">Halaman ${page}${lastPage ? ` dari ${nfF.format(lastPage)}` : ""}</span>
    <button class="btn sm" id="prev" ${page <= 1 ? "disabled" : ""}>‹ Sebelumnya</button>
    <button class="btn sm" id="next" ${canNext ? "" : "disabled"} title="${res.limit ? "Terkunci paket gratis" : ""}">${res.limit ? "🔒 " : ""}Berikutnya ›</button>`;
  $("#prev", el).addEventListener("click", () => go(`/m/${key}`, { ...q, page: page - 1 }));
  $("#next", el).addEventListener("click", () => go(`/m/${key}`, { ...q, page: page + 1 }));
}

function skeletonRows(n = 5) {
  return `<div style="padding:16px;display:grid;gap:14px">${Array.from({ length: n }, () => `<div class="skeleton"></div>`).join("")}</div>`;
}

// ============================================================ grafik
const charts = new Set();
function chartColor() {
  return getComputedStyle(document.documentElement).getPropertyValue("--chart").trim() || "#e0294f";
}
function chartInk() {
  const cs = getComputedStyle(document.documentElement);
  return { text: cs.getPropertyValue("--muted").trim(), grid: cs.getPropertyValue("--line").trim() };
}
// Kunci terjemahan FastMoss yang ikut terkirim sebagai nilai (mis. "common.goods.affiliate").
const I18N = { product_card: "Kartu produk", shop_account: "Akun toko", affiliate: "Afiliasi (kreator)",
  video: "Video", live: "LIVE", GMV: "Omzet", unitsSold: "Terjual" };
function shortLabel(v) {
  let s = String(v ?? "");
  if (/^common\.[\w.]+$/.test(s)) { const k = s.split(".").pop(); s = I18N[k] || k.replace(/_/g, " "); }
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(s)) return s.slice(11, 16);
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s.slice(5);
  return s.length > 28 ? `${s.slice(0, 27)}…` : s;
}
function fmtBy(type, v) {
  return type === "money" ? cur() + nfC.format(v) : nfC.format(v);
}

// FastMoss kadang mengirim deret lengkap tapi isinya nol semua (mis. akun tak aktif: 24 jam x 0 video);
// grafik kosong dengan sumbu "0-1" membingungkan, jadi tampilkan keterangan saja.
const ZERO_HTML = `<div class="empty">Semua nilainya 0 — belum ada aktivitas yang tercatat FastMoss pada periode ini.</div>`;
const allZero = (vals) => vals.every((v) => !v);

function lineChart(box, rows, x, series) {
  if (series.every((s) => allZero(rows.map((r) => toNum(dig(r, s.key)))))) { box.innerHTML = ZERO_HTML; return; }
  if (!window.Chart) return fallbackTable(box, rows, [{ label: "Tanggal", type: "text", key: x }, ...series]);
  let idx = 0;
  box.innerHTML = `${series.length > 1 ? `<div class="seg" style="margin-bottom:10px;flex-wrap:wrap">${series.map((s, i) => `<button type="button" data-s="${i}" class="${i ? "" : "on"}">${esc(s.label)}</button>`).join("")}</div>` : ""}
    <div class="chart-box"><canvas></canvas></div>
    <details style="margin-top:8px"><summary class="faint" style="cursor:pointer;font-size:12px">Lihat sebagai tabel</summary><div class="tbl"></div></details>`;
  const ink = chartInk();
  const ctx = $("canvas", box);
  const color = chartColor();
  const data = (i) => rows.map((r) => toNum(dig(r, series[i].key)) ?? null);
  // jumlah (bukan uang/rasio) yang semuanya bulat -> sumbu tanpa pecahan (hindari "2,5 video")
  const whole = (i) => (series[i].type === "num" && data(i).every((v) => v == null || Number.isInteger(v)) ? 0 : undefined);
  const chart = new Chart(ctx, {
    type: "line",
    data: { labels: rows.map((r) => shortLabel(dig(r, x))), datasets: [{ label: series[0].label, data: data(0), borderColor: color, backgroundColor: color + "22", fill: true, borderWidth: 2, pointRadius: rows.length > 40 ? 0 : 3, pointHoverRadius: 5, tension: 0 }] },
    options: {
      responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => `${series[idx].label}: ${series[idx].type === "money" ? cur() : ""}${nfF.format(c.parsed.y)}` } } },
      scales: {
        x: { grid: { display: false }, ticks: { color: ink.text, maxRotation: 0, autoSkip: true, maxTicksLimit: 8 } },
        y: { grid: { color: ink.grid }, border: { display: false }, ticks: { color: ink.text, callback: (v) => fmtBy(series[idx].type, v),
          precision: whole(0) } },
      },
    },
  });
  charts.add(chart);
  $$("[data-s]", box).forEach((b) => b.addEventListener("click", () => {
    idx = +b.dataset.s;
    $$("[data-s]", box).forEach((x2) => x2.classList.toggle("on", x2 === b));
    chart.data.datasets[0].data = data(idx);
    chart.data.datasets[0].label = series[idx].label;
    chart.options.scales.y.ticks.precision = whole(idx);
    chart.update();
  }));
  mountTable($(".tbl", box), [{ label: "Waktu", type: "text", key: x }, ...series], rows);
}

function barChart(box, rows, x, series) {
  const val = (r) => {
    const v = dig(r, series[0].key);
    return toNum(v) ?? (typeof v === "string" ? parseFloat(v.replace("%", "").replace(",", ".")) || 0 : 0);
  };
  const label = (r) => labelText(dig(r, x));
  if (!window.Chart || !rows.length) return fallbackTable(box, rows, [{ label: "Label", type: "text", key: x }, ...series]);
  const ink = chartInk();
  const color = chartColor();
  const vals = rows.map(val);
  if (allZero(vals)) { box.innerHTML = ZERO_HTML; return; }
  // banyak kategori berlabel pendek (mis. 24 jam) -> batang tegak supaya tidak memanjang ke bawah
  const upright = rows.length > 12 && rows.every((r) => label(r).length <= 8);
  const vAxis = upright ? "y" : "x";
  const whole = series[0].type === "num" && vals.every((v) => Number.isInteger(v));
  box.innerHTML = `<div class="chart-box" style="height:${upright ? 240 : Math.max(160, rows.length * 34 + 40)}px"><canvas></canvas></div>`;
  const valueTicks = { color: ink.text, callback: (v) => fmtBy(series[0].type, v), ...(whole ? { precision: 0 } : {}) };
  const chart = new Chart($("canvas", box), {
    type: "bar",
    data: { labels: rows.map((r) => shortLabel(label(r))), datasets: [{ label: series[0].label, data: vals, backgroundColor: color, borderRadius: 4, borderSkipped: "start", maxBarThickness: 18 }] },
    options: {
      indexAxis: upright ? "x" : "y", responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => `${series[0].label}: ${series[0].type === "money" ? cur() : ""}${nfF.format(c.parsed[vAxis])}` } } },
      scales: {
        [vAxis]: { grid: { color: ink.grid }, border: { display: false }, beginAtZero: true, ticks: valueTicks,
          ...(series[0].type === "money" ? { min: 0 } : {}) },   // omzet tak mungkin minus (sisa "Lainnya" kadang minus)
        [upright ? "x" : "y"]: { grid: { display: false }, ticks: { color: ink.text, autoSkip: upright, maxRotation: 0 } },
      },
    },
  });
  charts.add(chart);
}

function fallbackTable(box, rows, cols) {
  mountTable(box, cols, rows || []);
}

// ============================================================ penggambar bagian (detail & pasar)
function kpiHTML(fields, data) {
  if (!data || typeof data !== "object") return `<div class="empty">Tidak ada data.</div>`;
  let items = fields.map((f) => ({ l: f.label, v: cell(f, data) }));
  if (!items.length) {
    items = autoFields(data, 16).map((f) => ({ l: f.label, v: !blank(f.show) ? esc(f.show) : f.num ? fmtNum(data[f.k]) : esc(data[f.k]) }));
  }
  if (!items.length) return `<div class="empty">Tidak ada data.</div>`;
  return `<div class="grid k4">${items.map((i) => `<div class="kpi card" style="box-shadow:none"><div class="l">${esc(i.l)}</div><div class="v num">${i.v}</div></div>`).join("")}</div>`;
}

function kvHTML(fields, data) {
  return `<div class="kv">${fields.map((f) => `<div><span>${esc(f.label)}</span><span>${cell(f, data)}</span></div>`).join("")}</div>`;
}

function heroHTML(sec, data, kind, id) {
  const p = sec.profile || {};
  const title = dig(data, p.title) || "(tanpa nama)";
  const img = dig(data, p.img);
  let sub = dig(data, p.sub);
  sub = blank(sub) ? "" : `${p.sub_prefix || ""}${sub}`;
  const subLink = p.sub_link ? dig(data, p.sub_link[1]) : "";
  const tagList = (p.tags || []).flatMap((t) => { const v = dig(data, t); return blank(v) ? [] : (Array.isArray(v) ? v : [v]); });
  let ext = p.url ? dig(data, p.url) : "";
  if (p.url_tpl) ext = p.url_tpl.replace(/\{(\w+)\}/g, (_, k) => encodeURIComponent(dig(data, k) ?? ""));
  const fmPath = { product: "e-commerce/detail", shop: "shop-marketing/detail", creator: "influencer/detail", live: "live/detail", video: "media-source/video" }[kind];
  return `<div class="card"><div class="hero ${p.round ? "round" : ""}">
      ${img ? `<img src="${esc(img)}" alt="" referrerpolicy="no-referrer">` : ""}
      <div style="flex:1;min-width:240px"><h1>${esc(title)}</h1>
        ${sub ? `<div class="muted" style="margin-top:4px">${subLink ? `<a href="#/detail/${p.sub_link[0]}/${esc(subLink)}" style="text-decoration:underline">${esc(sub)}</a>` : esc(sub)}</div>` : ""}
        <div class="meta">${[...new Set(tagList)].slice(0, 6).map((t) => `<span class="pill">${esc(t)}</span>`).join("")}</div>
        <div class="meta" style="margin-top:10px">
          ${ext ? `<a class="btn sm" href="${esc(ext)}" target="_blank" rel="noopener">Buka di TikTok ↗</a>` : ""}
          <a class="btn sm" href="https://www.fastmoss.com/id/${fmPath}/${esc(id)}" target="_blank" rel="noopener">Buka di FastMoss ↗</a>
        </div></div></div>
    <div style="padding:0 20px 18px">${kpiHTML(sec.fields, data)}</div>
    ${sec.series.length ? `<div style="padding:0 20px 20px">${kvHTML(sec.series, data)}</div>` : ""}</div>`;
}

/** Muat & gambar satu bagian ke dalam kartu `card`. */
async function loadSection(card, sec, url, state, token, exportUrl) {
  const body = $(".sec-body", card);
  body.innerHTML = skeletonRows(3);
  let res;
  try { res = await api(url, state); } catch (e) { res = { status: "error", message: e.message }; }
  if (token !== S.token) return;
  if (res.status !== "ok") {
    body.innerHTML = statusBanner(res, true) || `<div class="empty">Tidak ada data.</div>`;
    $("[data-retry]", body)?.addEventListener("click", () => loadSection(card, sec, url, state, token, exportUrl));
    if (res.status === "locked") card.classList.add("is-locked");
    return;
  }
  const d = res.data;
  if (sec.view === "kpi") body.innerHTML = kpiHTML(sec.fields, d);
  else if (sec.view === "kv") body.innerHTML = kvHTML(sec.fields, d || {});
  else if (sec.view === "pairs") {
    const rows = Array.isArray(d) ? d : [];
    body.innerHTML = rows.length ? `<div class="kv">${rows.map((r) => `<div><span>${esc(dig(r, sec.x))}</span><span>${esc(dig(r, sec.series[0].key))}</span></div>`).join("")}</div>` : `<div class="empty">Tidak ada data.</div>`;
  } else if (sec.view === "line") {
    const rows = Array.isArray(d) ? d : [];
    if (!rows.length) body.innerHTML = `<div class="empty">Belum ada data tren.</div>`;
    else lineChart(body, rows, sec.x, sec.series);
  } else if (sec.view === "bars") {
    const rows = Array.isArray(d) ? d : [];
    if (sec.x && rows.length) barChart(body, rows, sec.x, sec.series);
    else body.innerHTML = kpiHTML([], d);
  } else if (sec.view === "table") {
    const cols = sec.fields.length ? sec.fields : autoCols(res.rows);
    const page = res.page || 1;
    body.innerHTML = `<div class="tbl"></div>${lockedRowsNote(res)}${sec.paged ? `<div class="pager"></div>` : ""}`;
    mountTable($(".tbl", body), cols, res.rows || [], { offset: (page - 1) * 10 });
    if (sec.paged) {
      const canNext = !res.limit && (res.rows || []).length >= 10 && (!res.total || page * 10 < res.total);
      const pg = $(".pager", body);
      pg.innerHTML = `<span class="muted" style="font-size:12.5px">${res.total != null ? `${nfF.format(res.total)} data · ` : ""}hal. ${page}</span>
        <button class="btn sm" data-p="-1" ${page <= 1 ? "disabled" : ""}>‹</button><button class="btn sm" data-p="1" ${canNext ? "" : "disabled"}>${res.limit ? "🔒 " : ""}›</button>`;
      $$("[data-p]", pg).forEach((b) => b.addEventListener("click", () => {
        state.page = page + +b.dataset.p;
        loadSection(card, sec, url, state, token, exportUrl);
      }));
    }
    const tools = $(".sec-tools", card);
    if (exportUrl && tools && !tools.dataset.done) {
      tools.dataset.done = "1";
      tools.innerHTML = exportButtons(exportUrl);
      bindExports(tools);
    }
  }
}

function sectionCard(sec) {
  const ctl = (sec.controls || []).map((c) => `<select class="select" data-ctl="${esc(c.param)}" style="height:30px">`
    + c.options.map(([v, l]) => `<option value="${esc(v)}" ${String(v) === String(c.default) ? "selected" : ""}>${esc(l)}</option>`).join("") + `</select>`).join("");
  return `<section class="card card-pad sec" data-sec="${esc(sec.key)}" style="${sec.wide || sec.view === "table" || sec.view === "kpi" ? "grid-column:1/-1" : ""}">
    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:12px">
      <h3 class="card-title" style="margin:0;flex:1">${esc(sec.title)}</h3>${ctl}<span class="sec-tools" style="display:flex;gap:6px"></span></div>
    ${sec.note ? `<p class="faint" style="margin:-6px 0 10px;font-size:12.5px">${esc(sec.note)}</p>` : ""}
    <div class="sec-body"></div></section>`;
}

function mountSections(grid, sections, urlFor, baseState, token, exportFor) {
  grid.innerHTML = sections.map(sectionCard).join("");
  for (const sec of sections) {
    const card = $(`[data-sec="${sec.key}"]`, grid);
    const state = { ...baseState };
    (sec.controls || []).forEach((c) => { state[c.param] = c.default; });
    const run = () => loadSection(card, sec, urlFor(sec), state, token, exportFor ? exportFor(sec, state) : null);
    $$("[data-ctl]", card).forEach((s) => s.addEventListener("change", () => {
      state[s.dataset.ctl] = s.value;
      delete state.page;
      run();
    }));
    run();
  }
}

// ============================================================ halaman detail
async function pageDetail(el, kind, id, q) {
  const det = S.catalog.details[kind];
  if (!det || !/^[\w-]+$/.test(id)) { el.innerHTML = `<div class="empty">Halaman detail tidak dikenal.</div>`; return; }
  const token = S.token;
  const tab = Math.min(Math.max(parseInt(q.tab || "0", 10) || 0, 0), det.tabs.length - 1);
  const profKey = Object.values(det.sections).find((s) => s.view === "profile")?.key;
  el.innerHTML = `<div class="page-head"><div><div class="crumb"><a href="javascript:history.back()">‹ Kembali</a> · ${esc(det.title)}</div></div></div>
    <div id="hero">${skeletonRows(4)}</div>
    <nav class="tabs">${det.tabs.map(([t], i) => `<a href="#/detail/${kind}/${esc(id)}?tab=${i}" class="${i === tab ? "on" : ""}">${esc(t)}</a>`).join("")}</nav>
    <div class="grid c2" id="secs"></div>`;
  if (profKey) {
    api(`/api/detail/${kind}/${id}/${profKey}`).then((res) => {
      if (token !== S.token) return;
      $("#hero", el).innerHTML = res.status === "ok" ? heroHTML(det.sections[profKey], res.data || {}, kind, id) : statusBanner(res, false);
    }).catch((e) => { $("#hero", el).innerHTML = statusBanner({ status: "error", message: e.message }); });
  }
  const keys = det.tabs[tab][1].filter((k) => k !== profKey);
  const secs = keys.map((k) => det.sections[k]).filter(Boolean);
  mountSections($("#secs", el), secs, (s) => `/api/detail/${kind}/${id}/${s.key}`, {}, token,
    (s, st) => (s.view === "table" ? `/api/export/detail/${kind}/${id}/${s.key}?${new URLSearchParams(Object.entries(st).filter(([k]) => k !== "page")).toString()}` : null));
}

// ============================================================ halaman tren pasar
async function pageMarket(el, key, q) {
  const pg = S.catalog.market.find((p) => p.key === key);
  if (!pg) { el.innerHTML = `<div class="empty">Halaman tidak ditemukan.</div>`; return; }
  const token = S.token;
  const state = { ...q };
  el.innerHTML = `<div class="page-head"><div><div class="crumb">Tren Pasar</div><h1>${esc(pg.title)}</h1><p>${esc(pg.desc)}</p></div></div>
    <div class="card"><div class="filters" id="flt"></div></div>
    ${S.account?.is_free ? `<div class="banner lock"><span class="ico">🔒</span><div>Paket gratis: data <b>harian</b> untuk <b>semua kategori</b>. Pilihan kategori & periode mingguan/bulanan akan menampilkan status terkunci.</div></div>` : ""}
    <div class="grid c2" id="secs" style="margin-top:14px"></div>`;
  await mountControls(pg.controls, state, $("#flt", el), null, () => go(`/market/${key}`, state));
  if (token !== S.token) return;
  mountSections($("#secs", el), pg.sections, (s) => `/api/market/${key}/${s.key}`, state, token,
    (s) => (s.view === "table" ? `/api/export/market/${key}/${s.key}?${new URLSearchParams(q).toString()}` : null));
}

// ============================================================ pengaturan
async function pageSettings(el, q = {}) {
  const token = S.token;
  const admin = !S.me || S.me.role === "admin";
  el.innerHTML = `<div class="page-head"><div><div class="crumb">Sistem</div><h1>Pengaturan & Cookie</h1>
      <p>Daftar akun FastMoss yang tersedia. Pilih akun yang Anda pakai — pilihan tersimpan di perangkat ini saja.</p></div></div>
    <div class="grid c2">
      <section class="card card-pad"><h3 class="card-title">Akun yang Anda pakai</h3><div id="acc">${skeletonRows(3)}</div>
        <div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap"><button class="btn" id="refAcc">Cek ulang semua akun</button>${admin ? `<button class="btn" id="clrCache">Kosongkan cache</button>` : ""}</div></section>
      <section class="card card-pad"><h3 class="card-title">Cara kerja multi-akun</h3>
        <ul class="muted" style="margin:0;padding-left:18px;line-height:1.75">
          <li>Satu akun = satu file di server: <code>config/cookies_akun_1.txt</code>, <code>cookies_akun_2.txt</code>, dst.</li>
          <li>Baris <code># nama: …</code> di file = nama akun yang tampil di pilihan akun.</li>
          <li>Tiap akun punya cache & status paket sendiri — data akun gratis dan berlangganan tidak tercampur.</li>
          <li>Isi / ganti cookie: klik <b>Isi cookie</b> / <b>Ganti cookie</b> pada tabel, lalu tempel cURL apa adanya atau pilih file .txt. Bisa juga edit file akunnya langsung (terbaca tanpa restart).</li>
        </ul></section>
      <section class="card card-pad" style="grid-column:1/-1">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:10px"><h3 class="card-title" style="margin:0">Daftar akun FastMoss</h3>
        ${admin ? `<button class="btn sm" id="addAcc">+ Tambah slot akun</button>` : ""}</div><div id="accList">${skeletonRows(3)}</div></section>
      ${admin ? `<section class="card card-pad" style="grid-column:1/-1" id="editor"><h3 class="card-title">Isi / ganti cookie akun</h3>
        <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px">
          <div class="field"><label for="ckAcc">Akun</label><select class="select" id="ckAcc"></select></div>
          <div class="field" style="flex:1;min-width:220px"><label for="ckLabel">Nama akun</label><input class="input" id="ckLabel" maxlength="60" placeholder="mis. Akun Berlangganan Tim"></div>
        </div>
        <ol class="muted" style="margin:0 0 12px;padding-left:18px;line-height:1.7">
          <li>Buka <a href="https://www.fastmoss.com/id" target="_blank" rel="noopener" style="text-decoration:underline">fastmoss.com</a> di Chrome dengan akun yang mau dipasang.</li>
          <li>Tekan <b>F12</b> → tab <b>Network</b> → muat ulang halaman → klik salah satu request <code>/api/…</code>.</li>
          <li>Klik kanan → <b>Copy → Copy as cURL</b> (cmd maupun bash), lalu tempel <b>apa adanya</b> di bawah — tanda <code>^</code> dan sejenisnya dibersihkan otomatis.</li>
        </ol>
        <div class="drop" id="ckDrop">
          <textarea class="input" id="ckText" rows="6" style="width:100%" spellcheck="false" autocomplete="off"
            placeholder="Tempel di sini: cURL (cmd/bash), header Cookie, isi cookie, PowerShell, atau ekspor JSON ekstensi cookie. Bisa juga seret file .txt ke kotak ini. Kosongkan bila hanya mengganti nama akun."></textarea>
          <div class="drop-hint">Lepaskan file untuk membaca isinya</div>
        </div>
        <div id="ckDetect" class="faint" style="font-size:12.5px;margin-top:6px;min-height:18px"></div>
        <div style="margin-top:8px;display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          <button class="btn primary" id="ckSave">Simpan & uji</button>
          <label class="btn" for="ckFile" style="cursor:pointer">Pilih file…</label>
          <input type="file" id="ckFile" accept=".txt,.json,.har,text/plain,application/json" hidden>
          <button class="btn ghost" id="ckClear" type="button">Kosongkan</button>
          <span id="ckMsg" class="muted"></span></div>
      </section>` : `<section class="card card-pad" style="grid-column:1/-1"><p class="muted" style="margin:0">Mengganti cookie atau menambah akun butuh kata sandi admin.</p></section>`}
    </div>`;

  const planPill = (a) => (!a.cookie?.exists ? `<span class="pill">Belum ada cookie</span>`
    : !a.logged_in ? `<span class="pill bad">Cookie bermasalah</span>`
      : a.is_free ? `<span class="pill lock">🔒 ${esc(a.plan)}</span>` : `<span class="pill ok">★ ${esc(a.plan)}</span>`);

  const drawAcc = () => {
    if (token !== S.token) return;
    const a = S.accounts.find((x) => x.id === S.acc);
    if (!a) { $("#acc", el).innerHTML = statusBanner({ status: "error", message: "Belum ada akun. Tambah slot akun lalu isi cookie-nya." }); return; }
    $("#acc", el).innerHTML = `<div class="kv">
      <div><span>Akun</span><span>${esc(a.label)}</span></div>
      <div><span>Paket</span><span>${planPill(a)}</span></div>
      <div><span>Nama FastMoss</span><span>${esc(a.nickname || "–")}</span></div>
      <div><span>Berlaku s/d</span><span>${a.expire_at ? fmtTs(a.expire_at, false) : "–"}</span></div>
      <div><span>Batas baris tampil</span><span>${!a.logged_in ? "–" : a.is_free ? `${S.catalog.free_row_limit} baris teratas (halaman 1)` : "Sesuai paket"}</span></div></div>
      ${a.logged_in || !a.message ? "" : `<p class="faint" style="font-size:12.5px;margin:10px 0 0">${esc(a.message)}</p>`}`;
  };

  const pickEditor = (id) => {
    const sel = $("#ckAcc", el);
    if (!sel) return;
    sel.value = id;
    $("#ckLabel", el).value = S.accounts.find((a) => a.id === id)?.label || "";
  };

  const drawList = () => {
    if (token !== S.token) return;
    const box = $("#accList", el);
    if (!S.accounts.length) { box.innerHTML = `<div class="empty">Belum ada file akun di folder config.</div>`; return; }
    const cols = [
      { label: "Akun", type: "html", key: "_name" }, { label: "Paket", type: "html", key: "_plan" },
      { label: "Nama FastMoss", type: "text", key: "nickname" }, { label: "Berlaku s/d", type: "date", key: "expire_at" },
      { label: "Cookie diubah", type: "html", key: "_upd" }, { label: "", type: "html", key: "_act" },
    ];
    const rows = S.accounts.map((a) => ({
      ...a,
      _name: `<b>${esc(a.label)}</b>${a.id === S.acc ? ` <span class="pill brand">dipakai</span>` : ""}<div class="faint" style="font-size:12px">config/${esc(a.file)}</div>`,
      _plan: planPill(a),
      _upd: a.cookie?.updated_at ? fmtTs(a.cookie.updated_at) : "–",
      _act: `<span style="white-space:nowrap">${a.id === S.acc ? "" : `<button class="btn sm" data-use="${esc(a.id)}">Pakai</button> `}`
        + `${!admin ? "" : a.cookie?.exists ? `<button class="btn sm ghost" data-edit="${esc(a.id)}">Ganti cookie</button>`
          : `<button class="btn sm primary" data-edit="${esc(a.id)}">Isi cookie</button>`}</span>`,
    }));
    box.innerHTML = `<div class="table-wrap"><table class="data" style="min-width:760px"><thead><tr><th>#</th>${cols.map((c) => `<th style="text-align:left">${esc(c.label)}</th>`).join("")}</tr></thead>
      <tbody>${rows.map((r) => `<tr><td>${esc(r.id)}</td>${cols.map((c) => `<td style="text-align:left">${c.type === "html" ? r[c.key] : cell(c, r)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
    $$("[data-use]", box).forEach((b) => b.addEventListener("click", () => setAccount(b.dataset.use)));
    $$("[data-edit]", box).forEach((b) => b.addEventListener("click", () => openEditor(b.dataset.edit)));
    const sel = $("#ckAcc", el);
    if (sel) {
      const keep = sel.value || S.acc;
      sel.innerHTML = S.accounts.map((a) => `<option value="${esc(a.id)}">${esc(a.id)} — ${esc(a.label)}</option>`).join("");
      pickEditor(S.accounts.some((a) => a.id === keep) ? keep : S.acc);
    }
  };

  const openEditor = (id) => {
    pickEditor(id);
    $("#editor", el)?.scrollIntoView({ behavior: "smooth", block: "start" });
    setTimeout(() => $("#ckText", el)?.focus({ preventScroll: true }), 350);
  };

  const refresh = async (force = false) => {
    await loadAccounts(force);
    await loadAccount();
    drawAcc();
    drawList();
  };
  refresh().then(() => { if (q.edit && admin && S.accounts.some((a) => a.id === q.edit)) openEditor(q.edit); });

  // deteksi format otomatis saat menempel (server hanya membalas ringkasan, bukan nilai cookie)
  let detTimer = 0;
  let detSeq = 0;
  const detect = () => {
    clearTimeout(detTimer);
    const box = $("#ckDetect", el);
    const text = $("#ckText", el)?.value.trim() || "";
    if (!box) return;
    if (!text) { box.textContent = ""; return; }
    box.innerHTML = `<span class="spinner"></span> Mengenali format…`;
    detTimer = setTimeout(async () => {
      const seq = ++detSeq;
      try {
        const r = await api("/api/cookie/preview", {}, { method: "POST", body: { text }, noRegion: true });
        if (seq !== detSeq) return;
        box.innerHTML = !r.ok
          ? `<span style="color:var(--bad)">✗ ${r.format ? `${esc(r.format)} terbaca, tapi tidak ada cookie di dalamnya.` : "Cookie tidak terbaca dari teks ini."}</span>`
          : `<span style="color:var(--ok)">✓</span> Terbaca sebagai <b>${esc(r.format)}</b> · ${r.count} cookie · `
            + (r.has_session ? `sesi login <code>fd_tk</code> ada` : `<span style="color:var(--bad)">sesi login <code>fd_tk</code> tidak ada — kemungkinan belum login</span>`);
      } catch (e) { if (seq === detSeq) box.textContent = e.message; }
    }, 350);
  };
  const loadFile = async (file) => {
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) { toast("File terlalu besar (maks. 2 MB)."); return; }
    $("#ckText", el).value = await file.text();
    $("#ckMsg", el).textContent = `Dibaca dari ${file.name}`;
    detect();
  };
  $("#ckText", el)?.addEventListener("input", detect);
  $("#ckFile", el)?.addEventListener("change", (e) => { loadFile(e.target.files[0]); e.target.value = ""; });
  $("#ckClear", el)?.addEventListener("click", () => { $("#ckText", el).value = ""; $("#ckMsg", el).textContent = ""; detect(); });
  const drop = $("#ckDrop", el);
  if (drop) {
    ["dragenter", "dragover"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add("over"); }));
    ["dragleave", "drop"].forEach((t) => drop.addEventListener(t, () => drop.classList.remove("over")));
    drop.addEventListener("drop", (e) => {
      const f = e.dataTransfer?.files?.[0];
      if (f) { e.preventDefault(); loadFile(f); }
    });
  }

  $("#refAcc", el).addEventListener("click", () => refresh(true));
  $("#clrCache", el)?.addEventListener("click", async () => {
    try { await api("/api/cache/clear", {}, { method: "POST", noRegion: true }); toast("Cache semua akun dikosongkan."); } catch (e) { toast(e.message); }
  });
  $("#addAcc", el)?.addEventListener("click", async () => {
    try {
      const a = await api("/api/accounts", {}, { method: "POST", body: { label: "" }, noRegion: true });
      toast(`Slot ${a.label} dibuat: config/${a.file}`);
      await refresh();
      openEditor(a.id);
    } catch (e) { toast(e.message); }
  });
  $("#ckAcc", el)?.addEventListener("change", (e) => pickEditor(e.target.value));
  $("#ckSave", el)?.addEventListener("click", async () => {
    const account = $("#ckAcc", el).value;
    const text = $("#ckText", el).value.trim();
    const label = $("#ckLabel", el).value.trim();
    $("#ckMsg", el).innerHTML = `<span class="spinner"></span> Menyimpan${text ? " & menguji" : ""}…`;
    try {
      const a = await api("/api/cookie", {}, { method: "POST", body: { account, text, label }, noRegion: true });
      $("#ckText", el).value = "";
      $("#ckDetect", el).textContent = "";
      S.options = {};
      await refresh();
      $("#ckMsg", el).textContent = !text ? `Nama akun ${a.id} disimpan.`
        : a.logged_in ? `Tersimpan. ${a.label}: ${a.nickname || "?"} — ${a.plan || ""}` : `Tersimpan, tapi: ${a.message}`;
    } catch (e) { $("#ckMsg", el).textContent = `Gagal: ${e.message}`; }
  });
}

boot();
