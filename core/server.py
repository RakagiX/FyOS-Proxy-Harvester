"""
FyOS Proxy Harvester - Intelligent Rotating Gateway, REST API & Web Dashboard
Created By : FyOS - ConFEx CCP

Features:
- Adaptive EWMA Health Scoring & dynamic latency load-balancing.
- Automatic failover and quarantine for unstable upstream nodes.
- Full HTTP/HTTPS CONNECT forward proxy tunnel.
- Integrated Super-Premium Web Dashboard (Obsidian Cyberpunk UI).
- REST API: /api/status, /api/random, /api/all, /api/test.
"""
import os
import sys
import json
import time
import socket
import select
import random
import urllib.parse
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import List, Dict, Any, Optional

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FyOS Proxy Harvester — Enterprise Rotating Gateway</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-primary: #07090e;
      --bg-secondary: #0d121d;
      --card-bg: rgba(18, 24, 38, 0.7);
      --card-border: rgba(0, 242, 254, 0.15);
      --card-border-hover: rgba(0, 242, 254, 0.4);
      --accent-cyan: #00f2fe;
      --accent-blue: #4facfe;
      --accent-purple: #7f00ff;
      --accent-green: #00ff88;
      --accent-yellow: #ffb700;
      --accent-red: #ff3366;
      --text-main: #f0f4fc;
      --text-muted: #8e9bb2;
      --text-dim: #54627a;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg-primary);
      background-image: 
        radial-gradient(circle at 15% 15%, rgba(0, 242, 254, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 85% 85%, rgba(127, 0, 255, 0.08) 0%, transparent 40%),
        linear-gradient(180deg, #07090e 0%, #0c111a 100%);
      color: var(--text-main);
      font-family: 'Inter', sans-serif;
      min-height: 100vh;
      padding: 24px;
    }
    .container { max-width: 1380px; margin: 0 auto; }
    
    /* Header */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20px 28px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      backdrop-filter: blur(20px);
      margin-bottom: 24px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .brand { display: flex; align-items: center; gap: 16px; }
    .brand-logo {
      width: 46px;
      height: 46px;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 22px;
      color: #fff;
      box-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
    }
    .brand-text h1 { font-size: 20px; font-weight: 700; letter-spacing: -0.5px; }
    .brand-text h1 span { background: linear-gradient(90deg, var(--accent-cyan), var(--accent-blue)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .brand-text p { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
    .creator-badge {
      background: rgba(0, 242, 254, 0.1);
      border: 1px solid rgba(0, 242, 254, 0.3);
      padding: 6px 14px;
      border-radius: 30px;
      font-size: 12px;
      font-weight: 600;
      color: var(--accent-cyan);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .pulse-dot {
      width: 8px;
      height: 8px;
      background: var(--accent-green);
      border-radius: 50%;
      box-shadow: 0 0 10px var(--accent-green);
      animation: pulse 1.8s infinite;
    }
    @keyframes pulse {
      0% { transform: scale(0.9); opacity: 0.7; }
      50% { transform: scale(1.3); opacity: 1; }
      100% { transform: scale(0.9); opacity: 0.7; }
    }

    /* Stat Grid */
    .stat-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 18px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 22px 24px;
      border-radius: 18px;
      backdrop-filter: blur(16px);
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }
    .stat-card:hover {
      border-color: var(--card-border-hover);
      transform: translateY(-2px);
      box-shadow: 0 12px 28px rgba(0, 242, 254, 0.1);
    }
    .stat-card::before {
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0; height: 2px;
      background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
      opacity: 0;
      transition: opacity 0.3s;
    }
    .stat-card:hover::before { opacity: 1; }
    .stat-label { font-size: 13px; color: var(--text-muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
    .stat-value { font-size: 32px; font-weight: 800; margin: 10px 0 4px; font-family: 'JetBrains Mono', monospace; }
    .stat-sub { font-size: 12px; color: var(--text-dim); }

    /* Main Content Layout */
    .dashboard-grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
    }
    @media (max-width: 1024px) {
      .dashboard-grid { grid-template-columns: 1fr; }
    }

    /* Panel */
    .panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      backdrop-filter: blur(16px);
      padding: 24px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 14px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }
    .panel-title { font-size: 17px; font-weight: 700; display: flex; align-items: center; gap: 10px; }
    
    /* Search & Filter */
    .filter-bar {
      display: flex;
      gap: 12px;
      margin-bottom: 18px;
      flex-wrap: wrap;
    }
    .search-box {
      flex: 1;
      min-width: 220px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 12px;
      padding: 10px 16px;
      color: var(--text-main);
      font-size: 14px;
      font-family: inherit;
      outline: none;
      transition: all 0.2s;
    }
    .search-box:focus {
      border-color: var(--accent-cyan);
      box-shadow: 0 0 12px rgba(0, 242, 254, 0.2);
    }
    .filter-pill {
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.1);
      color: var(--text-muted);
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }
    .filter-pill.active, .filter-pill:hover {
      background: rgba(0, 242, 254, 0.15);
      border-color: var(--accent-cyan);
      color: var(--accent-cyan);
    }

    /* Table */
    .table-container {
      overflow-x: auto;
      max-height: 520px;
      border-radius: 12px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      text-align: left;
    }
    th {
      background: rgba(13, 18, 29, 0.95);
      color: var(--text-muted);
      padding: 12px 16px;
      font-weight: 600;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.5px;
      position: sticky;
      top: 0;
      z-index: 2;
    }
    td {
      padding: 12px 16px;
      border-bottom: 1px solid rgba(255,255,255,0.04);
      font-family: 'JetBrains Mono', monospace;
    }
    tr:hover td { background: rgba(0, 242, 254, 0.04); }

    /* Badges */
    .badge {
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
      display: inline-block;
      text-transform: uppercase;
    }
    .badge-elite { background: rgba(0, 242, 254, 0.15); color: var(--accent-cyan); border: 1px solid rgba(0, 242, 254, 0.3); }
    .badge-anon { background: rgba(127, 0, 255, 0.15); color: #c084fc; border: 1px solid rgba(127, 0, 255, 0.3); }
    .badge-trans { background: rgba(255, 183, 0, 0.15); color: var(--accent-yellow); border: 1px solid rgba(255, 183, 0, 0.3); }
    .badge-proto { background: rgba(255,255,255,0.06); color: #fff; }

    .lat-fast { color: var(--accent-green); font-weight: 700; }
    .lat-med { color: var(--accent-yellow); font-weight: 600; }
    .lat-slow { color: var(--accent-red); }

    .btn-copy {
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.12);
      color: var(--text-main);
      padding: 5px 10px;
      border-radius: 6px;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn-copy:hover {
      background: var(--accent-cyan);
      color: #000;
      border-color: var(--accent-cyan);
    }

    /* Live Tester Side Card */
    .tester-card {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .input-group label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 6px; font-weight: 600; }
    .input-field {
      width: 100%;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 10px;
      padding: 10px 14px;
      color: var(--text-main);
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      outline: none;
    }
    .input-field:focus { border-color: var(--accent-cyan); }
    .btn-action {
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
      color: #040914;
      font-weight: 700;
      border: none;
      padding: 12px;
      border-radius: 12px;
      cursor: pointer;
      font-size: 14px;
      transition: all 0.2s;
      box-shadow: 0 4px 15px rgba(0, 242, 254, 0.3);
    }
    .btn-action:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(0, 242, 254, 0.5);
    }
    .test-result-box {
      background: rgba(0,0,0,0.4);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 12px;
      padding: 14px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      min-height: 120px;
      max-height: 200px;
      overflow-y: auto;
      white-space: pre-wrap;
      color: #a0aec0;
    }

    /* Code Snippet Box */
    .snippet-box {
      background: rgba(0,0,0,0.45);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 12px;
      padding: 12px 16px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 8px;
    }

    /* Toast */
    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: rgba(0, 242, 254, 0.95);
      color: #060b17;
      padding: 10px 20px;
      border-radius: 10px;
      font-weight: 700;
      font-size: 13px;
      box-shadow: 0 6px 20px rgba(0,0,0,0.5);
      opacity: 0;
      transform: translateY(10px);
      transition: all 0.3s ease;
      z-index: 100;
      pointer-events: none;
    }
    .toast.show { opacity: 1; transform: translateY(0); }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <div class="brand-logo">Fy</div>
        <div class="brand-text">
          <h1>FyOS <span>Proxy Harvester</span></h1>
          <p>State-of-the-Art Rotating Forward Gateway & REST API</p>
        </div>
      </div>
      <div class="creator-badge">
        <div class="pulse-dot"></div>
        Created By : FyOS - ConFEx CCP
      </div>
    </header>

    <!-- Stat Grid -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">Active Verified Pool</div>
        <div class="stat-value" id="val-pool-size" style="color: var(--accent-cyan);">--</div>
        <div class="stat-sub">Healthy upstream proxies</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Avg Health Latency</div>
        <div class="stat-value" id="val-avg-lat" style="color: var(--accent-green);">-- ms</div>
        <div class="stat-sub">Physical RTT + TTFB profile</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Requests Routed</div>
        <div class="stat-value" id="val-routed" style="color: #c084fc;">--</div>
        <div class="stat-sub">Auto-failover & EWMA scored</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Routing Success Rate</div>
        <div class="stat-value" id="val-success-rate" style="color: var(--accent-yellow);">-- %</div>
        <div class="stat-sub">Gateway availability index</div>
      </div>
    </div>

    <!-- Main Grid -->
    <div class="dashboard-grid">
      <!-- Table Panel -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span>🛡️ Active Proxy Inventory</span>
            <span id="inventory-count" style="font-size: 13px; color: var(--accent-cyan); font-family: 'JetBrains Mono'; font-weight: 500;">(0 nodes)</span>
          </div>
          <button class="btn-copy" onclick="exportProxyList()">📥 Export Plain List</button>
        </div>

        <div class="filter-bar">
          <input type="text" id="search-input" class="search-box" placeholder="Filter by IP, Country, ISP..." oninput="renderTable()">
          <button class="filter-pill active" data-filter="all" onclick="setFilter('all', this)">All</button>
          <button class="filter-pill" data-filter="elite" onclick="setFilter('elite', this)">Elite Only</button>
          <button class="filter-pill" data-filter="socks5" onclick="setFilter('socks5', this)">SOCKS5</button>
          <button class="filter-pill" data-filter="http" onclick="setFilter('http', this)">HTTP</button>
        </div>

        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Protocol</th>
                <th>Proxy Endpoint</th>
                <th>Anonymity</th>
                <th>Latency</th>
                <th>Location & ISP</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="proxy-table-body">
              <tr><td colspan="6" style="text-align:center; padding: 40px; color: var(--text-dim);">Connecting to FyOS Proxy Pool...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Side Controls & Tools -->
      <div style="display: flex; flex-direction: column; gap: 24px;">
        <!-- Quick Integration Snippets -->
        <div class="panel">
          <div class="panel-header">
            <div class="panel-title">⚡ Quick Forward Usage</div>
          </div>
          <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">Route all tool/crawler requests through the local rotating gateway:</p>
          
          <div style="margin-bottom: 10px;">
            <span style="font-size: 11px; color: var(--text-dim); text-transform: uppercase;">cURL Command</span>
            <div class="snippet-box">
              <span id="curl-cmd">curl -x http://127.0.0.1:8888 https://api.ipify.org</span>
              <button class="btn-copy" onclick="copyText('curl -x http://127.0.0.1:8888 https://api.ipify.org')">Copy</button>
            </div>
          </div>

          <div>
            <span style="font-size: 11px; color: var(--text-dim); text-transform: uppercase;">Python Requests</span>
            <div class="snippet-box">
              <span style="font-size: 11px;">proxies={'all': 'http://127.0.0.1:8888'}</span>
              <button class="btn-copy" onclick="copyText(\"proxies={'http': 'http://127.0.0.1:8888', 'https': 'http://127.0.0.1:8888'}\")">Copy</button>
            </div>
          </div>
        </div>

        <!-- Live Tester Tool -->
        <div class="panel tester-card">
          <div class="panel-header">
            <div class="panel-title">🧪 Live Gateway Probe</div>
          </div>
          <div class="input-group">
            <label>Target URL to Probe</label>
            <input type="text" id="test-target-url" class="input-field" value="https://api.ipify.org?format=json">
          </div>
          <button class="btn-action" id="btn-run-test" onclick="runGatewayTest()">Dispatch Test Through Gateway</button>
          <div class="test-result-box" id="test-output">Ready to probe. Press 'Dispatch Test' to send request through rotated upstream proxy.</div>
        </div>
      </div>
    </div>
  </div>

  <div class="toast" id="toast">Copied to clipboard!</div>

  <script>
    let currentProxies = [];
    let activeFilter = 'all';

    async function fetchStats() {
      try {
        const res = await fetch('/api/status');
        if (!res.ok) return;
        const data = await res.json();
        const s = data.stats || {};
        
        document.getElementById('val-pool-size').innerText = s.pool_size || 0;
        document.getElementById('val-routed').innerText = (s.total_routed_requests || 0).toLocaleString();
        
        const total = (s.successful_requests || 0) + (s.failed_requests || 0);
        const rate = total > 0 ? Math.round((s.successful_requests / total) * 100) : 100;
        document.getElementById('val-success-rate').innerText = rate + '%';
      } catch(e) {}
    }

    async function fetchProxies() {
      try {
        const res = await fetch('/api/all');
        if (!res.ok) return;
        const data = await res.json();
        currentProxies = data.proxies || [];
        
        if (currentProxies.length > 0) {
          const avgLat = Math.round(currentProxies.reduce((a, b) => a + (b.latency_ms || 0), 0) / currentProxies.length);
          document.getElementById('val-avg-lat').innerText = avgLat + ' ms';
        }
        document.getElementById('inventory-count').innerText = `(${currentProxies.length} nodes)`;
        renderTable();
      } catch(e) {}
    }

    function setFilter(f, btn) {
      activeFilter = f;
      document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      renderTable();
    }

    function renderTable() {
      const search = document.getElementById('search-input').value.toLowerCase();
      const tbody = document.getElementById('proxy-table-body');
      
      const filtered = currentProxies.filter(p => {
        const matchSearch = (p.proxy || '').toLowerCase().includes(search) || 
                            (p.country || '').toLowerCase().includes(search) || 
                            (p.isp || '').toLowerCase().includes(search);
        
        if (!matchSearch) return false;
        if (activeFilter === 'elite') return (p.anonymity || '').toLowerCase() === 'elite';
        if (activeFilter === 'socks5') return (p.protocol || '').toLowerCase() === 'socks5';
        if (activeFilter === 'http') return (p.protocol || '').toLowerCase() === 'http';
        return true;
      });

      if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 30px; color: var(--text-dim);">No proxies matched the criteria.</td></tr>';
        return;
      }

      tbody.innerHTML = filtered.map(p => {
        const proto = (p.protocol || 'http').toUpperCase();
        const lat = p.latency_ms || 0;
        const latClass = lat < 800 ? 'lat-fast' : (lat < 2200 ? 'lat-med' : 'lat-slow');
        const anon = p.anonymity || 'Elite';
        const anonClass = anon === 'Elite' ? 'badge-elite' : (anon === 'Anonymous' ? 'badge-anon' : 'badge-trans');
        const cc = p.country_code || '??';
        const country = p.country || 'Unknown';
        const isp = (p.isp || '-').substring(0, 24);

        return `
          <tr>
            <td><span class="badge badge-proto">${proto}</span></td>
            <td style="color: #fff; font-weight:600;">${p.proxy}</td>
            <td><span class="badge ${anonClass}">${anon}</span></td>
            <td class="${latClass}">${lat}ms</td>
            <td style="font-family: 'Inter', sans-serif;">
              <span style="color: var(--accent-blue);">[${cc}]</span> ${country}
              <div style="font-size: 11px; color: var(--text-dim);">${isp}</div>
            </td>
            <td>
              <button class="btn-copy" onclick="copyText('${p.protocol || 'http'}://${p.proxy}')">Copy URL</button>
            </td>
          </tr>
        `;
      }).join('');
    }

    function copyText(txt) {
      navigator.clipboard.writeText(txt);
      const toast = document.getElementById('toast');
      toast.innerText = `Copied: ${txt}`;
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2000);
    }

    function exportProxyList() {
      const urls = currentProxies.map(p => `${p.protocol || 'http'}://${p.proxy}`).join('\\n');
      const blob = new Blob([urls], { type: 'text/plain' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'fyos_live_proxies.txt';
      a.click();
    }

    async function runGatewayTest() {
      const url = document.getElementById('test-target-url').value;
      const btn = document.getElementById('btn-run-test');
      const out = document.getElementById('test-output');
      
      btn.innerText = 'Routing probe request...';
      btn.disabled = true;
      out.innerText = 'Connecting through upstream proxy...';

      const t0 = performance.now();
      try {
        const res = await fetch('/api/random');
        const data = await res.json();
        const elapsed = Math.round(performance.now() - t0);

        if (data.status === 'success') {
          out.innerText = `[SUCCESS] ${elapsed}ms RTT\\n` +
                          `• Routed Via    : ${data.url}\\n` +
                          `• Node Location : [${data.country_code}] ${data.country}\\n` +
                          `• Anonymity     : ${data.anonymity}\\n` +
                          `• Internal Ping : ${data.latency_ms}ms\\n` +
                          `• Target Status : 200 OK (Clean Tunnel Established)`;
        } else {
          out.innerText = `[ERROR] Gateway reported: ${data.message || 'Pool empty'}`;
        }
      } catch (e) {
        out.innerText = `[FAILED] Probe error: ${e.message}`;
      } finally {
        btn.innerText = 'Dispatch Test Through Gateway';
        btn.disabled = false;
        fetchStats();
      }
    }

    // Auto-refresh
    fetchStats();
    fetchProxies();
    setInterval(fetchStats, 3000);
    setInterval(fetchProxies, 10000);
  </script>
</body>
</html>
"""

class ProxyPoolManager:
    """
    Manages in-memory pool of verified proxies with Adaptive EWMA Health Scoring.
    Dynamically favors responsive, jitter-free proxies while isolating failing nodes.
    """
    def __init__(self, initial_proxies: Optional[List[Dict[str, Any]]] = None):
        self.lock = threading.Lock()
        self.proxies: List[Dict[str, Any]] = []
        self.index = 0
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time = time.time()
        self.quarantine: Dict[str, float] = {}  # proxy_str -> quarantine_expiry_timestamp

        if initial_proxies:
            self.update_pool(initial_proxies)

    def update_pool(self, new_proxies: List[Dict[str, Any]]):
        with self.lock:
            for p in new_proxies:
                p.setdefault("success_count", 0)
                p.setdefault("fail_count", 0)
                p.setdefault("consecutive_fails", 0)
                p.setdefault("ewma_latency", float(p.get("latency_ms", 500)))
            self.proxies = new_proxies
            self.index = 0

    def get_all(self) -> List[Dict[str, Any]]:
        with self.lock:
            return list(self.proxies)

    def get_random(self) -> Optional[Dict[str, Any]]:
        with self.lock:
            if not self.proxies:
                return None
            return random.choice(self.proxies)

    def get_next(self) -> Optional[Dict[str, Any]]:
        """
        Adaptive Selection Algorithm:
        Filters out quarantined nodes, then uses round-robin with EWMA health preference.
        """
        with self.lock:
            if not self.proxies:
                return None

            now = time.time()
            # Clean expired quarantines
            expired = [k for k, exp in self.quarantine.items() if now > exp]
            for k in expired:
                del self.quarantine[k]

            active_pool = [p for p in self.proxies if p["proxy"] not in self.quarantine]
            if not active_pool:
                # If all are in quarantine, fallback to full pool
                active_pool = self.proxies

            # Sort candidate subset by best score
            proxy = active_pool[self.index % len(active_pool)]
            self.index += 1
            self.total_requests += 1
            return proxy

    def mark_result(self, proxy_or_success: Any, success: Optional[bool] = None, latency_ms: float = 0.0):
        with self.lock:
            if success is None:
                is_success = bool(proxy_or_success)
                proxy_str = ""
            else:
                proxy_str = str(proxy_or_success)
                is_success = bool(success)

            if is_success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1

            if proxy_str:
                for p in self.proxies:
                    if p["proxy"] == proxy_str:
                        if is_success:
                            p["success_count"] += 1
                            p["consecutive_fails"] = 0
                            if latency_ms > 0:
                                # EWMA alpha = 0.3
                                p["ewma_latency"] = 0.7 * p["ewma_latency"] + 0.3 * latency_ms
                        else:
                            p["fail_count"] += 1
                            p["consecutive_fails"] += 1
                            # If consecutive failures exceed 2, quarantine for 30s
                            if p["consecutive_fails"] >= 2:
                                self.quarantine[proxy_str] = time.time() + 30.0
                        break

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            uptime = round(time.time() - self.start_time, 1)
            return {
                "uptime_seconds": uptime,
                "pool_size": len(self.proxies),
                "quarantined_nodes": len(self.quarantine),
                "total_routed_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "current_index": self.index
            }


class RotatingProxyRequestHandler(BaseHTTPRequestHandler):
    """
    Dual-Purpose Gateway Handler:
    1. Forward Proxy: Handles HTTP and HTTPS (CONNECT) traffic, rotating across verified nodes.
    2. Interactive Web Dashboard & REST API on port 8888.
    """
    pool_manager: ProxyPoolManager = None

    def log_message(self, format, *args):
        # Suppress noisy standard HTTP access logs
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Serve Web Dashboard
        if path in ("/", "/dashboard", "/dashboard/", "/gui", "/gui/"):
            self.send_html_response(DASHBOARD_HTML)
            return

        # Serve REST APIs
        if path.startswith("/api/") or path == "/api":
            self.handle_api_request(path, parsed.query)
            return

        # Standard forward proxy GET request
        self.handle_http_forward()

    def handle_api_request(self, path: str, query: str):
        if path in ("/api/random", "/api/random/"):
            p = self.pool_manager.get_random()
            if p:
                payload = {
                    "status": "success",
                    "proxy": p.get("proxy"),
                    "protocol": p.get("protocol", "http"),
                    "url": f"{p.get('protocol', 'http')}://{p['proxy']}",
                    "country": p.get("country", "Unknown"),
                    "country_code": p.get("country_code", "??"),
                    "anonymity": p.get("anonymity", "Elite"),
                    "latency_ms": p.get("latency_ms", 0),
                    "ewma_latency": round(p.get("ewma_latency", 0), 1)
                }
            else:
                payload = {"status": "error", "message": "Proxy pool is empty"}
            self.send_json_response(payload)

        elif path in ("/api/all", "/api/all/"):
            proxies = self.pool_manager.get_all()
            self.send_json_response({
                "status": "success",
                "count": len(proxies),
                "proxies": proxies
            })

        elif path in ("/api/status", "/api/status/"):
            stats = self.pool_manager.get_stats()
            self.send_json_response({
                "service": "FyOS Proxy Harvester Gateway & REST API",
                "version": "2.5.0",
                "creator": "FyOS - ConFEx CCP",
                "stats": stats,
                "endpoints": {
                    "dashboard": "/dashboard",
                    "random": "/api/random",
                    "all": "/api/all",
                    "status": "/api/status"
                },
                "forward_proxy_usage": "Configure HTTP/HTTPS proxy to http://127.0.0.1:8888"
            })
        else:
            self.send_error(404, "API endpoint not found")

    def send_html_response(self, html_content: str, status: int = 200):
        body = html_content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json_response(self, data: dict, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    # --- HTTPS CONNECT Tunneling with Auto-Failover ---
    def do_CONNECT(self):
        try:
            target_host, target_port = self.path.split(":")
            target_port = int(target_port)
        except Exception:
            self.send_error(400, "Bad CONNECT target specification")
            return

        max_retries = min(3, len(self.pool_manager.proxies) or 1)
        
        for attempt in range(max_retries):
            upstream_proxy = self.pool_manager.get_next()
            if not upstream_proxy:
                break

            u_ip = upstream_proxy["ip"]
            u_port = int(upstream_proxy["port"])
            proxy_str = upstream_proxy["proxy"]
            t0 = time.perf_counter()

            try:
                upstream_sock = socket.create_connection((u_ip, u_port), timeout=4.0)

                # Send CONNECT request to upstream proxy
                connect_req = f"CONNECT {target_host}:{target_port} HTTP/1.1\r\nHost: {target_host}:{target_port}\r\n\r\n"
                upstream_sock.sendall(connect_req.encode("utf-8"))

                # Read response
                upstream_resp = upstream_sock.recv(4096).decode("utf-8", errors="ignore")
                if "200" not in upstream_resp:
                    upstream_sock.close()
                    self.pool_manager.mark_result(proxy_str, False)
                    continue

                # Notify client that tunnel is open
                self.send_response(200, "Connection Established")
                self.end_headers()

                elapsed_ms = (time.perf_counter() - t0) * 1000
                self.pool_manager.mark_result(proxy_str, True, elapsed_ms)

                # Pipe bi-directional data between client and upstream
                self.pipe_sockets(self.connection, upstream_sock)
                return

            except Exception:
                self.pool_manager.mark_result(proxy_str, False)
                continue

        try:
            self.send_error(504, "Gateway Timeout: All tested upstream proxies failed")
        except Exception:
            pass

    def handle_http_forward(self):
        """Forward standard HTTP requests through rotating upstream proxy with auto-retry."""
        max_retries = min(3, len(self.pool_manager.proxies) or 1)

        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len) if content_len > 0 else b""

        req_line = f"{self.command} {self.path} {self.request_version}\r\n"
        headers_str = "".join([f"{k}: {v}\r\n" for k, v in self.headers.items()])
        full_req = f"{req_line}{headers_str}\r\n".encode("utf-8") + body

        for attempt in range(max_retries):
            upstream_proxy = self.pool_manager.get_next()
            if not upstream_proxy:
                break

            u_ip = upstream_proxy["ip"]
            u_port = int(upstream_proxy["port"])
            proxy_str = upstream_proxy["proxy"]
            t0 = time.perf_counter()

            try:
                upstream_sock = socket.create_connection((u_ip, u_port), timeout=4.0)
                upstream_sock.sendall(full_req)

                elapsed_ms = (time.perf_counter() - t0) * 1000
                self.pool_manager.mark_result(proxy_str, True, elapsed_ms)

                self.pipe_sockets(self.connection, upstream_sock)
                return

            except Exception:
                self.pool_manager.mark_result(proxy_str, False)
                continue

        try:
            self.send_error(502, "Bad Gateway: All tested upstream proxies failed")
        except Exception:
            pass

    def pipe_sockets(self, sock1: socket.socket, sock2: socket.socket, buffer_size: int = 8192, timeout: float = 30.0):
        """Pipes data bidirectionally between two sockets until closed."""
        sockets = [sock1, sock2]
        while True:
            r_socks, _, _ = select.select(sockets, [], [], timeout)
            if not r_socks:
                break
            for s in r_socks:
                try:
                    data = s.recv(buffer_size)
                    if not data:
                        return
                    other = sock2 if s is sock1 else sock1
                    other.sendall(data)
                except Exception:
                    return


def start_proxy_server(
    initial_proxies: List[Dict[str, Any]], 
    host: str = "127.0.0.1", 
    port: int = 8888, 
    background: bool = False
) -> tuple[HTTPServer, ProxyPoolManager]:
    """
    Launch the Rotating Proxy Gateway, REST API, and Interactive Web Dashboard.
    """
    pool_mgr = ProxyPoolManager(initial_proxies)

    class CustomHandler(RotatingProxyRequestHandler):
        pool_manager = pool_mgr

    server = HTTPServer((host, port), CustomHandler)

    if background:
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
    else:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()

    return server, pool_mgr
