"""Regression guards: an empty Render tickets.types now uses safe built-in categories."""
import unittest
from pathlib import Path
from core.ticket_categories import effective_ticket_types
ROOT = Path(__file__).resolve().parent
class EmptyTicketConfigTests(unittest.TestCase):
    def test_persistent_dropdown_uses_fallback(self):
        bot = (ROOT / "bot.py").read_text(encoding="utf-8")
        self.assertIn("if effective_ticket_types(self.config):", bot)
        self.assertIn("self.add_view(TicketPanelView(self))", bot)
        self.assertEqual(len(effective_ticket_types({"tickets":{"types":[]}})), 11)
    def test_panel_uses_builtins_when_missing(self):
        tickets = (ROOT / "cogs/tickets.py").read_text(encoding="utf-8")
        self.assertIn("for item in effective_ticket_types(self.bot.config):", tickets)
        self.assertNotIn("Ticket categories have not been configured yet", tickets)
if __name__ == "__main__": unittest.main()
