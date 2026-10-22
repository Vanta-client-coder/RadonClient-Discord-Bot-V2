"""Dependency-free logic regression tests with small Discord stubs."""
import asyncio
import importlib
import sys
import time
import types
import unittest
from unittest.mock import MagicMock

if 'discord' not in sys.modules:
    discord = types.ModuleType('discord')
    class HTTPException(Exception):
        status = 429
    class Forbidden(HTTPException):
        status = 403
    class NotFound(HTTPException):
        status = 404
    class TextChannel: pass
    discord.HTTPException = HTTPException
    discord.Forbidden = Forbidden
    discord.NotFound = NotFound
    discord.TextChannel = TextChannel
    discord.Embed = MagicMock
    ext = types.ModuleType('discord.ext')
    class DummyLoop:
        def __init__(self, func): self.func = func
        def change_interval(self, **kwargs): pass
        def before_loop(self, fn): return fn
        def is_running(self): return False
        def start(self): pass
    ext.tasks = types.SimpleNamespace(loop=lambda **kwargs: lambda fn: DummyLoop(fn))
    discord.ext = ext
    sys.modules['discord'] = discord
    sys.modules['discord.ext'] = ext

from status_monitor import RadonStatusMonitor, _is_limited

class HeartbeatLogicTests(unittest.TestCase):
    def bot(self, interval=600):
        bot = MagicMock()
        bot.config = {'monitor': {'heartbeatSeconds': interval}, 'channels': {'botStatus': '123'}}
        bot.is_ready.return_value = True
        return bot

    def test_interval_clamped(self):
        self.assertEqual(RadonStatusMonitor(self.bot(3)).heartbeat_seconds, 300)
        self.assertEqual(RadonStatusMonitor(self.bot(999999)).heartbeat_seconds, 3600)

    def test_pending_offline_active_and_stale(self):
        monitor = RadonStatusMonitor(self.bot())
        self.assertEqual(monitor.diagnostics()['state'], 'pending')
        monitor.last_success_ts = int(time.time())
        self.assertEqual(monitor.diagnostics()['state'], 'active')
        monitor.last_success_ts -= 2000
        self.assertEqual(monitor.diagnostics()['state'], 'stale')
        monitor.bot.is_ready.return_value = False
        self.assertEqual(monitor.diagnostics()['state'], 'offline')

    def test_forbidden_disables_monitor_without_retry(self):
        monitor = RadonStatusMonitor(self.bot())
        monitor._failure('test', sys.modules['discord'].Forbidden('denied'))
        self.assertEqual(monitor.diagnostics()['state'], 'disabled')
        self.assertEqual(monitor.disabled_reason, 'missing_discord_channel_permissions')

    def test_rate_limit_sets_extended_cooldown(self):
        monitor = RadonStatusMonitor(self.bot())
        monitor._failure('test', sys.modules['discord'].HTTPException('429'))
        self.assertGreater(monitor._pause_until - time.monotonic(), 1790)

    def test_refresh_does_not_access_discord_when_not_ready(self):
        monitor = RadonStatusMonitor(self.bot())
        monitor.bot.is_ready.return_value = False
        asyncio.run(monitor.refresh())
        monitor.bot.get_channel.assert_not_called()
        self.assertIsNone(monitor.last_attempt_ts)

if __name__ == '__main__': unittest.main()
