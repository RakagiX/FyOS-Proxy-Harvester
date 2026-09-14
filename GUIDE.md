# ⚡ FyOS Proxy Harvester — Panduan Lengkap Penggunaan (Usage Guide)
**Created By : FyOS - ConFEx CCP**

Panduan praktis cara menggunakan **FyOS Proxy Harvester (ConFEx CCP)**, kustomisasi jumlah panen (50, 100, 500 proxy), filter negara, penggunaan Local Rotating Gateway, integrasi bot/scraper, dan akses ke **Interactive Obsidian Web Dashboard**.

---

## Daftar Isi
1. [Untuk Apa Saja Tool Ini Digunakan? (Real-World Use Cases)](#1-untuk-apa-saja-tool-ini-digunakan-real-world-use-cases)
2. [Cara Menjalankan Menu Interaktif Super-Premium](#2-cara-menjalankan-menu-interaktif-super-premium)
3. [Menggunakan Interactive Obsidian Web Dashboard](#3-menggunakan-interactive-obsidian-web-dashboard)
4. [Cara Panen Lebih dari 15 Proxy (Kustom Jumlah)](#4-cara-panen-lebih-dari-15-proxy-kustom-jumlah)
5. [Cara Menjalankan Local Rotating Proxy & REST API (Port 8888)](#5-cara-menjalankan-local-rotating-proxy--rest-api-port-8888)
6. [Cara Panen Khusus Proxy Tertentu](#6-cara-panen-khusus-proxy-tertentu)
   - [Khusus Proxy Elite L1 (High Anonymity)](#a-khusus-proxy-elite-l1-high-anonymity)
   - [Khusus Negara Tertentu (ID, SG, US, dll)](#b-khusus-negara-tertentu-id-sg-us-dll)
   - [Khusus Tembus Website Tertentu (Google, Shopee, xAI)](#c-khusus-tembus-website-tertentu-google-shopee-xai)
7. [Cara Integrasi ke Script Python / Scraper / Bot](#7-cara-integrasi-ke-script-python--scraper--bot)
8. [Tabel Semua Perintah CLI Lengkap](#8-tabel-semua-perintah-cli-lengkap)

---

## 1. Untuk Apa Saja Tool Ini Digunakan? (Real-World Use Cases)

Fungsi mendasar tool ini adalah menyediakan pasokan **IP proxy gratis tanpa batas** yang terus dirotasi secara otomatis dengan algoritma kesehatan cerdas (Adaptive EWMA). Berikut adalah skenario pemanfaatan terbesarnya:

1. **🕷️ Web Scraping Skala Besar**: Menghindari pemblokiran IP (*HTTP 429 Too Many Requests*) saat menyedot ribuan data marketplace (Shopee/Tokopedia), portal berita, atau media sosial.
2. **🤖 AI & LLM Load Balancing**: Membagi request bot AI (seperti bot WhatsApp / Grok / ChatGPT / Gemini / 9Router) ke puluhan IP agar tidak terkena limit rate API.
3. **👥 Otomasi Bot & Multi-Akun**: Mencegah bot kena banned atau deteksi checkpoint massal (Puppeteer, Playwright, Selenium) karena tiap instance browser memegang IP terisolasi.
4. **🌍 Audit SEO & Peringkat Google Regional**: Melihat hasil pencarian SERP dan tayangan iklan Google murni dari sudut pandang negara lain (misal: `--country US` atau `--country SG`).
5. **🛡️ Akses Bebas Sensor / Blokir ISP**: Membuka API publik atau forum developer global yang terblokir ISP lokal tanpa perlu bayar biaya VPN bulanan.
6. **🔒 Security Testing / Bug Bounty**: Mendistribusikan lalu lintas pengujian penetrasi endpoint agar tidak langsung memicu filter fail2ban server target.

---

## 2. Cara Menjalankan Menu Interaktif Super-Premium

Buka terminal di folder proyek:
```powershell
python main.py
```
Akan muncul banner terminal modern dengan tema Obsidian Neon dan penanda resmi **`Created By : FyOS - ConFEx CCP`**. Cukup tekan angka atau huruf opsi yang diinginkan:
- `[1]` : **Racikan Ternak Akun** (Grok, Qoder & Bot AI, Elite L1, Auto-BansosRouter)
- `[2]` : **Racikan Scraper Brutal** (Pool 30+ IP, rotasi tiap request)
- `[3]` : **Racikan Turbo Surfing** (Ping terendah <350ms, Node SG/ID/US)
- `[4]` : **Mode Daemon 24 Jam** (Auto-refresh tiap 15 menit di port 8888)
- `[W]` : **Webshare Residential Hunter** (IP perumahan lolos Cloudflare)
- `[D]` : **Buka Web Dashboard** (Membuka GUI Obsidian interaktif di browser)
- `[E]` : **Ekspor File Mentah** (Simpan format TXT, JSON, CSV & SOCKS5)
- `[T]` : **Uji Tembus Identitas** (Live proof audit perbandingan IP asli vs masked)
- `[M]` : **Bengkel Oprek Manual** (Atur protokol, filter negara ISO, target URL)
- `[S]` : **Gudang Hasil Panen** (Buka riwayat proxy aktif dalam tabel visual)
- `[L]` : **Ganti Bahasa** (Switch antara Bahasa Indonesia & English)
- `[0]` : **Keluar**

---

## 3. Menggunakan Interactive Obsidian Web Dashboard

Saat Anda menyalakan Gateway di port 8888 (atau menggunakan opsi `[D]`, `[7]`, atau flag `--serve 8888 --open-dashboard`), buka URL berikut di browser Anda:

```
http://127.0.0.1:8888/dashboard
```

### Fitur Web Dashboard:
- **Statistik Visual Real-time**: Memantau pool size aktif, average latency, total request yang ter-routing, dan availability rate.
- **Tabel Filter & Pencarian Cepat**: Cari proxy berdasarkan IP, nama negara, kode ISO, atau nama ISP.
- **Filter Chips**: 1-klik untuk menyaring hanya proxy *Elite*, *SOCKS5*, atau *HTTP*.
- **One-Click Copy**: Tombol instan untuk menyalin URL proxy (`http://ip:port`), format mentah, atau perintah cURL.
- **In-Browser Proxy Probe**: Masukkan URL target dan klik tombol uji coba untuk menguji langsung respon server melalui proxy yang sedang berputar.

---

## 4. Cara Panen Lebih dari 15 Proxy (Kustom Jumlah)

### Opsi A: Lewat Menu Interaktif
1. Jalankan `python main.py`.
2. Pilih opsi `[M]` (Bengkel Oprek) lalu pilih opsi `[1]`.
3. Masukkan jumlah yang Anda inginkan, misal: `50` atau `100`.

### Opsi B: Langsung Lewat CLI
```powershell
# Panen 50 proxy hidup tercepat:
python main.py --target 50 --max 800

# Panen 100 proxy hidup:
python main.py --target 100 --max 1500

# Panen 30 proxy khusus SOCKS5:
python main.py --protocol socks5 --target 30 --max 600
```

---

## 5. Cara Menjalankan Local Rotating Proxy & REST API (Port 8888)

Cukup jalankan:
```powershell
python main.py --serve 8888 --target 25 --open-dashboard
```
Terminal akan memvalidasi 25 proxy hidup terbaik, menyalakan gateway di `127.0.0.1:8888`, dan langsung membuka Web Dashboard di browser Anda!

### REST API Endpoints:
- `GET http://127.0.0.1:8888/api/random` — Ambil 1 proxy hidup tercepat secara acak.
- `GET http://127.0.0.1:8888/api/all` — Ambil seluruh daftar proxy hidup dalam JSON terstruktur.
- `GET http://127.0.0.1:8888/api/status` — Status kesehatan pool, total request, dan uptime gateway.

---

## 6. Cara Panen Khusus Proxy Tertentu

### A. Khusus Proxy Elite L1 (High Anonymity)
Proxy yang tidak menyuntikkan header proxy apapun dan menyamarkan diri secara sempurna:
```powershell
python main.py --anonymity elite --target 20
```

### B. Khusus Negara Tertentu (ID, SG, US, dll)
```powershell
# Khusus Indonesia:
python main.py --country ID --target 10

# Khusus Singapura:
python main.py --country SG --target 10

# Khusus Amerika Serikat:
python main.py --country US --target 20
```

### C. Khusus Tembus Website Tertentu (Google, Shopee, xAI)
```powershell
# Tes validasi langsung ke target Google:
python main.py --target-url https://google.com --target 10

# Tes validasi ke target Shopee:
python main.py --target-url https://shopee.co.id --target 10
```

---

## 7. Cara Integrasi ke Script Python / Scraper / Bot

### Contoh 1: Menggunakan Local Rotating Gateway (Rekomendasi Utama)
```python
import requests

# Arahkan scraper/crawler ke gateway lokal FyOS
proxies = {
    "http": "http://127.0.0.1:8888",
    "https": "http://127.0.0.1:8888"
}

for i in range(5):
    resp = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=10)
    print(f"Request #{i+1} menggunakan IP:", resp.json()["ip"])
```

### Contoh 2: Mengambil IP dari REST API secara Dinamis
```python
import requests

# Ambil 1 proxy acak dari FyOS REST API
api_resp = requests.get("http://127.0.0.1:8888/api/random").json()
proxy_url = api_resp["url"]
print(f"Menggunakan proxy: {proxy_url} ([{api_resp['country_code']}] {api_resp['country']})")

data = requests.get("https://api.ipify.org", proxies={"http": proxy_url, "https": proxy_url})
print("IP Terlihat:", data.text)
```

---

## 8. Tabel Semua Perintah CLI Lengkap

| Perintah | Fungsi |
| :--- | :--- |
| `python main.py` | Membuka TUI Menu Interaktif Super-Premium |
| `python main.py --target 50` | Panen 50 proxy hidup tercepat |
| `python main.py --protocol socks5 --target 20` | Panen 20 proxy khusus SOCKS5 |
| `python main.py --country ID --target 10` | Panen 10 proxy khusus lokasi Indonesia |
| `python main.py --anonymity elite --target 15` | Panen 15 proxy tingkat Elite L1 (Anti Bocor) |
| `python main.py --target-url https://google.com` | Validasi proxy langsung ke target web |
| `python main.py --serve 8888 --target 20` | Jalankan Rotating Forward Proxy & REST API di port 8888 |
| `python main.py --serve 8888 --open-dashboard` | Jalankan gateway dan otomatis buka Web Dashboard di browser |
| `python main.py --loop 15 --target 30` | Auto-refresh panen otomatis tiap 15 menit |
| `python main.py --sync-9router auto` | Sinkronisasi proxy otomatis ke 9Router SQLite |

---

*Created By : **FyOS - ConFEx CCP** | Enterprise Network Engineering*
