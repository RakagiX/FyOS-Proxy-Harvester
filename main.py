#!/usr/bin/env python3
"""
FyOS Proxy Harvester (ConFEx CCP) v2.5
Created By : FyOS - ConFEx CCP

State-of-the-Art Multi-Protocol Proxy Harvester, Intelligent Health-Scored Rotating Gateway,
Real-Time Network Profiler & Interactive Web Dashboard.
"""
import os
import sys
import time
import argparse
import webbrowser
import requests
from typing import Optional, List, Dict, Any

# Force UTF-8 encoding on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Rich Terminal UI with Colorama fallback
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.align import Align
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = Style = DummyColor()

from core.fetcher import fetch_proxies_sync
from core.checker import check_proxies_pool, DEFAULT_TEST_URL
from core.exporter import export_all_formats
from core.server import start_proxy_server
from core.glyphs import glyphs, supports_emojis

CURRENT_LANG = "ID"

ASCII_ART = r"""
  ███████╗██╗   ██╗ ██████╗ ███████╗    ██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗
  ██╔════╝╚██╗ ██╔╝██╔═══██╗██╔════╝    ██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝
  █████╗   ╚████╔╝ ██║   ██║███████╗    ██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝ 
  ██╔══╝    ╚██╔╝  ██║   ██║╚════██║    ██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝  
  ██║        ██║   ╚██████╔╝███████║    ██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║   
  ╚═╝        ╚═╝    ╚═════╝ ╚══════╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   """

def get_banner_text() -> str:
    z_l = glyphs.zap
    z_r = glyphs.zap_right
    return f"""{Fore.CYAN}{Style.BRIGHT}{ASCII_ART}{Style.RESET_ALL}
{Fore.YELLOW}       {z_l} FyOS PROXY HARVESTER v2.5 — Enterprise Multi-Protocol Engine {z_r}
{Fore.WHITE}       High-Speed Multi-Stage Scraper, Dual-Phase Latency & Rotating Gateway
{Fore.LIGHTBLACK_EX}                     Created By : {Fore.CYAN}{Style.BRIGHT}FyOS - ConFEx CCP{Fore.LIGHTBLACK_EX} (Official Release)
{Style.RESET_ALL}"""

def print_banner():
    if HAS_RICH and console:
        title_text = Text(ASCII_ART, style="bold cyan")
        sub_text = Text()
        z_l = glyphs.zap
        z_r = glyphs.zap_right
        sub_text.append(f"\n{z_l} FyOS PROXY HARVESTER v2.5 — Enterprise Multi-Protocol Engine {z_r}\n", style="bold yellow")
        sub_text.append("High-Speed Multi-Stage Scraper, Dual-Phase Latency & Rotating Gateway\n", style="white")
        sub_text.append("Created By : ", style="dim")
        sub_text.append("FyOS - ConFEx CCP", style="bold cyan")
        sub_text.append(" | Precision Network Engineering", style="dim")

        p = Panel(
            Align.center(Text.assemble(title_text, sub_text)),
            border_style="cyan",
            padding=(0, 2)
        )
        console.print(p)
    else:
        print(get_banner_text())

def find_9router_db() -> Optional[str]:
    """Auto-detection for 9Router / BansosRouter SQLite database via env or relative paths."""
    env_path = os.environ.get("BANSOS_ROUTER_DB") or os.environ.get("NINEROUTER_DB")
    if env_path and os.path.exists(env_path):
        return env_path

    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.normpath(os.path.join(base_dir, "..", "9router-mibp-version", "data", "db", "data.sqlite")),
        os.path.normpath(os.path.join(base_dir, "..", "9router", "data", "db", "data.sqlite")),
        os.path.normpath(os.path.join(base_dir, "..", "bansos-router", "data", "db", "data.sqlite")),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

def find_grok_python() -> str:
    """Detect python executable for Grok Farm / Webshare Hunter."""
    env_py = os.environ.get("GROK_PYTHON")
    if env_py and os.path.exists(env_py):
        return env_py
    candidates = [
        os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "grok-register", "venv", "Scripts", "python.exe")),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return sys.executable

