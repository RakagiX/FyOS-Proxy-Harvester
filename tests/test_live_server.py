import json
import unittest
import urllib.request
from core.server import start_proxy_server

class TestLiveServerAndDashboard(unittest.TestCase):
    def setUp(self):
        self.mock_proxies = [
            {
                "ip": "1.1.1.1",
                "port": 8080,
                "proxy": "1.1.1.1:8080",
                "protocol": "http",
                "latency_ms": 120,
                "anonymity": "Elite",
                "country": "United States",
                "country_code": "US",
                "isp": "Cloudflare"
            }
        ]
        self.server, self.pool = start_proxy_server(self.mock_proxies, host="127.0.0.1", port=8999, background=True)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_dashboard_endpoint(self):
        url = "http://127.0.0.1:8999/dashboard"
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            content = resp.read().decode("utf-8")
            self.assertIn("FyOS - ConFEx CCP", content)
            self.assertIn("Active Proxy Inventory", content)

    def test_api_status_endpoint(self):
        url = "http://127.0.0.1:8999/api/status"
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("creator"), "FyOS - ConFEx CCP")
            self.assertEqual(data.get("service"), "FyOS Proxy Harvester Gateway & REST API")

    def test_api_all_and_random_endpoints(self):
        url_all = "http://127.0.0.1:8999/api/all"
        with urllib.request.urlopen(url_all, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("count"), 1)

        url_random = "http://127.0.0.1:8999/api/random"
        with urllib.request.urlopen(url_random, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("status"), "success")
            self.assertEqual(data.get("proxy"), "1.1.1.1:8080")

if __name__ == "__main__":
    unittest.main()
