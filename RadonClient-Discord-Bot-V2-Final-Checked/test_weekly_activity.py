import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from core.database import Database
from core.weekly_activity import week_key, is_eligible

class WeeklyTests(unittest.TestCase):
    def test_week_starts_monday(self):
        self.assertEqual(week_key(datetime(2026,10,22,tzinfo=timezone.utc)), '2026-10-19')
    def test_staff_excluded(self):
        cfg={'roles':{'owner':'1','support':['2'],'autoRole':'3'}}
        member=lambda x: SimpleNamespace(bot=False,roles=[SimpleNamespace(id=x)],guild_permissions=SimpleNamespace(administrator=False,manage_guild=False))
        self.assertFalse(is_eligible(member(1),cfg))
        self.assertFalse(is_eligible(member(2),cfg))
        self.assertTrue(is_eligible(member(3),cfg))
    def test_count_limit_report_and_invite(self):
        with tempfile.TemporaryDirectory() as d:
            db=Database(Path(d)/'test.db')
            self.assertTrue(db.record_weekly_message(1,'2026-10-19',9,100))
            self.assertFalse(db.record_weekly_message(1,'2026-10-19',9,108))
            self.assertTrue(db.record_weekly_message(1,'2026-10-19',9,116))
            self.assertEqual(db.weekly_top(1,'2026-10-19'), [('9',2)])
            db.set_weekly_report(1,'2026-10-19',12,24)
            db.set_weekly_report(1,'2026-10-19',12,25)
            self.assertEqual(db.get_weekly_report(1,'2026-10-19')[0],'24')
            self.assertTrue(db.mark_weekly_invitation(1,'2026-10-19',9,3))
            self.assertFalse(db.mark_weekly_invitation(1,'2026-10-19',9,3))
            db.clear_weekly_invitation(1,'2026-10-19',9)
            self.assertTrue(db.mark_weekly_invitation(1,'2026-10-19',9,3))

if __name__=='__main__': unittest.main()
