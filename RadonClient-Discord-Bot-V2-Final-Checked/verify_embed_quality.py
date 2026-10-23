import sys
import types
import unittest
from unittest.mock import MagicMock

class DummyEmbed:
    def __init__(self, title=None, description=None, color=None):
        self.title, self.description, self.color = title, description, color
        self.fields = []
    def set_footer(self, **kwargs):
        self.footer = kwargs
    def set_thumbnail(self, **kwargs):
        self.thumbnail = kwargs
    def add_field(self, **kwargs):
        self.fields.append(types.SimpleNamespace(**kwargs))

discord = types.ModuleType("discord")
discord.Embed = DummyEmbed
sys.modules["discord"] = discord

from core.embeds import color_from_config, radon_embed, add_safe_field, embed_character_count

class EmbedQualityTests(unittest.TestCase):
    def test_valid_color(self):
        self.assertEqual(color_from_config({'branding': {'color': '#123ABC'}}), 0x123ABC)
    def test_invalid_color_fallback(self):
        self.assertEqual(color_from_config({'branding': {'color': 'invalid'}}), 0x20D5DD)
    def test_invalid_oversize_color_fallback(self):
        self.assertEqual(color_from_config({'branding': {'color': '#123456789'}}), 0x20D5DD)
    def test_embed_lengths(self):
        e = radon_embed({}, 'x'*400, 'y'*5000)
        self.assertLessEqual(len(e.title), 256)
        self.assertLessEqual(len(e.description), 4096)
    def test_aggregate_limit(self):
        e = radon_embed({}, "t"*256, "d"*4096)
        for _ in range(25):
            add_safe_field(e, "label"*60, "x"*1024)
        self.assertLessEqual(embed_character_count(e), 6000)

    def test_fields_bound(self):
        e = radon_embed({})
        for _ in range(30):
            add_safe_field(e, 'n'*300, 'v'*2000)
        self.assertGreater(len(e.fields), 0)
        self.assertLessEqual(len(e.fields), 25)
        self.assertLessEqual(embed_character_count(e), 6000)
        self.assertLessEqual(len(e.fields[0].value), 1024)

if __name__ == '__main__':
    unittest.main()
