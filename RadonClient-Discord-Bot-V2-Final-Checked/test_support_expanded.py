import tempfile
import unittest
from pathlib import Path
from core.ticket_auto_reply import match_ticket_issue, TOPICS
from core.database import Database

class ExpandedSupportTests(unittest.TestCase):
    def test_topic_count_and_replies(self):
        self.assertGreaterEqual(len(TOPICS), 20)
        for entry in TOPICS:
            self.assertGreaterEqual(len(entry.phrases), 3, entry.title)
            self.assertTrue(len(entry.advice) > 80, entry.title)
            self.assertLess(len(entry.advice), 1800, entry.title)
            self.assertIn('1.', entry.advice)

    def test_examples(self):
        samples = {
            'my fps drops and stutters': 'Performance, lag or FPS',
            'my auto anchor gets stuck': 'Auto Anchor',
            'my flight keeps rubberbanding': 'Flight or server movement',
            'the auto crystal aims at the wrong obsidian': 'Auto Crystal',
            'fast break only does animation': 'Fast Break',
            'my shield breaker stops after respawn': 'Shield Breaker and combat',
            'help my keybind resets': 'Keybinds and ClickGUI',
            'i want a refund': 'Refund policy',
            'my minecraft crashes on startup': 'Minecraft crashes on launch',
            'possible phishing scam with my account': 'Account security',
            'how to install fabric loader': 'Installing Radon Client',
            'hello!': 'General support',
        }
        for example, title in samples.items():
            with self.subTest(example=example):
                self.assertEqual(match_ticket_issue(example)[0], title)

    def test_feedback_single_use_owner_open_ticket(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / 'db.sqlite')
            db.create_ticket(22, 1, 33, 'support', '2026-10-22')
            self.assertFalse(db.set_auto_support_feedback(22, 33, 'staff'))
            self.assertTrue(db.claim_first_ticket_auto_reply(22, 33))
            self.assertFalse(db.set_auto_support_feedback(22, 77, 'staff'))
            self.assertTrue(db.set_auto_support_feedback(22, 33, 'staff'))
            self.assertFalse(db.set_auto_support_feedback(22, 33, 'staff'))
            self.assertFalse(db.set_auto_support_feedback(22, 33, 'helped'))
            db.close_ticket(22, '2026-10-22')
            self.assertFalse(db.set_auto_support_feedback(22, 33, 'helped'))
            db.conn.close()

if __name__ == '__main__':
    unittest.main()
