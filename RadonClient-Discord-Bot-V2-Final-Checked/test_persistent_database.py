import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from core.database import Database
from core.postgres_backend import HybridRow, PostgresConnection, POSTGRES_SCHEMA


class PersistentDatabaseTests(unittest.TestCase):
    def test_hybrid_row_supports_sqlite_and_mapping_access(self):
        row = HybridRow(["user_id", "count"], ("123", 5))
        self.assertEqual(row[0], "123")
        self.assertEqual(row["count"], 5)
        self.assertEqual(tuple(row), ("123", 5))

    def test_schema_has_every_required_table(self):
        for name in ("tickets", "warnings", "giveaways", "giveaway_entries", "license_sales_messages", "weekly_activity", "weekly_reports", "weekly_invites"):
            self.assertTrue(any(f"CREATE TABLE IF NOT EXISTS {name}" in s for s in POSTGRES_SCHEMA), name)

    def test_sqlite_persists_after_reopening(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"DATABASE_URL": "", "RADON_REQUIRE_PERSISTENT_DB": "0"}):
            path = Path(tmp) / "radon.db"
            db = Database(path)
            db.record_weekly_message("guild", "2026-W43", "member", 100)
            db.create_ticket(1, 2, 3, "general", "now")
            db.conn.close()
            again = Database(path)
            self.assertEqual(again.weekly_top("guild", "2026-W43"), [("member", 1)])
            self.assertIsNotNone(again.get_ticket(1))
            again.conn.close()

    def test_persistent_required_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"DATABASE_URL": "", "RADON_REQUIRE_PERSISTENT_DB": "1"}):
            with self.assertRaisesRegex(RuntimeError, "DATABASE_URL"):
                Database(Path(tmp) / "db.sqlite")

    def test_postgres_uses_correct_sql_placeholder(self):
        class FakeConn:
            def execute(self, query, args):
                self.query, self.args = query, args
                class Cursor:
                    rowcount = 1
                return Cursor()
        adapter = PostgresConnection.__new__(PostgresConnection)
        adapter._conn = FakeConn()
        adapter.execute("INSERT OR IGNORE INTO weekly_reports VALUES (?,?,?,?)", (1, 2, 3, 4))
        self.assertIn("ON CONFLICT DO NOTHING", adapter._conn.query)
        self.assertIn("%s", adapter._conn.query)
        self.assertNotIn("?", adapter._conn.query)


if __name__ == "__main__":
    unittest.main()
