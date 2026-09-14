import unittest
import re
from core.glyphs import GlyphSet, supports_emojis

def strip_ansi(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

class TestAdaptiveGlyphsAndMenus(unittest.TestCase):
    def test_glyph_set_compat_mode(self):
        g = GlyphSet(use_emoji=False)
        self.assertEqual(g.zap, ">>")
        self.assertEqual(g.live_prefix, "")
        self.assertEqual(g.ok, "[OK]")
        self.assertEqual(g.warn, "[!]")
        self.assertEqual(g.err, "[X]")
        self.assertEqual(g.rank, "[RANK]")
        self.assertEqual(g.net, "[NETWORK]")
        self.assertEqual(g.shield, "[SHIELD]")
        self.assertEqual(g.secure, "[SECURE]")

        # Ensure no characters above U+FFFF exist in compat mode
        for prop in ['zap', 'live_prefix', 'step_harvest', 'step_check', 'step_export',
                     'ok', 'success', 'warn', 'err', 'rank', 'net', 'clip', 'shield',
                     'secure', 'tip', 'test', 'stop', 'loop', 'vault', 'bot', 'scraper',
                     'daemon', 'resident', 'exit_sym']:
            val = getattr(g, prop)
            for ch in val:
                self.assertLessEqual(ord(ch), 0xFFFF, f"Property {prop} contains SMP char: {ch}")

    def test_glyph_set_emoji_mode(self):
        g = GlyphSet(use_emoji=True)
        self.assertEqual(g.zap, "⚡")
        self.assertEqual(g.live_prefix, "🟢 ")
        self.assertEqual(g.ok, "✓")
        self.assertEqual(g.err, "❌")

if __name__ == '__main__':
    unittest.main()
