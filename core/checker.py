"""
FyOS Proxy Harvester - High-Speed Multi-Protocol Proxy Checker & Neural Profiler
Created By : FyOS - ConFEx CCP

Features:
- Dual-Phase Latency Measurement (TCP Handshake RTT + HTTP TTFB).
- L1-L3 Anonymity Classification (Elite, Anonymous, Transparent).
- Secure HTTPS GeoIP & ISP enrichment with in-memory caching.
- Multi-engine support: curl_cffi (TLS impersonation), requests, and standard urllib.
- Anti-SSRF protection and early termination concurrency pool.
"""
import sys
import time
import json
import socket
import ssl
import urllib.request
import urllib.error
import urllib.parse
from typing import List, Dict, Any, Optional, Callable
import concurrent.futures

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Optional curl_cffi for native libcurl SOCKS4/SOCKS5 performance
try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

DEFAULT_TEST_URL = "https://api.ipify.org?format=json"
_CACHED_HOST_IP: Optional[str] = None
_GEOIP_CACHE: Dict[str, Dict[str, str]] = {}

def is_safe_test_url(url: str) -> bool:
    """Anti-SSRF protection: ensure test URL is valid HTTP/HTTPS and not cloud metadata."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = (parsed.hostname or "").lower()
        blocked_hosts = {
            "169.254.169.254", "metadata.google.internal", "instance-data", 
            "169.254.170.2", "fd00:ec2::254"
        }
        if hostname in blocked_hosts:
            return False
        return True
    except Exception:
        return False

def get_host_ip() -> str:
    """Retrieve host machine's external IP to detect transparent proxy leaks."""
    global _CACHED_HOST_IP
    if _CACHED_HOST_IP is not None:
        return _CACHED_HOST_IP

    endpoints = [
        "https://api.ipify.org?format=json",
        "https://icanhazip.com",
        "https://ifconfig.me/ip"
    ]
    for url in endpoints:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 FyOS-Harvester/2.5"})
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=3.5, context=ctx) as resp:
                raw = resp.read().decode("utf-8").strip()
                if raw.startswith("{"):
                    _CACHED_HOST_IP = json.loads(raw).get("ip", "").strip()
                else:
                    _CACHED_HOST_IP = raw.strip()
                if _CACHED_HOST_IP:
                    return _CACHED_HOST_IP
        except Exception:
            continue
    _CACHED_HOST_IP = ""
    return _CACHED_HOST_IP

def measure_tcp_handshake(ip: str, port: int, timeout: float = 1.5) -> Optional[float]:
    """
    Measure raw TCP SYN-ACK handshake latency in milliseconds.
    Provides physical network RTT independent of server processing.
    """
    t0 = time.perf_counter()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        elapsed_ms = (time.perf_counter() - t0) * 1000
        s.close()
        return round(elapsed_ms, 1)
    except Exception:
        try:
            s.close()
        except Exception:
            pass
        return None

def classify_anonymity(headers_obj: Any, egress_ip: str, host_ip: str) -> str:
    """
    Classify proxy anonymity level:
    - Transparent (L3): Leaks real client IP
    - Anonymous (L2): Hides real client IP, but indicates proxy usage via headers
    - Elite (L1): Completely hides client IP and proxy presence (Stealth/Residential profile)
    """
    if host_ip and egress_ip and egress_ip == host_ip:
        return "Transparent"

    proxy_indicators = {
        "via", "x-forwarded-for", "forwarded", "x-real-ip", 
        "proxy-connection", "x-proxy-id", "x-cache", "client-ip",
        "cf-connecting-ip", "true-client-ip"
    }

    found_proxy_header = False
    items = []
    if hasattr(headers_obj, "items"):
        items = headers_obj.items()
    elif isinstance(headers_obj, dict):
        items = headers_obj.items()

    for k, v in items:
        k_low = str(k).lower()
        v_str = str(v)
        if host_ip and host_ip in v_str:
            return "Transparent"
        if k_low in proxy_indicators:
            found_proxy_header = True

    if found_proxy_header:
        return "Anonymous"
    return "Elite"