def print_live_proxy(proxy_res: dict, current_count: int, target: int):
    proto = proxy_res.get("protocol", "http").upper()
    lat = proxy_res.get("latency_ms", 0)
    tcp_rtt = proxy_res.get("tcp_rtt_ms", lat // 2)
    proxy = proxy_res.get("proxy", "")
    cc = proxy_res.get("country_code", "??")
    country = proxy_res.get("country", "Unknown")
    isp = proxy_res.get("isp", "-")
    anon = proxy_res.get("anonymity", "Elite")
    
    # Anonymity badge styling
    if anon == "Elite":
        anon_badge = f"{Fore.CYAN}{Style.BRIGHT}[ELITE L1]{Style.RESET_ALL}"
    elif anon == "Anonymous":
        anon_badge = f"{Fore.MAGENTA}[ANON L2]{Style.RESET_ALL} "
    else:
        anon_badge = f"{Fore.YELLOW}[TRAN L3]{Style.RESET_ALL} "

    # Color based on latency
    if lat < 800:
        lat_color = Fore.GREEN
    elif lat < 2200:
        lat_color = Fore.YELLOW
    else:
        lat_color = Fore.RED

    live_badge = f"{glyphs.live_prefix}[LIVE {current_count:02d}/{target:02d}]"
    print(
        f"  {Fore.GREEN}{live_badge}{Style.RESET_ALL} "
        f"{Fore.CYAN}{proto:<6}{Style.RESET_ALL} "
        f"{Fore.WHITE}{proxy:<21}{Style.RESET_ALL} | "
        f"{anon_badge} | "
        f"{lat_color}{lat:>4}ms{Style.RESET_ALL} (TCP:{tcp_rtt:>3}ms) | "
        f"{Fore.BLUE}[{cc}] {country:<13}{Style.RESET_ALL} | "
        f"{Fore.LIGHTBLACK_EX}{isp[:20]}{Style.RESET_ALL}"
    )

def run_harvester(
    protocols: list, 
    max_check: int = 250, 
    target_alive: int = 20, 
    timeout: float = 3.0, 
    workers: int = 50, 
    country: str = None, 
    anonymity: str = None,
    target_url: str = None,
    output_dir: str = None, 
    sync_9router: str = None,
    serve_port: int = None,
    open_browser: bool = False
):
    t_start = time.perf_counter()
    check_url = target_url or DEFAULT_TEST_URL
    
    print(f"\n{Fore.YELLOW}{glyphs.step_harvest} [1/3] Harvesting & Deduplicating candidates from verified feeds...{Style.RESET_ALL}")
    candidates = fetch_proxies_sync(protocols=protocols, country_filter=country)
    
    if not candidates:
        print(f"{Fore.RED}{glyphs.err} Gagal mengambil kandidat proxy dari feed.{Style.RESET_ALL}")
        return []

    url_hint = f" | Target: {check_url[:35]}" if target_url else ""
    anon_hint = f" | Anon: {anonymity.upper()}" if anonymity and anonymity.lower() != 'all' else ""
    c_hint = f" | Country: {country.upper()}" if country else ""
    print(f"\n{Fore.YELLOW}{glyphs.step_check} [2/3] Dual-Phase Validation (Target Alive: {target_alive}, Timeout: {timeout}s{url_hint}{anon_hint}{c_hint})...{Style.RESET_ALL}")
    
    live_proxies = check_proxies_pool(
        candidates=candidates,
        max_check=max_check,
        target_alive=target_alive,
        timeout=timeout,
        max_workers=workers,
        country_filter=country,
        anonymity_filter=anonymity,
        test_url=check_url,
        on_live_callback=print_live_proxy,
        enable_pre_triage=True
    )

    elapsed_total = round(time.perf_counter() - t_start, 2)
    speed = round(len(candidates) / max(0.1, elapsed_total), 1)
    
    print(f"\n{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Style.BRIGHT}{glyphs.success} Validation Complete! Found {len(live_proxies)} alive proxies in {elapsed_total}s ({speed} scans/sec).{Style.RESET_ALL}")

    if not live_proxies:
        print(f"{Fore.YELLOW}{glyphs.warn} Tidak ada proxy yang lolos batas timeout {timeout}s. Coba perbesar --timeout atau perbanyak --max.{Style.RESET_ALL}")
        return []

    print(f"\n{Fore.YELLOW}{glyphs.step_export} [3/3] Exporting verified proxies to disk...{Style.RESET_ALL}")
    files = export_all_formats(live_proxies, output_dir=output_dir, sync_9router_db=sync_9router)
    
    print(f"  {Fore.GREEN}{glyphs.ok}{Style.RESET_ALL} Plain Text:  {Fore.WHITE}{files.get('all_txt')}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}{glyphs.ok}{Style.RESET_ALL} URLs Format: {Fore.WHITE}{files.get('urls_txt')}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}{glyphs.ok}{Style.RESET_ALL} Elite Only:  {Fore.WHITE}{files.get('elite_txt')}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}{glyphs.ok}{Style.RESET_ALL} Rich JSON:   {Fore.WHITE}{files.get('json')}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}{glyphs.ok}{Style.RESET_ALL} CSV Sheet:   {Fore.WHITE}{files.get('csv')}{Style.RESET_ALL}")
    
    if "9router_db" in files:
        print(f"  {Fore.GREEN}{glyphs.ok}{Style.RESET_ALL} BansosRouter DB: {Fore.WHITE}Synced to {files['9router_db']}{Style.RESET_ALL}")

    # Display Top 3 Fastest Proxies
    print(f"\n{Fore.CYAN}{glyphs.rank} TOP FASTEST ELITE NODES (FyOS Neural Latency):{Style.RESET_ALL}")
    for idx, p in enumerate(live_proxies[:3], 1):
        proto = p.get('protocol', 'http').upper()
        anon = p.get('anonymity', 'Elite')
        tcp = p.get('tcp_rtt_ms', p['latency_ms'] // 2)
        print(f"  {idx}. {Fore.GREEN}{proto}://{p['proxy']}{Style.RESET_ALL} [{anon}] Latency: {Fore.YELLOW}{p['latency_ms']}ms{Style.RESET_ALL} (TCP: {tcp}ms) - [{p['country_code']}] {p['country']}")
    print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n")

    if serve_port:
        dash_url = f"http://127.0.0.1:{serve_port}/dashboard"
        print(f"{Fore.GREEN}{Style.BRIGHT}{glyphs.net} STARTING INTELLIGENT ROTATING GATEWAY & WEB DASHBOARD...{Style.RESET_ALL}")
        print(f"  • {Fore.CYAN}{Style.BRIGHT}Interactive Web Dashboard :{Style.RESET_ALL} {Fore.YELLOW}{dash_url}{Style.RESET_ALL}")
        print(f"  • Forward Proxy Endpoint  : {Fore.CYAN}http://127.0.0.1:{serve_port}{Style.RESET_ALL}")
        print(f"  • Random Proxy REST API   : {Fore.CYAN}http://127.0.0.1:{serve_port}/api/random{Style.RESET_ALL}")
        print(f"  • All Proxies REST API    : {Fore.CYAN}http://127.0.0.1:{serve_port}/api/all{Style.RESET_ALL}")
        print(f"  • Health & Status API     : {Fore.CYAN}http://127.0.0.1:{serve_port}/api/status{Style.RESET_ALL}")
        print(f"\n{Fore.WHITE}{glyphs.clip} SNIPPET SIAP PAKAI (COPY-PASTE):{Style.RESET_ALL}")
        print(f"  • {Fore.YELLOW}Python Requests:{Style.RESET_ALL} proxies={{'http': 'http://127.0.0.1:{serve_port}', 'https': 'http://127.0.0.1:{serve_port}'}}")
        print(f"  • {Fore.YELLOW}cURL Command:{Style.RESET_ALL}    curl -x http://127.0.0.1:{serve_port} https://api.ipify.org")
        print(f"  • {Fore.YELLOW}Browser Proxy:{Style.RESET_ALL}   Set Manual Proxy Host -> 127.0.0.1 | Port -> {serve_port}")
        print(f"\n{Fore.LIGHTBLACK_EX}Created By : FyOS - ConFEx CCP | Press Ctrl+C to stop server.{Style.RESET_ALL}\n")
        
        if open_browser:
            try:
                webbrowser.open(dash_url)
            except Exception:
                pass

        start_proxy_server(live_proxies, host="127.0.0.1", port=serve_port, background=False)

    return live_proxies

def view_saved_results(output_dir: str = None):
    if not output_dir:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(base_dir, "output")
    json_file = os.path.join(output_dir, "proxies.json")
    if not os.path.exists(json_file):
        print(f"\n{Fore.YELLOW}Belum ada riwayat hasil proxy tersimpan di {output_dir}. Jalankan harvest dulu!{Style.RESET_ALL}")
        return

    import json
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if HAS_RICH and console:
        table = Table(title=f"{glyphs.vault} FyOS Saved Vault — {json_file}", border_style="cyan")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Protocol", style="cyan")
        table.add_column("Proxy Endpoint", style="bold white")
        table.add_column("Latency", justify="right")
        table.add_column("Anonymity", style="bold")
        table.add_column("Location & ISP")

        proxies = data.get("proxies", [])
        for idx, p in enumerate(proxies[:15], 1):
            lat = p.get("latency_ms", 0)
            lat_style = "green" if lat < 800 else ("yellow" if lat < 2200 else "red")
            table.add_row(
                str(idx),
                p.get("protocol", "http").upper(),
                p.get("proxy", ""),
                f"[{lat_style}]{lat}ms[/{lat_style}]",
                p.get("anonymity", "Elite"),
                f"[{p.get('country_code', '??')}] {p.get('country', '')} - {p.get('isp', '-')[:22]}"
            )
        console.print(table)
    else:
        print(f"\n{Fore.CYAN}{glyphs.vault} HASIL PROXY TERAKHIR DARI {json_file}:{Style.RESET_ALL}")
        print(f"  • Generated By       : {Fore.YELLOW}{data.get('generated_by', 'FyOS - ConFEx CCP')}{Style.RESET_ALL}")
        print(f"  • Terakhir diperbarui: {Fore.WHITE}{data.get('generated_at', '-')}{Style.RESET_ALL}")
        print(f"  • Total proxy aktif  : {Fore.GREEN}{data.get('total_alive', 0)}{Style.RESET_ALL}")
        print(f"  • Protokol           : {Fore.WHITE}{data.get('protocols', {})}{Style.RESET_ALL}\n")

        proxies = data.get("proxies", [])
        print(f"{Fore.CYAN}DAFTAR 10 PROXY TERCEPAT:{Style.RESET_ALL}")
        for idx, p in enumerate(proxies[:10], 1):
            proto = p.get('protocol', 'http').upper()
            print(f"  {idx:>2}. {Fore.GREEN}{proto:<6}{Style.RESET_ALL} {Fore.WHITE}{p['proxy']:<21}{Style.RESET_ALL} | {Fore.YELLOW}{p['latency_ms']:>4}ms{Style.RESET_ALL} | [{p['country_code']}] {p['country']} ({p.get('isp', '-')[:22]})")

def test_live_masking(port: int = 8888):
    """
    Fitur Pembuktian Langsung [T]:
    Uji apakah IP asli tertutup sempurna lewat Gateway 8888.
    """
    print(f"\n{Fore.CYAN}{glyphs.test} AUDIT IDENTITAS & STATUS ANONIMITAS (LIVE MASKING TEST)...{Style.RESET_ALL}")
    
    # 1. Direct IP
    print(f"  {Fore.LIGHTBLACK_EX}[1/2] Mendeteksi IP Asli perangkat kamu (Direct Connection)...{Style.RESET_ALL}")
    real_ip = "Unknown"
    real_isp = "Unknown"
    try:
        r = requests.get("https://ipwho.is/", timeout=5.0)
        if r.status_code == 200:
            d = r.json()
            real_ip = d.get("ip", "Unknown")
            real_isp = f"{d.get('connection', {}).get('isp', d.get('isp', '-'))} - {d.get('city', '-')}, {d.get('country', '-')}"
    except Exception:
        try:
            r = requests.get("https://api.ipify.org?format=json", timeout=4.0)
            real_ip = r.json().get("ip", "Unknown")
        except Exception:
            pass

    # 2. Connection through Gateway
    print(f"  {Fore.LIGHTBLACK_EX}[2/2] Menguji koneksi lewat FyOS Rotating Gateway (127.0.0.1:{port})...{Style.RESET_ALL}")
    proxies = {
        "http": f"http://127.0.0.1:{port}",
        "https": f"http://127.0.0.1:{port}"
    }
    gateway_ip = None
    gateway_info = None
    try:
        r = requests.get("https://ipwho.is/", proxies=proxies, timeout=8.0)
        if r.status_code == 200:
            d = r.json()
            gateway_ip = d.get("ip")
            gateway_info = f"{d.get('connection', {}).get('isp', d.get('isp', '-'))} - {d.get('city', '-')}, {d.get('country', '-')}"
    except Exception:
        try:
            r = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=6.0)
            if r.status_code == 200:
                gateway_ip = r.json().get("ip")
        except Exception:
            pass

    print(f"\n{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{Style.BRIGHT}{glyphs.shield}  HASIL AUDIT IDENTITAS & PRIVASI KONEKSI FYOS:{Style.RESET_ALL}")
    print(f"  • IP Asli Kamu     : {Fore.YELLOW}{real_ip}{Style.RESET_ALL} ({real_isp})")
    
    if gateway_ip:
        print(f"  • IP Masked Gateway: {Fore.GREEN}{Style.BRIGHT}{gateway_ip}{Style.RESET_ALL} ({gateway_info or 'Masked Proxy'})")
        if gateway_ip != real_ip:
            print(f"\n  {Fore.GREEN}{Style.BRIGHT}{glyphs.secure} STATUS: 100% AMAN & TERSAMARKAN! (ZERO LEAK){Style.RESET_ALL}")
            print(f"  {Fore.LIGHTBLACK_EX}Identitas asli kamu tertutup sempurna. Website target melihat kamu dari IP proxy.{Style.RESET_ALL}")
        else:
            print(f"\n  {Fore.RED}{glyphs.warn} STATUS: IP Gateway sama dengan IP asli. Periksa kembali konfigurasi proxy.{Style.RESET_ALL}")
    else:
        print(f"  • Gateway {port}     : {Fore.RED}Tidak aktif atau belum ada proxy hidup di pool.{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}{glyphs.tip} Tips: Jalankan salah satu Racikan [1-4] dulu untuk menyalakan Gateway {port}!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n")

def show_manual_menu():
    """Sub-menu [M] Bengkel Oprek Manual untuk power user."""
    global CURRENT_LANG
    while True:
        print_banner()
        if CURRENT_LANG == "ID":
            if glyphs.use_emoji:
                m_box = f"""{Fore.CYAN}┌────────────────────────────────────────────────────────────────────────┐
│             {Fore.WHITE}{Style.BRIGHT}🛠️  BENGKEL OPREK MANUAL (FYOS PROXY HARVESTER){Fore.CYAN}            │
│       {Fore.LIGHTBLACK_EX}"Buat yang paham jeroan teknis — tetap penting & bebas diatur!"{Fore.CYAN}  │
├────────────────────────────────────────────────────────────────────────┤
│  {Fore.GREEN}[1]{Fore.WHITE} ⚡ Quick Harvest Standar   {Fore.LIGHTBLACK_EX}Ambil 15 proxy tercepat dari semua tipe     {Fore.CYAN}│
│  {Fore.GREEN}[2]{Fore.WHITE} 🔒 Khusus SOCKS5          {Fore.LIGHTBLACK_EX}Protokol tercepat & stabil (HTTP diskip)    {Fore.CYAN}│
│  {Fore.GREEN}[3]{Fore.WHITE} 🌐 Khusus HTTP / HTTPS    {Fore.LIGHTBLACK_EX}Proxy klasik untuk web traffic biasa        {Fore.CYAN}│
│  {Fore.GREEN}[4]{Fore.WHITE} 🌍 Filter Negara Tertentu {Fore.LIGHTBLACK_EX}Bebas ketik kode ISO (ID, SG, US, JP, dll)  {Fore.CYAN}│
│  {Fore.GREEN}[5]{Fore.WHITE} 🛡️ Khusus Elite Proxies   {Fore.LIGHTBLACK_EX}High Anonymity Only — anti bocor header     {Fore.CYAN}│
│  {Fore.GREEN}[6]{Fore.WHITE} 🎯 Tembak Target URL      {Fore.LIGHTBLACK_EX}Uji tembus domain incaran (contoh: x.ai)    {Fore.CYAN}│
│  {Fore.GREEN}[7]{Fore.WHITE} 🏠 Nyalakan Gateway 8888  {Fore.LIGHTBLACK_EX}Host forward proxy & REST API lokal         {Fore.CYAN}│
│  {Fore.GREEN}[8]{Fore.WHITE} 🔌 Setor ke BansosRouter  {Fore.LIGHTBLACK_EX}Inject proxy langsung ke database SQLite    {Fore.CYAN}│
│  {Fore.RED}[0]{Fore.WHITE} 🔙 Balik ke Menu Racikan  {Fore.LIGHTBLACK_EX}Kembali ke beranda utama                    {Fore.CYAN}│
└────────────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}"""
            else:
                m_box = f"""{Fore.CYAN}┌────────────────────────────────────────────────────────────────────────┐
│             {Fore.WHITE}{Style.BRIGHT}>> BENGKEL OPREK MANUAL (FYOS PROXY HARVESTER) <<{Fore.CYAN}          │
│      {Fore.LIGHTBLACK_EX}"Buat yang paham jeroan teknis -- tetap penting dan bebas diatur!"{Fore.CYAN}│
├────────────────────────────────────────────────────────────────────────┤
│  {Fore.GREEN}[1]{Fore.CYAN} [QUICK]   {Fore.WHITE}Quick Harvest Standar  {Fore.LIGHTBLACK_EX}Ambil 15 proxy tercepat         {Fore.CYAN}│
│  {Fore.GREEN}[2]{Fore.CYAN} [SOCKS5]  {Fore.WHITE}Khusus SOCKS5          {Fore.LIGHTBLACK_EX}Protokol tercepat & stabil      {Fore.CYAN}│
│  {Fore.GREEN}[3]{Fore.CYAN} [HTTP]    {Fore.WHITE}Khusus HTTP / HTTPS    {Fore.LIGHTBLACK_EX}Proxy klasik untuk web traffic  {Fore.CYAN}│
│  {Fore.GREEN}[4]{Fore.CYAN} [COUNTRY] {Fore.WHITE}Filter Negara Tertentu {Fore.LIGHTBLACK_EX}Bebas ketik kode ISO (ID, SG...){Fore.CYAN}│
│  {Fore.GREEN}[5]{Fore.CYAN} [ELITE]   {Fore.WHITE}Khusus Elite Proxies   {Fore.LIGHTBLACK_EX}High Anonymity - anti bocor IP  {Fore.CYAN}│
│  {Fore.GREEN}[6]{Fore.CYAN} [TARGET]  {Fore.WHITE}Tembak Target URL      {Fore.LIGHTBLACK_EX}Uji tembus domain target khusus {Fore.CYAN}│
│  {Fore.GREEN}[7]{Fore.CYAN} [GATEWAY] {Fore.WHITE}Nyalakan Gateway 8888  {Fore.LIGHTBLACK_EX}Host forward proxy & REST API   {Fore.CYAN}│
│  {Fore.GREEN}[8]{Fore.CYAN} [BANSOS]  {Fore.WHITE}Setor ke BansosRouter  {Fore.LIGHTBLACK_EX}Inject proxy ke database SQLite {Fore.CYAN}│
│  {Fore.RED}[0]{Fore.CYAN} [BACK]    {Fore.WHITE}Balik ke Menu Racikan  {Fore.LIGHTBLACK_EX}Kembali ke beranda utama        {Fore.CYAN}│
└────────────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}"""
            prompt_str = f"{Fore.YELLOW}Pilih opsi Bengkel [1-8, 0=Kembali]: {Style.RESET_ALL}"
        else:
            if glyphs.use_emoji:
                m_box = f"""{Fore.CYAN}┌────────────────────────────────────────────────────────────────────────┐
│             {Fore.WHITE}{Style.BRIGHT}🛠️  MANUAL TUNING WORKSHOP (FYOS PROXY HARVESTER){Fore.CYAN}          │
│        {Fore.LIGHTBLACK_EX}"For power users who need custom protocols, filters & hooks"{Fore.CYAN} │
├────────────────────────────────────────────────────────────────────────┤
│  {Fore.GREEN}[1]{Fore.WHITE} ⚡ Standard Quick Sweep   {Fore.LIGHTBLACK_EX}Grab 15 fastest random live proxies          {Fore.CYAN}│
│  {Fore.GREEN}[2]{Fore.WHITE} 🔒 Pure SOCKS5 Only       {Fore.LIGHTBLACK_EX}Ultra-fast SOCKS5 sockets only              {Fore.CYAN}│
│  {Fore.GREEN}[3]{Fore.WHITE} 🌐 Classic HTTP / HTTPS   {Fore.LIGHTBLACK_EX}Standard HTTP browsing nodes                {Fore.CYAN}│
│  {Fore.GREEN}[4]{Fore.WHITE} 🌍 Custom Country Filter  {Fore.LIGHTBLACK_EX}Filter by country ISO code (ID, SG, US...)  {Fore.CYAN}│
│  {Fore.GREEN}[5]{Fore.WHITE} 🛡️ Elite Proxies Only     {Fore.LIGHTBLACK_EX}Strict ghost mode — zero header leaks       {Fore.CYAN}│
│  {Fore.GREEN}[6]{Fore.WHITE} 🎯 Target-Specific Snipe  {Fore.LIGHTBLACK_EX}Probe directly against custom website/API   {Fore.CYAN}│
│  {Fore.GREEN}[7]{Fore.WHITE} 🏠 Launch Local Gateway   {Fore.LIGHTBLACK_EX}Start rotating forward proxy on port 8888   {Fore.CYAN}│
│  {Fore.GREEN}[8]{Fore.WHITE} 🔌 Sync BansosRouter DB   {Fore.LIGHTBLACK_EX}Feed live proxies into SQLite database pool {Fore.CYAN}│
│  {Fore.RED}[0]{Fore.WHITE} 🔙 Back to Presets Menu   {Fore.LIGHTBLACK_EX}Return to primary launcher                  {Fore.CYAN}│
└────────────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}"""
            else:
                m_box = f"""{Fore.CYAN}┌────────────────────────────────────────────────────────────────────────┐
│             {Fore.WHITE}{Style.BRIGHT}>> MANUAL TUNING WORKSHOP (FYOS PROXY HARVESTER) <<{Fore.CYAN}        │
│        {Fore.LIGHTBLACK_EX}"For power users who need custom protocols, filters & hooks"{Fore.CYAN}    │
├────────────────────────────────────────────────────────────────────────┤
│  {Fore.GREEN}[1]{Fore.CYAN} [QUICK]   {Fore.WHITE}Standard Quick Sweep   {Fore.LIGHTBLACK_EX}Grab 15 fastest random proxies  {Fore.CYAN}│
│  {Fore.GREEN}[2]{Fore.CYAN} [SOCKS5]  {Fore.WHITE}Pure SOCKS5 Only       {Fore.LIGHTBLACK_EX}Ultra-fast SOCKS5 sockets only  {Fore.CYAN}│
│  {Fore.GREEN}[3]{Fore.CYAN} [HTTP]    {Fore.WHITE}Classic HTTP / HTTPS   {Fore.LIGHTBLACK_EX}Standard HTTP browsing nodes    {Fore.CYAN}│
│  {Fore.GREEN}[4]{Fore.CYAN} [COUNTRY] {Fore.WHITE}Custom Country Filter  {Fore.LIGHTBLACK_EX}Filter by ISO code (ID, SG, US) {Fore.CYAN}│
│  {Fore.GREEN}[5]{Fore.CYAN} [ELITE]   {Fore.WHITE}Elite Proxies Only     {Fore.LIGHTBLACK_EX}Strict ghost mode - zero leak   {Fore.CYAN}│
│  {Fore.GREEN}[6]{Fore.CYAN} [TARGET]  {Fore.WHITE}Target-Specific Snipe  {Fore.LIGHTBLACK_EX}Probe against custom target API {Fore.CYAN}│
│  {Fore.GREEN}[7]{Fore.CYAN} [GATEWAY] {Fore.WHITE}Launch Local Gateway   {Fore.LIGHTBLACK_EX}Start rotating proxy on 8888    {Fore.CYAN}│
│  {Fore.GREEN}[8]{Fore.CYAN} [BANSOS]  {Fore.WHITE}Sync BansosRouter DB   {Fore.LIGHTBLACK_EX}Feed proxies into SQLite pool   {Fore.CYAN}│
│  {Fore.RED}[0]{Fore.CYAN} [BACK]    {Fore.WHITE}Back to Presets Menu   {Fore.LIGHTBLACK_EX}Return to primary launcher      {Fore.CYAN}│
└────────────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}"""
            prompt_str = f"{Fore.YELLOW}Select workshop option [1-8, 0=Back]: {Style.RESET_ALL}"

        print(m_box)
        try:
            choice = input(prompt_str).strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice in ("0", "b", "back", "q"):
            break
        elif choice == "1":
            q_str = f"{Fore.CYAN}{'Target proxy hidup [default: 15]: ' if CURRENT_LANG == 'ID' else 'Target alive count [default: 15]: '}{Style.RESET_ALL}"
            t_input = input(q_str).strip()
            target_val = int(t_input) if t_input.isdigit() and int(t_input) > 0 else 15
            run_harvester(protocols=["http", "socks4", "socks5"], max_check=max(250, target_val * 15), target_alive=target_val, timeout=3.0)
        elif choice == "2":
            q_str = f"{Fore.CYAN}{'Target SOCKS5 hidup [default: 15]: ' if CURRENT_LANG == 'ID' else 'Target SOCKS5 count [default: 15]: '}{Style.RESET_ALL}"
            t_input = input(q_str).strip()
            target_val = int(t_input) if t_input.isdigit() and int(t_input) > 0 else 15
            run_harvester(protocols=["socks5"], max_check=max(250, target_val * 15), target_alive=target_val, timeout=3.0)
        elif choice == "3":
            q_str = f"{Fore.CYAN}{'Target HTTP hidup [default: 15]: ' if CURRENT_LANG == 'ID' else 'Target HTTP count [default: 15]: '}{Style.RESET_ALL}"
            t_input = input(q_str).strip()
            target_val = int(t_input) if t_input.isdigit() and int(t_input) > 0 else 15
            run_harvester(protocols=["http"], max_check=max(250, target_val * 15), target_alive=target_val, timeout=3.0)
        elif choice == "4":
            cc_prompt = f"{Fore.CYAN}{'Kode negara ISO 2 huruf (contoh: ID, SG, US) [default: ID]: ' if CURRENT_LANG == 'ID' else 'Enter 2-letter Country Code [default: ID]: '}{Style.RESET_ALL}"
            cc = input(cc_prompt).strip() or "ID"
            t_prompt = f"{Fore.CYAN}{'Target proxy hidup [default: 5]: ' if CURRENT_LANG == 'ID' else 'Target alive count [default: 5]: '}{Style.RESET_ALL}"
            t_input = input(t_prompt).strip()
            target_val = int(t_input) if t_input.isdigit() and int(t_input) > 0 else 5
            run_harvester(protocols=["http", "socks4", "socks5"], max_check=max(350, target_val * 35), target_alive=target_val, country=cc, timeout=3.5)
        elif choice == "5":
            q_str = f"{Fore.CYAN}{'Target Elite proxy [default: 15]: ' if CURRENT_LANG == 'ID' else 'Target Elite count [default: 15]: '}{Style.RESET_ALL}"
            t_input = input(q_str).strip()
            target_val = int(t_input) if t_input.isdigit() and int(t_input) > 0 else 15
            run_harvester(protocols=["http", "socks4", "socks5"], max_check=max(350, target_val * 20), target_alive=target_val, anonymity="elite", timeout=3.0)
        elif choice == "6":
            u_prompt = f"{Fore.CYAN}{'URL target uji [default: https://google.com]: ' if CURRENT_LANG == 'ID' else 'Target URL [default: https://google.com]: '}{Style.RESET_ALL}"
            t_url = input(u_prompt).strip() or "https://google.com"
            t_prompt = f"{Fore.CYAN}{'Target proxy lolos [default: 10]: ' if CURRENT_LANG == 'ID' else 'Target alive count [default: 10]: '}{Style.RESET_ALL}"
            t_input = input(t_prompt).strip()
            target_val = int(t_input) if t_input.isdigit() and int(t_input) > 0 else 10
            run_harvester(protocols=["http", "socks4", "socks5"], max_check=max(400, target_val * 25), target_alive=target_val, target_url=t_url, timeout=3.5)
        elif choice == "7":
            port_prompt = f"{Fore.CYAN}{'Port gateway lokal [default: 8888]: ' if CURRENT_LANG == 'ID' else 'Local gateway port [default: 8888]: '}{Style.RESET_ALL}"
            port_input = input(port_prompt).strip()
            port_val = int(port_input) if port_input.isdigit() else 8888
            t_prompt = f"{Fore.CYAN}{'Jumlah proxy hidup di pool [default: 15]: ' if CURRENT_LANG == 'ID' else 'Target alive pool size [default: 15]: '}{Style.RESET_ALL}"
            t_input = input(t_prompt).strip()
            target_val = int(t_input) if t_input.isdigit() and int(t_input) > 0 else 15
            run_harvester(protocols=["http", "socks4", "socks5"], max_check=max(300, target_val * 15), target_alive=target_val, timeout=3.0, serve_port=port_val, open_browser=True)
        elif choice == "8":
            detected_db = find_9router_db()
            hint = f" [Terdeteksi: {detected_db}]" if detected_db else ""
            custom_path = input(f"{Fore.CYAN}{'Path ke data.sqlite BansosRouter' + hint + ' [Enter untuk default]: ' if CURRENT_LANG == 'ID' else 'Enter BansosRouter data.sqlite path' + hint + ' [Enter for default]: '}{Style.RESET_ALL}").strip()
            db_target = custom_path if custom_path else detected_db
            if db_target and os.path.exists(db_target):
                run_harvester(protocols=["http", "socks4", "socks5"], max_check=250, target_alive=15, sync_9router=db_target)
            else:
                print(f"{Fore.RED}{'Database tidak ditemukan. Pastikan path benar.' if CURRENT_LANG == 'ID' else 'Database not found. Please verify path.'}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}{'Pilihan tidak valid.' if CURRENT_LANG == 'ID' else 'Invalid option.'}{Style.RESET_ALL}")

        try:
            pause_msg = "[Tekan Enter untuk kembali ke menu bengkel...]" if CURRENT_LANG == "ID" else "[Press Enter to return to workshop...]"
            input(f"\n{Fore.LIGHTBLACK_EX}{pause_msg}{Style.RESET_ALL}")
        except (KeyboardInterrupt, EOFError):
            break

def show_interactive_menu():
    global CURRENT_LANG
    while True:
        print_banner()
        if CURRENT_LANG == "ID":
            if glyphs.use_emoji:
                menu_box = f"""{Fore.CYAN}┌────────────────────────────────────────────────────────────────────────┐
│             {Fore.WHITE}{Style.BRIGHT}🌾 FYOS PROXY HARVESTER v2.5 (ENTERPRISE ARSENAL){Fore.CYAN}          │
│          {Fore.LIGHTBLACK_EX}Pilih Racikan Kebutuhanmu — Sekali Klik, Langsung Gas!{Fore.CYAN}        │
├────────────────────────────────────────────────────────────────────────┤
│  {Fore.MAGENTA}RACIKAN SPESIAL (TINGGAL PILIH & GAS):{Fore.CYAN}                                │
│  {Fore.GREEN}[1]{Fore.WHITE} 🐔 Racikan Ternak Akun    {Fore.LIGHTBLACK_EX}Khusus Grok/AI, Elite L1, Auto-BansosRouter    {Fore.CYAN}│
│  {Fore.GREEN}[2]{Fore.WHITE} 🕷️ Racikan Scraper Brutal {Fore.LIGHTBLACK_EX}Pool 30+ IP, Ganti IP Tiap Request, Anti-Block {Fore.CYAN}│
│  {Fore.GREEN}[3]{Fore.WHITE} ⚡ Racikan Turbo Surfing  {Fore.LIGHTBLACK_EX}Ping <350ms, Node SG/ID/US, Dual RTT Speed     {Fore.CYAN}│
│  {Fore.GREEN}[4]{Fore.WHITE} 🚜 Mode Daemon 24 Jam     {Fore.LIGHTBLACK_EX}Auto-Pilot looping panen tiap 15m, Port 8888   {Fore.CYAN}│
│  {Fore.GREEN}[W]{Fore.WHITE} 🏢 Webshare Hunter        {Fore.LIGHTBLACK_EX}Panen 10-30 Proxy Residensial Lolos Cloudflare  {Fore.CYAN}│
│                                                                        │
│  {Fore.MAGENTA}EKSPOR, DASHBOARD & PEMBUKTIAN LANGSUNG:{Fore.CYAN}                                 │
│  {Fore.CYAN}[D]{Fore.WHITE} 🌐 Buka Web Dashboard     {Fore.LIGHTBLACK_EX}Buka Obsidian GUI interaktif di browser (8888) {Fore.CYAN}│
│  {Fore.CYAN}[E]{Fore.WHITE} 📥 Ekspor File Mentah     {Fore.LIGHTBLACK_EX}Panen & simpan format TXT, JSON, CSV & SOCKS5  {Fore.CYAN}│
│  {Fore.CYAN}[T]{Fore.WHITE} 🧪 Uji Tembus Identitas   {Fore.LIGHTBLACK_EX}Live Proof: Cek apakah IP asli tertutup aman   {Fore.CYAN}│
│                                                                        │
│  {Fore.MAGENTA}BENGKEL OPREK & PENGATURAN:{Fore.CYAN}                                             │
│  {Fore.YELLOW}[M]{Fore.WHITE} 🛠️ Bengkel Oprek Manual   {Fore.LIGHTBLACK_EX}Atur sendiri protokol, ISO negara, & target URL {Fore.CYAN}│
│  {Fore.YELLOW}[S]{Fore.WHITE} 📂 Gudang Hasil Panen     {Fore.LIGHTBLACK_EX}Buka riwayat proxy aktif yang tersimpan di disk {Fore.CYAN}│
│  {Fore.BLUE}[L]{Fore.WHITE} 🌐 Ganti Bahasa (EN/ID)   {Fore.LIGHTBLACK_EX}Currently: Bahasa Indonesia                    {Fore.CYAN}│
│  {Fore.RED}[0]{Fore.WHITE} 💀 Cabut Dulu (Rebahan)   {Fore.LIGHTBLACK_EX}Keluar dari program & nikmati hari              {Fore.CYAN}│
├────────────────────────────────────────────────────────────────────────┤
│  {Fore.LIGHTBLACK_EX}Created By: {Fore.YELLOW}FyOS - ConFEx CCP{Fore.LIGHTBLACK_EX}   Status: {Fore.GREEN}Active & Neural Ready{Fore.CYAN}       │
└────────────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}"""
            else:
                menu_box = f"""{Fore.CYAN}┌────────────────────────────────────────────────────────────────────────┐
│             {Fore.WHITE}{Style.BRIGHT}>> FYOS PROXY HARVESTER v2.5 (ENTERPRISE ARSENAL) <<{Fore.CYAN}       │
│          {Fore.LIGHTBLACK_EX}Pilih Racikan Kebutuhanmu — Sekali Klik, Langsung Gas!{Fore.CYAN}        │
├────────────────────────────────────────────────────────────────────────┤
│  {Fore.MAGENTA}RACIKAN SPESIAL (TINGGAL PILIH & GAS):{Fore.CYAN}                                │
│  {Fore.GREEN}[1]{Fore.CYAN} [AI-BOT]   {Fore.WHITE}Racikan Ternak Akun    {Fore.LIGHTBLACK_EX}Khusus Grok/AI, Elite, Bansos   {Fore.CYAN}│
│  {Fore.GREEN}[2]{Fore.CYAN} [SCRAPER]  {Fore.WHITE}Racikan Scraper Brutal {Fore.LIGHTBLACK_EX}Pool 30+ IP, Anti-Block, Fast   {Fore.CYAN}│
│  {Fore.GREEN}[3]{Fore.CYAN} [TURBO]    {Fore.WHITE}Racikan Turbo Surfing  {Fore.LIGHTBLACK_EX}Ping <350ms, Dual RTT Latency   {Fore.CYAN}│
│  {Fore.GREEN}[4]{Fore.CYAN} [DAEMON]   {Fore.WHITE}Mode Daemon 24 Jam     {Fore.LIGHTBLACK_EX}Auto-Pilot Loop tiap 15m, 8888  {Fore.CYAN}│
│  {Fore.GREEN}[W]{Fore.CYAN} [RESIDEN]  {Fore.WHITE}Webshare Hunter        {Fore.LIGHTBLACK_EX}Panen 10-30 Residential IPs     {Fore.CYAN}│
│                                                                        │
│  {Fore.MAGENTA}EKSPOR, DASHBOARD & PEMBUKTIAN LANGSUNG:{Fore.CYAN}                                 │
│  {Fore.CYAN}[D]{Fore.CYAN} [WEB GUI]  {Fore.WHITE}Buka Web Dashboard     {Fore.LIGHTBLACK_EX}Obsidian UI interaktif di 8888  {Fore.CYAN}│
│  {Fore.CYAN}[E]{Fore.CYAN} [EXPORT]   {Fore.WHITE}Ekspor File Mentah     {Fore.LIGHTBLACK_EX}Format TXT, JSON, CSV & SOCKS5  {Fore.CYAN}│
│  {Fore.CYAN}[T]{Fore.CYAN} [AUDIT]    {Fore.WHITE}Uji Tembus Identitas   {Fore.LIGHTBLACK_EX}Live Proof: Tes IP Asli Tertutup{Fore.CYAN}│
│                                                                        │
│  {Fore.MAGENTA}BENGKEL OPREK & PENGATURAN:{Fore.CYAN}                                             │
│  {Fore.YELLOW}[M]{Fore.CYAN} [MANUAL]   {Fore.WHITE}Bengkel Oprek Manual   {Fore.LIGHTBLACK_EX}Atur protokol, ISO negara & URL {Fore.CYAN}│
│  {Fore.YELLOW}[S]{Fore.CYAN} [VAULT]    {Fore.WHITE}Gudang Hasil Panen     {Fore.LIGHTBLACK_EX}Buka riwayat proxy aktif di disk{Fore.CYAN}│
│  {Fore.BLUE}[L]{Fore.CYAN} [LANG]     {Fore.WHITE}Ganti Bahasa (EN/ID)   {Fore.LIGHTBLACK_EX}Currently: Bahasa Indonesia     {Fore.CYAN}│
│  {Fore.RED}[0]{Fore.CYAN} [EXIT]     {Fore.WHITE}Cabut Dulu (Rebahan)   {Fore.LIGHTBLACK_EX}Keluar dari program & santai    {Fore.CYAN}│
├────────────────────────────────────────────────────────────────────────┤
│  {Fore.LIGHTBLACK_EX}Created By: {Fore.YELLOW}FyOS - ConFEx CCP{Fore.LIGHTBLACK_EX}   Status: {Fore.GREEN}Active & Neural Ready{Fore.CYAN}         │
└────────────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}"""
            prompt_str = f"{Fore.YELLOW}Pilih Racikan [1-4, W, D, E, T, M, S, L, 0] (Default: 1): {Style.RESET_ALL}"
        else:
            if glyphs.use_emoji:
                menu_box = f"""{Fore.CYAN}┌────────────────────────────────────────────────────────────────────────┐
│             {Fore.WHITE}{Style.BRIGHT}🌾 FYOS PROXY HARVESTER v2.5 (ENTERPRISE ARSENAL){Fore.CYAN}          │
│             {Fore.LIGHTBLACK_EX}Pick Your Battle Setup — One Click to Dominate!{Fore.CYAN}            │
├────────────────────────────────────────────────────────────────────────┤
│  {Fore.MAGENTA}PLUG & PLAY BATTLE PRESETS:{Fore.CYAN}                                              │
│  {Fore.GREEN}[1]{Fore.WHITE} 🐔 Account Farming Mode   {Fore.LIGHTBLACK_EX}Tuned for Grok/AI bots, Elite L1, BansosRouter {Fore.CYAN}│
│  {Fore.GREEN}[2]{Fore.WHITE} 🕷️ Mass Web Scraper       {Fore.LIGHTBLACK_EX}30+ Pool, Auto-Rotate per Request, Anti-Block  {Fore.CYAN}│
│  {Fore.GREEN}[3]{Fore.WHITE} ⚡ Lightning Turbo Surf   {Fore.LIGHTBLACK_EX}Ping <350ms, SG/ID/US, Dual RTT Optimization   {Fore.CYAN}│
│  {Fore.GREEN}[4]{Fore.WHITE} 🚜 24/7 Farmer Daemon     {Fore.LIGHTBLACK_EX}Auto-Pilot loop every 15m, Port 8888 always on {Fore.CYAN}│
│  {Fore.GREEN}[W]{Fore.WHITE} 🏢 Webshare Hunter        {Fore.LIGHTBLACK_EX}Harvest 10-30 Cloudflare-Bypass Residential IPs {Fore.CYAN}│
│                                                                        │
│  {Fore.MAGENTA}EXPORTS, DASHBOARD & VERIFICATION:{Fore.CYAN}                                      │
│  {Fore.CYAN}[D]{Fore.WHITE} 🌐 Launch Web Dashboard   {Fore.LIGHTBLACK_EX}Open Obsidian Interactive Web GUI on port 8888 {Fore.CYAN}│
│  {Fore.CYAN}[E]{Fore.WHITE} 📥 Raw File Exporter      {Fore.LIGHTBLACK_EX}Export TXT, JSON, CSV & URLs for external tools {Fore.CYAN}│
│  {Fore.CYAN}[T]{Fore.WHITE} 🧪 Live Identity Test     {Fore.LIGHTBLACK_EX}Instant Proof: Verify real IP masking on 8888  {Fore.CYAN}│
│                                                                        │
│  {Fore.MAGENTA}MANUAL TUNING & SETTINGS:{Fore.CYAN}                                               │
│  {Fore.YELLOW}[M]{Fore.WHITE} 🛠️ Manual Tuning Workshop {Fore.LIGHTBLACK_EX}Custom protocols, ISO filters & target domain  {Fore.CYAN}│
│  {Fore.YELLOW}[S]{Fore.WHITE} 📂 Saved Proxy Vault      {Fore.LIGHTBLACK_EX}Inspect latest active proxies saved on disk    {Fore.CYAN}│
│  {Fore.BLUE}[L]{Fore.WHITE} 🌐 Switch Language (ID/EN){Fore.LIGHTBLACK_EX}Currently: English                             {Fore.CYAN}│
│  {Fore.RED}[0]{Fore.WHITE} 💀 Rage Quit              {Fore.LIGHTBLACK_EX}Exit program cleanly                           {Fore.CYAN}│
├────────────────────────────────────────────────────────────────────────┤
│  {Fore.LIGHTBLACK_EX}Created By: {Fore.YELLOW}FyOS - ConFEx CCP{Fore.LIGHTBLACK_EX}   Status: {Fore.GREEN}Active & Neural Ready{Fore.CYAN}       │
└────────────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}"""
            else:
                menu_box = f"""{Fore.CYAN}┌────────────────────────────────────────────────────────────────────────┐
│             {Fore.WHITE}{Style.BRIGHT}>> FYOS PROXY HARVESTER v2.5 (ENTERPRISE ARSENAL) <<{Fore.CYAN}       │
│             {Fore.LIGHTBLACK_EX}Pick Your Battle Setup — One Click to Dominate!{Fore.CYAN}            │
├────────────────────────────────────────────────────────────────────────┤
│  {Fore.MAGENTA}PLUG & PLAY BATTLE PRESETS:{Fore.CYAN}                                              │
│  {Fore.GREEN}[1]{Fore.CYAN} [AI-BOT]   {Fore.WHITE}Account Farming Mode   {Fore.LIGHTBLACK_EX}Tuned for Grok/AI, Elite, DB    {Fore.CYAN}│
│  {Fore.GREEN}[2]{Fore.CYAN} [SCRAPER]  {Fore.WHITE}Mass Web Scraper       {Fore.LIGHTBLACK_EX}30+ Pool, Auto-Rotate, Anti-Ban {Fore.CYAN}│
│  {Fore.GREEN}[3]{Fore.CYAN} [TURBO]    {Fore.WHITE}Lightning Turbo Surf   {Fore.LIGHTBLACK_EX}Ping <350ms, Dual RTT Latency   {Fore.CYAN}│
│  {Fore.GREEN}[4]{Fore.CYAN} [DAEMON]   {Fore.WHITE}24/7 Farmer Daemon     {Fore.LIGHTBLACK_EX}Auto-Pilot loop every 15m, 8888 {Fore.CYAN}│
│  {Fore.GREEN}[W]{Fore.CYAN} [RESIDEN]  {Fore.WHITE}Webshare Hunter        {Fore.LIGHTBLACK_EX}Harvest 10-30 Residential IPs   {Fore.CYAN}│
│                                                                        │
│  {Fore.MAGENTA}EXPORTS, DASHBOARD & VERIFICATION:{Fore.CYAN}                                      │
│  {Fore.CYAN}[D]{Fore.CYAN} [WEB GUI]  {Fore.WHITE}Launch Web Dashboard   {Fore.LIGHTBLACK_EX}Obsidian Web GUI on port 8888   {Fore.CYAN}│
│  {Fore.CYAN}[E]{Fore.CYAN} [EXPORT]   {Fore.WHITE}Raw File Exporter      {Fore.LIGHTBLACK_EX}Export TXT, JSON, CSV & SOCKS5  {Fore.CYAN}│
│  {Fore.CYAN}[T]{Fore.CYAN} [AUDIT]    {Fore.WHITE}Live Identity Test     {Fore.LIGHTBLACK_EX}Instant Proof: Verify IP Masking{Fore.CYAN}│
│                                                                        │
│  {Fore.MAGENTA}MANUAL TUNING & SETTINGS:{Fore.CYAN}                                               │
│  {Fore.YELLOW}[M]{Fore.CYAN} [MANUAL]   {Fore.WHITE}Manual Tuning Workshop {Fore.LIGHTBLACK_EX}Custom protocols & ISO filters  {Fore.CYAN}│
│  {Fore.YELLOW}[S]{Fore.CYAN} [VAULT]    {Fore.WHITE}Saved Proxy Vault      {Fore.LIGHTBLACK_EX}Inspect latest proxies on disk  {Fore.CYAN}│
│  {Fore.BLUE}[L]{Fore.CYAN} [LANG]     {Fore.WHITE}Switch Language (ID/EN){Fore.LIGHTBLACK_EX}Currently: English              {Fore.CYAN}│
│  {Fore.RED}[0]{Fore.CYAN} [EXIT]     {Fore.WHITE}Rage Quit              {Fore.LIGHTBLACK_EX}Exit program cleanly            {Fore.CYAN}│
├────────────────────────────────────────────────────────────────────────┤
│  {Fore.LIGHTBLACK_EX}Created By: {Fore.YELLOW}FyOS - ConFEx CCP{Fore.LIGHTBLACK_EX}   Status: {Fore.GREEN}Active & Neural Ready{Fore.CYAN}         │
└────────────────────────────────────────────────────────────────────────┘{Style.RESET_ALL}"""
            prompt_str = f"{Fore.YELLOW}Select Option [1-4, W, D, E, T, M, S, L, 0] (Default: 1): {Style.RESET_ALL}"

        print(menu_box)
        try:
            choice = input(prompt_str).strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
            break

        if choice.lower() == "l":
            CURRENT_LANG = "EN" if CURRENT_LANG == "ID" else "ID"
            new_lang_name = "Bahasa Indonesia" if CURRENT_LANG == "ID" else "English"
            print(f"\n{Fore.GREEN}{glyphs.net} Bahasa antarmuka diubah ke: {new_lang_name}{Style.RESET_ALL}")
            continue

        if choice.lower() == "m":
            show_manual_menu()
            continue

        if choice.lower() == "d":
            dash_url = "http://127.0.0.1:8888/dashboard"
            print(f"\n{Fore.CYAN}{glyphs.net} Membuka FyOS Web Dashboard di {dash_url}...{Style.RESET_ALL}")
            try:
                webbrowser.open(dash_url)
            except Exception:
                pass
            test_live_masking(port=8888)
            continue

        if choice.lower() == "t":
            test_live_masking(port=8888)
        elif choice.lower() == "e":
            q_str = f"{Fore.CYAN}{'Target jumlah proxy hidup yang mau diekspor [default: 20]: ' if CURRENT_LANG == 'ID' else 'Target alive proxies to export [default: 20]: '}{Style.RESET_ALL}"
            t_input = input(q_str).strip()
            target_val = int(t_input) if t_input.isdigit() and int(t_input) > 0 else 20
            run_harvester(protocols=["http", "socks4", "socks5"], max_check=max(250, target_val * 15), target_alive=target_val, timeout=3.0)
        elif choice == "" or choice == "1":
            print(f"\n{Fore.GREEN}{glyphs.bot} {'Menjalankan Racikan Ternak Akun (Grok, Qoder & Bot AI)...' if CURRENT_LANG == 'ID' else 'Launching Account Farming Preset (Grok, Qoder & AI)...'}{Style.RESET_ALL}")
            db_target = find_9router_db()
            if db_target:
                print(f"  {Fore.CYAN}{glyphs.ok} BansosRouter SQLite terdeteksi di: {Fore.WHITE}{db_target}{Style.RESET_ALL}")
            run_harvester(
                protocols=["http", "socks5"], 
                max_check=350, 
                target_alive=20, 
                anonymity="elite", 
                timeout=2.5, 
                serve_port=8888, 
                sync_9router=db_target,
                open_browser=True
            )
        elif choice == "2":
            print(f"\n{Fore.GREEN}{glyphs.scraper} {'Menjalankan Racikan Scraper Brutal (Shopee, Tokopedia, Web Data)...' if CURRENT_LANG == 'ID' else 'Launching Mass Web Scraper Preset...'}{Style.RESET_ALL}")
            run_harvester(
                protocols=["http", "socks4", "socks5"], 
                max_check=500, 
                target_alive=30, 
                anonymity="elite", 
                timeout=3.5, 
                serve_port=8888, 
                open_browser=True
            )
        elif choice == "3":
            print(f"\n{Fore.GREEN}{glyphs.zap} {'Menjalankan Racikan Turbo Surfing (Ping Terendah, SG/ID/US)...' if CURRENT_LANG == 'ID' else 'Launching Lightning Turbo Surfing Preset...'}{Style.RESET_ALL}")
            run_harvester(
                protocols=["http", "socks5"], 
                max_check=350, 
                target_alive=15, 
                timeout=2.0, 
                serve_port=8888, 
                open_browser=True
            )
        elif choice == "4":
            print(f"\n{Fore.MAGENTA}{glyphs.daemon} {'Mode Daemon 24 Jam Aktif: Refresh berkala setiap 15 menit. Tekan Ctrl+C untuk berhenti.' if CURRENT_LANG == 'ID' else '24/7 Farmer Daemon Active: Auto-refreshing every 15 mins. Press Ctrl+C to stop.'}{Style.RESET_ALL}")
            while True:
                try:
                    db_target = find_9router_db()
                    run_harvester(
                        protocols=["http", "socks5"], 
                        max_check=300, 
                        target_alive=20, 
                        timeout=2.5, 
                        serve_port=8888, 
                        sync_9router=db_target
                    )
                    time.sleep(15 * 60)
                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}{'Mode Daemon dihentikan.' if CURRENT_LANG == 'ID' else 'Daemon stopped.'}{Style.RESET_ALL}")
                    break
        elif choice.lower() == "w":
            from core.webshare_hunter import run_webshare_hunter
            print(f"\n{Fore.GREEN}{glyphs.resident} {'Membuka Webshare Residential Hunter...' if CURRENT_LANG == 'ID' else 'Launching Webshare Residential Hunter...'}{Style.RESET_ALL}")
            acc_prompt = f"{Fore.CYAN}{'Berapa akun Webshare yang ingin dipanen? [Default: 1]: ' if CURRENT_LANG == 'ID' else 'How many Webshare accounts to hunt? [Default: 1]: '}{Style.RESET_ALL}"
            a_input = input(acc_prompt).strip()
            total_acc = int(a_input) if a_input.isdigit() and int(a_input) > 0 else 1

            head_prompt = f"{Fore.CYAN}{'Jalankan di background tanpa jendela (Headless)? [y/N]: ' if CURRENT_LANG == 'ID' else 'Run in background (Headless)? [y/N]: '}{Style.RESET_ALL}"
            h_input = input(head_prompt).strip().lower()
            is_headless = h_input in ("y", "yes")

            db_target = find_9router_db()
            run_webshare_hunter(total=total_acc, headless=is_headless, sync_9router_db=db_target)
        elif choice.lower() in ("s", "saved"):
            view_saved_results()
        elif choice == "0" or choice.lower() == "q":
            goodbye_msg = f"{glyphs.exit_sym} Sesi selesai. Dibuat dengan presisi oleh FyOS - ConFEx CCP! 👋" if CURRENT_LANG == "ID" else f"{glyphs.exit_sym} Session closed. Crafted with precision by FyOS - ConFEx CCP! 👋"
            print(f"\n{Fore.YELLOW}{goodbye_msg}{Style.RESET_ALL}\n")
            break
        else:
            invalid_msg = "Pilihan tidak valid. Silakan pilih 1-4, W, D, E, T, M, S, L, atau 0." if CURRENT_LANG == "ID" else "Invalid option. Please choose 1-4, W, D, E, T, M, S, L, or 0."
            print(f"{Fore.RED}{invalid_msg}{Style.RESET_ALL}")

        try:
            pause_msg = "[Tekan Enter untuk kembali ke menu utama...]" if CURRENT_LANG == "ID" else "[Press Enter to return to main menu...]"
            input(f"\n{Fore.LIGHTBLACK_EX}{pause_msg}{Style.RESET_ALL}")
        except (KeyboardInterrupt, EOFError):
            break

