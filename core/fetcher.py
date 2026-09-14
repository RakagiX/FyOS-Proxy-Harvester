"""
FyOS Proxy Harvester - Concurrent Multi-Feed Proxy Fetcher & Triaging Engine
Created By : FyOS - ConFEx CCP

Downloads and parses free public proxy feeds across HTTP, SOCKS4, and SOCKS5.
Supports httpx (async) with SSL verification and automated fallback to urllib.request.
Includes subnet diversity grouping and ultra-fast TCP pre-flight triaging.
"""
import os
import re
import sys
import ssl
import json
import socket
import asyncio
import urllib.request
import urllib.error
import concurrent.futures
from typing import List, Dict, Set, Optional, Tuple, Any

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

# Regex to accurately capture IPv4:Port with optional protocol prefixes
PROXY_REGEX = re.compile(
    r"(?:(?P<proto>https?|socks4|socks5)://)?"
    r"(?P<ip>(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})"
    r":(?P<port>\d{2,5})",
    re.IGNORECASE
)

def load_sources_config(config_path: Optional[str] = None) -> Dict[str, List[str]]:
    """Load sources from json configuration file."""
    if not config_path:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config", "sources.json")
        
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"http": [], "socks4": [], "socks5": []}

def _parse_proxies_from_text(content: str, protocol: str) -> List[Dict[str, Any]]:
    proxies = []
    for match in PROXY_REGEX.finditer(content):
        ip = match.group("ip")
        port = int(match.group("port"))
        if 1 <= port <= 65535:
            proxies.append({
                "ip": ip,
                "port": port,
                "proxy": f"{ip}:{port}",
                "protocol": protocol,
                "subnet": ".".join(ip.split(".")[:3]) + ".0/24"
            })
    return proxies

async def fetch_single_source_async(client: "httpx.AsyncClient", url: str, protocol: str) -> List[Dict[str, Any]]:
    """Fetch using httpx AsyncClient with secure certificate validation."""
    try:
        resp = await client.get(url, timeout=12.0)
        if resp.status_code == 200:
            return _parse_proxies_from_text(resp.text, protocol)
    except Exception:
        pass
    return []

def fetch_single_source_urllib(url: str, protocol: str) -> List[Dict[str, Any]]:
    """Fallback fetch using standard urllib with default SSL context."""
    try:
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FyOS-Harvester/2.5"}
        )
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=10.0, context=ctx) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
            return _parse_proxies_from_text(text, protocol)
    except Exception:
        pass
    return []

async def fetch_all_proxies_httpx(target_urls: List[Tuple[str, str]], verbose: bool, country_info: str) -> List[List[Dict[str, Any]]]:
    tasks = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FyOS-Proxy-Harvester/2.5"}
    # Security fix: verify=True ensures standard SSL/TLS validation against MITM tampering
    async with httpx.AsyncClient(headers=headers, verify=True, follow_redirects=True) as client:
        for url, proto in target_urls:
            tasks.append(fetch_single_source_async(client, url, proto))
        if verbose:
            print(f"[*] [FyOS Engine] Harvesting raw proxies from {len(tasks)} verified source feeds{country_info}...")
        return await asyncio.gather(*tasks)

def fetch_all_proxies_threaded(target_urls: List[Tuple[str, str]], verbose: bool, country_info: str) -> List[List[Dict[str, Any]]]:
    if verbose:
        print(f"[*] [FyOS Engine] Harvesting raw proxies from {len(target_urls)} verified source feeds{country_info} (Secure urllib)...")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        future_to_url = {executor.submit(fetch_single_source_urllib, u, p): u for u, p in target_urls}
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                results.append(future.result())
            except Exception:
                pass
    return results

def fast_tcp_ping(ip: str, port: int, timeout: float = 0.8) -> bool:
    """
    Ultra-fast non-blocking TCP SYN check to discard dead endpoints immediately.
    Saves massive worker bandwidth before HTTP/TLS negotiation.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        s.close()
        return True
    except Exception:
        try:
            s.close()
        except Exception:
            pass
        return False

def triage_candidates_fast(candidates: List[Dict[str, Any]], max_workers: int = 100, timeout: float = 0.8) -> List[Dict[str, Any]]:
    """
    Pre-flight triage stage: Runs fast TCP probe across candidates to filter out dead IPs.
    """
    survivors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_candidate = {
            executor.submit(fast_tcp_ping, c["ip"], c["port"], timeout): c
            for c in candidates
        }
        for future in concurrent.futures.as_completed(future_to_candidate):
            c = future_to_candidate[future]
            try:
                if future.result():
                    survivors.append(c)
            except Exception:
                pass
    return survivors

def fetch_proxies_sync(
    protocols: Optional[List[str]] = None, 
    country_filter: Optional[str] = None,
    config_path: Optional[str] = None,
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """
    Scrape all endpoints across requested protocols.
    Deduplicates by protocol and IP:Port, adding subnet intelligence.
    """
    sources = load_sources_config(config_path)
    if not protocols or "all" in protocols:
        target_protocols = list(sources.keys())
    else:
        target_protocols = [p.lower() for p in protocols if p.lower() in sources]

    target_urls = []
    for proto in target_protocols:
        urls = sources.get(proto, [])
        for url in urls:
            target_url = url
            if country_filter and "proxyscrape.com" in target_url and "country=all" in target_url:
                target_url = target_url.replace("country=all", f"country={country_filter.upper()}")
            target_urls.append((target_url, proto))

    c_info = f" (Country: {country_filter.upper()})" if country_filter else ""
    
    if HAS_HTTPX:
        try:
            batch_results = asyncio.run(fetch_all_proxies_httpx(target_urls, verbose, c_info))
        except Exception:
            # Fallback if asyncio loop is already running or httpx raises SSL error on specific host
            batch_results = fetch_all_proxies_threaded(target_urls, verbose, c_info)
    else:
        batch_results = fetch_all_proxies_threaded(target_urls, verbose, c_info)

    # Deduplicate with subnet indexing
    seen_proxies: Set[str] = set()
    unique_candidates: List[Dict[str, Any]] = []

    for batch in batch_results:
        for item in batch:
            key = f"{item['protocol']}://{item['proxy']}"
            if key not in seen_proxies:
                seen_proxies.add(key)
                unique_candidates.append(item)

    if verbose:
        print(f"[+] Total unique candidates harvested: {len(unique_candidates):,} proxies")
        for proto in target_protocols:
            cnt = sum(1 for p in unique_candidates if p['protocol'] == proto)
            print(f"  • {proto.upper()}: {cnt:,} candidates")

    return unique_candidates

async def fetch_all_proxies(
    protocols: Optional[List[str]] = None, 
    country_filter: Optional[str] = None,
    config_path: Optional[str] = None,
    verbose: bool = True
) -> List[Dict[str, Any]]:
    return fetch_proxies_sync(protocols=protocols, country_filter=country_filter, config_path=config_path, verbose=verbose)
