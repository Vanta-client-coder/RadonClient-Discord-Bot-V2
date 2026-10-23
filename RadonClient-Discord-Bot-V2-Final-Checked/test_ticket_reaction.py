"""Regression checks for ticket reaction wiring; Discord API requires live test."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class TicketReactionTests(unittest.TestCase):
    def test_reaction_gateway_intent(self):
        self.assertIn('intents.reactions = True', (ROOT/'bot.py').read_text())
    def test_panel_is_owner_only(self):
        s=(ROOT/'cogs/tickets.py').read_text()
        self.assertIn('if not ctx.guild or not is_owner_or_coowner(ctx.author, self.bot.config):',s)
    def test_panel_author_and_marker_validation(self):
        s=(ROOT/'cogs/tickets.py').read_text()
        self.assertIn('message.author.id != self.bot.user.id',s)
        self.assertIn('REACTION_PANEL_MARKER',s)
    def test_existing_limits_and_category_reused(self):
        s=(ROOT/'cogs/tickets.py').read_text()
        self.assertIn('await create_ticket(self.bot, ReactionTicketContext(guild, member), default_type)',s)
        self.assertIn('get_open_tickets_for_user',s)
        self.assertIn('resolve_ticket_category',s)
    def test_first_configured_type_or_support_default(self):
        s=(ROOT/'cogs/tickets.py').read_text()
        self.assertIn('"support" and not bot.config.get("tickets", {}).get("types")',s)
        self.assertIn('if self.bot.config.get("tickets", {}).get("types") else "support"',s)
if __name__=='__main__': unittest.main()
