import os
import json
import tempfile
import unittest
from core.exporter import export_all_formats

class TestExporter(unittest.TestCase):
    def setUp(self):
        self.sample_proxies = [
            {
                "ip": "103.20.50.1",
                "port": 8080,
                "proxy": "103.20.50.1:8080",
                "protocol": "http",
                "latency_sec": 0.15,
                "latency_ms": 150,
                "tcp_rtt_ms": 50,
                "anonymity": "Elite",
                "country_code": "ID",
                "country": "Indonesia",
                "city": "Jakarta",
                "isp": "Telkom Indonesia",
                "egress_ip": "103.20.50.1"
            },
            {
                "ip": "178.62.200.15",
                "port": 1080,
                "proxy": "178.62.200.15:1080",
                "protocol": "socks5",
                "latency_sec": 0.32,
                "latency_ms": 320,
                "tcp_rtt_ms": 110,
                "anonymity": "Anonymous",
                "country_code": "NL",
                "country": "Netherlands",
                "city": "Amsterdam",
                "isp": "DigitalOcean",
                "egress_ip": "178.62.200.15"
            }
        ]

    def test_export_structure_and_branding(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = export_all_formats(self.sample_proxies, output_dir=tmpdir)
            
            self.assertIn("all_txt", files)
            self.assertIn("urls_txt", files)
            self.assertIn("elite_txt", files)
            self.assertIn("json", files)
            self.assertIn("csv", files)

            # Check JSON file content and creator branding
            with open(files["json"], "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertEqual(data["generated_by"], "FyOS - ConFEx CCP")
                self.assertEqual(data["total_alive"], 2)
                self.assertEqual(data["protocols"]["http"], 1)
                self.assertEqual(data["protocols"]["socks5"], 1)

            # Check elite txt
            with open(files["elite_txt"], "r", encoding="utf-8") as f:
                elite_content = f.read().strip()
                self.assertIn("http://103.20.50.1:8080", elite_content)
                self.assertNotIn("178.62.200.15", elite_content)

if __name__ == "__main__":
    unittest.main()
