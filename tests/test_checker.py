import unittest
from core.checker import classify_anonymity, is_safe_test_url, measure_tcp_handshake

class TestCheckerAlgorithms(unittest.TestCase):
    def test_safe_url_validation(self):
        self.assertTrue(is_safe_test_url("https://api.ipify.org"))
        self.assertTrue(is_safe_test_url("https://google.com"))
        # SSRF blocked endpoints
        self.assertFalse(is_safe_test_url("http://169.254.169.254/latest/meta-data/"))
        self.assertFalse(is_safe_test_url("http://metadata.google.internal/computeMetadata/v1/"))
        self.assertFalse(is_safe_test_url("ftp://example.com"))

    def test_anonymity_classification_transparent(self):
        # When host IP is in response or headers, it's Transparent
        headers = {"X-Forwarded-For": "1.2.3.4, 114.122.50.1", "Via": "1.1 proxy"}
        anon = classify_anonymity(headers, egress_ip="1.2.3.4", host_ip="114.122.50.1")
        self.assertEqual(anon, "Transparent")

        # When egress equals host IP
        anon2 = classify_anonymity({}, egress_ip="114.122.50.1", host_ip="114.122.50.1")
        self.assertEqual(anon2, "Transparent")

    def test_anonymity_classification_anonymous(self):
        # When proxy indicator headers exist, but host IP is hidden
        headers = {"Via": "1.1 squid", "X-Proxy-ID": "999"}
        anon = classify_anonymity(headers, egress_ip="1.2.3.4", host_ip="114.122.50.1")
        self.assertEqual(anon, "Anonymous")

    def test_anonymity_classification_elite(self):
        # When zero proxy indicators exist and host IP is hidden
        headers = {"Server": "cloudflare", "Content-Type": "application/json"}
        anon = classify_anonymity(headers, egress_ip="1.2.3.4", host_ip="114.122.50.1")
        self.assertEqual(anon, "Elite")

if __name__ == "__main__":
    unittest.main()
