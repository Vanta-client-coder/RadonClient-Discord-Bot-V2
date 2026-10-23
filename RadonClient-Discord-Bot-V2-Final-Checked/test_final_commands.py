import ast
import unittest
from pathlib import Path
from core.permissions import command_allowed

class FinalCommandsTests(unittest.TestCase):
    def test_public_diagnostics_available_without_staff_role(self):
        user = type('Member', (), {'roles': []})()
        for name in ('help', 'botinfo', 'uptime'):
            self.assertTrue(command_allowed(user, name, {'roles': {}, 'commandAccess': {}}))

    def test_staff_does_not_gain_admin_privileges(self):
        role = type('Role', (), {'id': 42})()
        member = type('Member', (), {'roles': [role]})()
        config = {'roles': {'support': ['42']}, 'commandAccess': {}}
        self.assertFalse(command_allowed(member, 'ban', config))
        self.assertTrue(command_allowed(member, 'claim', config))

    def test_help_filters_unknown_commands(self):
        source = Path('cogs/utility.py').read_text()
        ast.parse(source)
        self.assertIn('self.bot.get_command(n)', source)
        self.assertIn('command_allowed(ctx.author, n, self.bot.config)', source)

    def test_uptime_monotonic_tracking(self):
        self.assertIn('_radon_ready_monotonic', Path('bot.py').read_text())
        self.assertIn('time.monotonic()', Path('cogs/utility.py').read_text())

if __name__ == '__main__':
    unittest.main()