def main():
    parser = argparse.ArgumentParser(
        description="FyOS Proxy Harvester v2.5 - High-Speed Multi-Protocol Proxy Harvester, Intelligent Rotating Gateway & Dashboard\nCreated By : FyOS - ConFEx CCP"
    )
    parser.add_argument("--protocol", "-p", choices=["all", "http", "socks4", "socks5"], default="all", help="Target proxy protocol (default: all)")
    parser.add_argument("--max", "-m", type=int, default=250, help="Maximum candidate proxies to validate (default: 250)")
    parser.add_argument("--target", "-t", type=int, default=15, help="Target number of alive proxies to collect (default: 15)")
    parser.add_argument("--timeout", type=float, default=3.0, help="Connection timeout in seconds (default: 3.0)")
    parser.add_argument("--workers", "-w", type=int, default=50, help="Concurrent testing workers (default: 50)")
    parser.add_argument("--country", "-c", type=str, default=None, help="Filter by country ISO code (e.g. US, SG, ID, DE)")
    parser.add_argument("--anonymity", choices=["all", "elite", "anonymous", "transparent"], default="all", help="Filter by anonymity level (default: all)")
    parser.add_argument("--target-url", type=str, default=None, help="Validate proxies against specific website (e.g. https://google.com)")
    parser.add_argument("--serve", nargs="?", const=8888, type=int, default=None, help="Start local rotating forward proxy, REST API & Web Dashboard on port (default: 8888)")
    parser.add_argument("--open-dashboard", action="store_true", help="Automatically launch Web Dashboard in browser upon starting server")
    parser.add_argument("--loop", "-l", type=int, default=0, help="Auto-refresh loop interval in minutes (0 = single run)")
    parser.add_argument("--output", "-o", type=str, default=None, help="Custom output directory")
    parser.add_argument("--sync-9router", type=str, default=None, help="Path to BansosRouter/9Router data.sqlite for direct database sync (or 'auto')")
    parser.add_argument("--webshare", "-W", type=int, nargs="?", const=1, default=None, help="Trigger Webshare Residential Hunter for N accounts (default: 1)")
    parser.add_argument("--headless", action="store_true", help="Run Webshare Hunter in headless mode")
    parser.add_argument("--emoji", action="store_true", default=False, help="Force enable rich emoji icons (for modern terminals)")
    parser.add_argument("--no-emoji", action="store_true", default=False, help="Force disable emojis (use 100%% CMD-safe badges)")

    if len(sys.argv) == 1:
        show_interactive_menu()
        return

    args = parser.parse_args()

    if args.emoji:
        glyphs.use_emoji = True
    elif args.no_emoji:
        glyphs.use_emoji = False

    print_banner()

    router_db = args.sync_9router
    if router_db == "auto" or router_db is None:
        router_db = find_9router_db()

    if args.webshare is not None:
        from core.webshare_hunter import run_webshare_hunter
        run_webshare_hunter(total=args.webshare, headless=args.headless, sync_9router_db=router_db, output_dir=args.output)
        return

    proto_list = [args.protocol] if args.protocol != "all" else ["http", "socks4", "socks5"]

    if args.loop > 0:
        print(f"{Fore.MAGENTA}{glyphs.loop} Auto-refresh loop active: Running every {args.loop} minutes... (Press Ctrl+C to stop){Style.RESET_ALL}")
        while True:
            try:
                run_harvester(
                    protocols=proto_list,
                    max_check=args.max,
                    target_alive=args.target,
                    timeout=args.timeout,
                    workers=args.workers,
                    country=args.country,
                    anonymity=args.anonymity,
                    target_url=args.target_url,
                    output_dir=args.output,
                    sync_9router=router_db,
                    serve_port=args.serve,
                    open_browser=args.open_dashboard
                )
                print(f"{Fore.LIGHTBLACK_EX}Sleeping for {args.loop} minutes before next sweep...{Style.RESET_ALL}")
                time.sleep(args.loop * 60)
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}{glyphs.stop} Harvester stopped by user.{Style.RESET_ALL}")
                break
    else:
        run_harvester(
            protocols=proto_list,
            max_check=args.max,
            target_alive=args.target,
            timeout=args.timeout,
            workers=args.workers,
            country=args.country,
            anonymity=args.anonymity,
            target_url=args.target_url,
            output_dir=args.output,
            sync_9router=router_db,
            serve_port=args.serve,
            open_browser=args.open_dashboard
        )

if __name__ == "__main__":
    main()
