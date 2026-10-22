import asyncio
import time
import unittest
from unittest.mock import MagicMock
from status_monitor import RadonStatusMonitor, _extract_timestamp, _duration

class MonitorTests(unittest.TestCase):
    def test_minimum_interval(self):
        bot = MagicMock()
        bot.config = {'monitor': {'heartbeatSeconds': 60}}
        monitor = RadonStatusMonitor(bot)
        self.assertEqual(monitor.heartbeat_seconds, 300)

    def test_cooldown(self):
        bot = MagicMock()
        bot.config = {'monitor': {'heartbeatSeconds': 60}}
        monitor = RadonStatusMonitor(bot)
        monitor._failure('test', Exception('failure'))
        self.assertGreater(monitor._pause_until, time.monotonic())

    def test_helpers(self):
        self.assertEqual(_extract_timestamp('<t:12345:R>'), 12345)
        self.assertIn('m', _duration(61))

if __name__ == '__main__':
    unittest.main()
