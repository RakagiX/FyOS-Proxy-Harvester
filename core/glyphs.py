"""
FyOS Proxy Harvester v2.5 - Adaptive Glyph & Symbol System
Created By : FyOS - ConFEx CCP

Intelligently detects console capabilities to eliminate [?] or tofu boxes in Windows CMD (conhost.exe)
while providing crisp, high-tech, enterprise-grade badges.
"""
import os
import sys

def supports_emojis() -> bool:
    """
    Check if the current terminal supports full SMP color emojis cleanly.
    Windows Terminal (WT_SESSION), VSCode, or modern terminal emulators.
    Standard Windows CMD (conhost.exe) returns False to prevent [?] boxes.
    """
    env_setting = os.environ.get("FYOS_EMOJI", "").lower()
    if env_setting in ("1", "true", "yes"):
        return True
    if env_setting in ("0", "false", "no"):
        return False
    if os.name == "nt":
        # Check if inside Windows Terminal or VSCode terminal
        if "WT_SESSION" in os.environ or os.environ.get("TERM_PROGRAM") == "vscode":
            return True
        return False
    return True

class GlyphSet:
    def __init__(self, use_emoji: bool = None):
        self.use_emoji = supports_emojis() if use_emoji is None else use_emoji

    def refresh(self, use_emoji: bool = None):
        self.use_emoji = supports_emojis() if use_emoji is None else use_emoji

    @property
    def zap(self) -> str:
        return "⚡" if self.use_emoji else ">>"

    @property
    def zap_right(self) -> str:
        return "⚡" if self.use_emoji else "<<"

    @property
    def live_prefix(self) -> str:
        return "🟢 " if self.use_emoji else ""

    @property
    def step_harvest(self) -> str:
        return "⚡" if self.use_emoji else "[*]"

    @property
    def step_check(self) -> str:
        return "🔍" if self.use_emoji else "[*]"

    @property
    def step_export(self) -> str:
        return "💾" if self.use_emoji else "[*]"

    @property
    def ok(self) -> str:
        return "✓" if self.use_emoji else "[OK]"

    @property
    def success(self) -> str:
        return "🎉" if self.use_emoji else "[SUCCESS]"

    @property
    def warn(self) -> str:
        return "⚠️" if self.use_emoji else "[!]"

    @property
    def err(self) -> str:
        return "❌" if self.use_emoji else "[X]"

    @property
    def rank(self) -> str:
        return "🏆" if self.use_emoji else "[RANK]"

    @property
    def net(self) -> str:
        return "🌐" if self.use_emoji else "[NETWORK]"

    @property
    def clip(self) -> str:
        return "📋" if self.use_emoji else "[INFO]"

    @property
    def shield(self) -> str:
        return "🛡️" if self.use_emoji else "[SHIELD]"

    @property
    def secure(self) -> str:
        return "✅" if self.use_emoji else "[SECURE]"

    @property
    def tip(self) -> str:
        return "💡" if self.use_emoji else "[TIP]"

    @property
    def test(self) -> str:
        return "🧪" if self.use_emoji else "[*]"

    @property
    def stop(self) -> str:
        return "🛑" if self.use_emoji else "[STOP]"

    @property
    def loop(self) -> str:
        return "🔄" if self.use_emoji else "[LOOP]"

    @property
    def vault(self) -> str:
        return "📂" if self.use_emoji else "[VAULT]"

    @property
    def bot(self) -> str:
        return "🐔" if self.use_emoji else "[BOT]"

    @property
    def scraper(self) -> str:
        return "🕷️" if self.use_emoji else "[SCRAPER]"

    @property
    def daemon(self) -> str:
        return "🚜" if self.use_emoji else "[DAEMON]"

    @property
    def resident(self) -> str:
        return "🏢" if self.use_emoji else "[RESIDENTIAL]"

    @property
    def exit_sym(self) -> str:
        return "💀" if self.use_emoji else "[EXIT]"

glyphs = GlyphSet()