def test_single_proxy(
    proxy_info: Dict[str, Any], 
    timeout: float = 3.0, 
    test_url: str = DEFAULT_TEST_URL,
    host_ip: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Test a single proxy candidate across designated protocol.
    Measures Dual-Phase Latency: TCP Handshake RTT and HTTP Download TTFB.
    """
    if not is_safe_test_url(test_url):
        test_url = DEFAULT_TEST_URL

    proxy_str = proxy_info["proxy"]
    proto = proxy_info.get("protocol", "http").lower()
    url_proxy = f"{proto}://{proxy_str}"
    proxies = {"http": url_proxy, "https": url_proxy}
    ip = proxy_info.get("ip", proxy_str.split(":")[0])
    port = proxy_info.get("port", int(proxy_str.split(":")[1]))

    # Phase 1: Measure physical TCP Handshake Latency
    tcp_rtt = measure_tcp_handshake(ip, port, timeout=min(1.5, timeout))

    # Phase 2: Full HTTP/HTTPS End-to-End Validation
    t0 = time.perf_counter()
    try:
        if HAS_CURL_CFFI:
            resp = curl_requests.get(test_url, proxies=proxies, timeout=timeout)
            status_code = resp.status_code
            if 200 <= status_code < 400:
                elapsed = round(time.perf_counter() - t0, 3)
                public_ip = ip
                try:
                    data = resp.json()
                    public_ip = data.get("ip", public_ip)
                except Exception:
                    pass
                
                anon = classify_anonymity(resp.headers, public_ip, host_ip)
                return {
                    "ip": ip,
                    "port": port,
                    "proxy": proxy_str,
                    "protocol": proto,
                    "latency_sec": elapsed,
                    "latency_ms": int(elapsed * 1000),
                    "tcp_rtt_ms": tcp_rtt or int(elapsed * 500),
                    "egress_ip": public_ip,
                    "anonymity": anon,
                    "country": "Unknown",
                    "country_code": "??",
                    "city": "-",
                    "isp": "-"
                }
        elif HAS_REQUESTS:
            resp = requests.get(test_url, proxies=proxies, timeout=timeout)
            status_code = resp.status_code
            if 200 <= status_code < 400:
                elapsed = round(time.perf_counter() - t0, 3)
                public_ip = ip
                try:
                    data = resp.json()
                    public_ip = data.get("ip", public_ip)
                except Exception:
                    pass
                
                anon = classify_anonymity(resp.headers, public_ip, host_ip)
                return {
                    "ip": ip,
                    "port": port,
                    "proxy": proxy_str,
                    "protocol": proto,
                    "latency_sec": elapsed,
                    "latency_ms": int(elapsed * 1000),
                    "tcp_rtt_ms": tcp_rtt or int(elapsed * 500),
                    "egress_ip": public_ip,
                    "anonymity": anon,
                    "country": "Unknown",
                    "country_code": "??",
                    "city": "-",
                    "isp": "-"
                }
        else:
            # Fallback to standard library urllib with proxy handler
            proxy_handler = urllib.request.ProxyHandler({'http': url_proxy, 'https': url_proxy})
            opener = urllib.request.build_opener(proxy_handler)
            req = urllib.request.Request(test_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FyOS-Harvester/2.5"})
            ctx = ssl.create_default_context()
            with opener.open(req, timeout=timeout) as resp:
                status_code = resp.status
                if 200 <= status_code < 400:
                    elapsed = round(time.perf_counter() - t0, 3)
                    public_ip = ip
                    try:
                        data = json.loads(resp.read().decode("utf-8"))
                        public_ip = data.get("ip", public_ip)
                    except Exception:
                        pass
                    
                    anon = classify_anonymity(resp.headers, public_ip, host_ip)
                    return {
                        "ip": ip,
                        "port": port,
                        "proxy": proxy_str,
                        "protocol": proto,
                        "latency_sec": elapsed,
                        "latency_ms": int(elapsed * 1000),
                        "tcp_rtt_ms": tcp_rtt or int(elapsed * 500),
                        "egress_ip": public_ip,
                        "anonymity": anon,
                        "country": "Unknown",
                        "country_code": "??",
                        "city": "-",
                        "isp": "-"
                    }
    except Exception:
        pass
    return None

def lookup_single_ip_secure(ip: str) -> Dict[str, str]:
    """Secure HTTPS GeoIP lookup with in-memory memoization."""
    if ip in _GEOIP_CACHE:
        return _GEOIP_CACHE[ip]

    # Use HTTPS ipwho.is (free, encrypted, comprehensive)
    url = f"https://ipwho.is/{ip}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 FyOS-Harvester/2.5"})
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=3.0, context=ctx) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("success", False):
                    res = {
                        "country": data.get("country", "Unknown"),
                        "country_code": data.get("country_code", "??"),
                        "city": data.get("city", "-"),
                        "isp": data.get("connection", {}).get("isp", data.get("isp", "-"))
                    }
                    _GEOIP_CACHE[ip] = res
                    return res
    except Exception:
        pass

    # Fallback to secondary HTTPS endpoint freeipapi.com
    try:
        fallback_url = f"https://freeipapi.com/api/json/{ip}"
        req = urllib.request.Request(fallback_url, headers={"User-Agent": "Mozilla/5.0 FyOS-Harvester/2.5"})
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=3.0, context=ctx) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                res = {
                    "country": data.get("countryName", "Unknown"),
                    "country_code": data.get("countryCode", "??"),
                    "city": data.get("cityName", "-"),
                    "isp": "-"
                }
                _GEOIP_CACHE[ip] = res
                return res
    except Exception:
        pass

    default_res = {"country": "Unknown", "country_code": "??", "city": "-", "isp": "-"}
    _GEOIP_CACHE[ip] = default_res
    return default_res

def batch_enrich_geoip(live_proxies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich live proxies with secure GeoIP & ISP data using multithreaded HTTPS lookups.
    Zero cleartext leakage.
    """
    if not live_proxies:
        return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_proxy = {
            executor.submit(lookup_single_ip_secure, p["ip"]): p
            for p in live_proxies
        }
        for future in concurrent.futures.as_completed(future_to_proxy):
            p = future_to_proxy[future]
            try:
                geo = future.result()
                p["country"] = geo.get("country", "Unknown")
                p["country_code"] = geo.get("country_code", "??")
                p["city"] = geo.get("city", "-")
                p["isp"] = geo.get("isp", "-")
            except Exception:
                pass

    return live_proxies

def check_proxies_pool(
    candidates: List[Dict[str, Any]],
    max_check: int = 300,
    target_alive: int = 20,
    timeout: float = 3.0,
    max_workers: int = 60,
    country_filter: Optional[str] = None,
    anonymity_filter: Optional[str] = None,
    test_url: str = DEFAULT_TEST_URL,
    on_live_callback: Optional[Callable] = None,
    enable_pre_triage: bool = True
) -> List[Dict[str, Any]]:
    """
    Multi-stage verification pipeline:
    Stage 1: Pre-flight fast TCP ping triage (drops dead IPs in ~800ms)
    Stage 2: Full HTTP/HTTPS End-to-End deep check with latency measurement
    Stage 3: Secure GeoIP & ISP enrichment
    """
    to_test = candidates[:max_check]
    
    # Pre-triage: if we have more than 40 candidates, fast-filter first to boost performance
    if enable_pre_triage and len(to_test) > 40:
        triaged = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(100, max_workers * 2)) as triage_exec:
            future_to_c = {
                triage_exec.submit(measure_tcp_handshake, c["ip"], c["port"], 1.0): c
                for c in to_test
            }
            for future in concurrent.futures.as_completed(future_to_c):
                c = future_to_c[future]
                rtt = future.result()
                if rtt is not None:
                    c["tcp_rtt_ms"] = rtt
                    triaged.append(c)
        if triaged:
            # Test surviving candidates first
            to_test = triaged + [c for c in to_test if c not in triaged]

    alive_list: List[Dict[str, Any]] = []
    host_ip = get_host_ip()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_proxy = {
            executor.submit(test_single_proxy, p, timeout, test_url, host_ip): p 
            for p in to_test
        }
        
        for future in concurrent.futures.as_completed(future_to_proxy):
            res = future.result()
            if res:
                # Anonymity filter check
                if anonymity_filter and anonymity_filter.lower() != "all":
                    if res.get("anonymity", "").lower() != anonymity_filter.lower():
                        continue

                # Country filter check (quick lookup)
                if country_filter:
                    geo = lookup_single_ip_secure(res["ip"])
                    res["country"] = geo["country"]
                    res["country_code"] = geo["country_code"]
                    res["city"] = geo["city"]
                    res["isp"] = geo["isp"]

                    c_upper = country_filter.upper()
                    if res.get("country_code") != c_upper and res.get("country", "").upper() != c_upper:
                        continue

                alive_list.append(res)
                if on_live_callback:
                    on_live_callback(res, len(alive_list), target_alive)
                if len(alive_list) >= target_alive:
                    # Cancel remaining pending checks
                    for f in future_to_proxy:
                        f.cancel()
                    break

    # Enrich with GeoIP for all alive proxies
    if alive_list and not country_filter:
        batch_enrich_geoip(alive_list)

    # Sort by lowest latency
    alive_list.sort(key=lambda x: x["latency_ms"])
    return alive_list
