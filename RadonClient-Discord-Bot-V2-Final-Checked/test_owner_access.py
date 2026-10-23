"""Regression tests for the Discord command role gate (no live Discord API)."""
import unittest
from types import SimpleNamespace
from core.permissions import command_allowed

class TestRoleGate(unittest.TestCase):
    def setUp(self):
        self.config = {"roles": {
            "owner": "1555224034902278214",
            "coOwner": "1555224142792491128",
            "dev": "1555223821227917343",
            "support": ["1555224377652416532"]},
            "commandAccess": {}}

    def member(self, *ids):
        return SimpleNamespace(roles=[SimpleNamespace(id=int(i)) for i in ids])

    def test_owner_has_access(self):
        self.assertTrue(command_allowed(self.member(self.config["roles"]["owner"]), "announce", self.config))
        self.assertTrue(command_allowed(self.member(self.config["roles"]["owner"]), "help", self.config))

    def test_coowner_has_access(self):
        self.assertTrue(command_allowed(self.member(self.config["roles"]["coOwner"]), "giveaway", self.config))

    def test_help_access(self):
        self.assertTrue(command_allowed(self.member(), "help", self.config))

    def test_no_escalation_for_other_roles(self):
        self.assertTrue(command_allowed(self.member(self.config["roles"]["dev"]), "ban", self.config))
        self.assertFalse(command_allowed(self.member(self.config["roles"]["dev"]), "announce", self.config))
        self.assertFalse(command_allowed(self.member(), "ban", self.config))

    def test_explicit_permission(self):
        self.config["commandAccess"] = {"dev": ["ban"]}
        self.assertTrue(command_allowed(self.member(self.config["roles"]["dev"]), "ban", self.config))
        self.assertFalse(command_allowed(self.member(self.config["roles"]["dev"]), "kick", self.config))

if __name__ == "__main__":
    unittest.main()
