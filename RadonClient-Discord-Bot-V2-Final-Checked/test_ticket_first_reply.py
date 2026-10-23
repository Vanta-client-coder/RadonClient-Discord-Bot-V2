import tempfile
import unittest
from pathlib import Path
from core.database import Database
from core.ticket_auto_reply import match_ticket_issue


class FirstReplyTests(unittest.TestCase):
    def test_match_topics(self):
        for text, topic in [('My Minecraft crashes', 'Minecraft crashes on launch'), ('Fabric installation help', 'Installing Radon Client'), ('my license is broken', 'Licenses and activation'), ('auto crystal bug', 'Auto Crystal'), ('can I get a refund', 'Refund policy'), ('hi there', 'General support')]:
            self.assertEqual(match_ticket_issue(text)[0], topic)

    def test_one_reply_only_and_only_owner(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Database(Path(temp) / 'test.db')
            db.create_ticket(123, 1, 456, 'support', '2026-10-22')
            self.assertFalse(db.claim_first_ticket_auto_reply(123, 999))
            self.assertTrue(db.claim_first_ticket_auto_reply(123, 456))
            self.assertFalse(db.claim_first_ticket_auto_reply(123, 456))
            db.close_ticket(123, '2026-10-22')
            self.assertFalse(db.claim_first_ticket_auto_reply(123, 456))
            db.conn.close()


if __name__ == '__main__':
    unittest.main()
