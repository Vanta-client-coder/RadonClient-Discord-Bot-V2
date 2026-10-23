"""One-time optional SQLite -> PostgreSQL migration. Run locally, never in Render startup.

Usage: set DATABASE_URL privately, then:
    python migrate_sqlite_to_postgres.py path/to/radon.db

The target tables must be empty. The source database is never modified.
"""
import os
import sqlite3
import sys
from pathlib import Path
from core.database import Database

TABLES = (
    "warnings", "tickets", "giveaways", "giveaway_entries",
    "license_sales_messages", "weekly_activity", "weekly_reports", "weekly_invites",
)


def migrate(source_path, destination):
    source_path = Path(source_path)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    source = sqlite3.connect(f"file:{source_path.resolve()}?mode=ro", uri=True)
    try:
        source.row_factory = sqlite3.Row
        source_tables = {row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        with destination.lock, destination.conn:
            for table in TABLES:
                if destination.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]:
                    raise RuntimeError(f"Destination table {table} already has records; migration aborted without overwriting data.")
            totals = {}
            for table in TABLES:
                if table not in source_tables:
                    totals[table] = 0
                    continue
                rows = source.execute(f"SELECT * FROM {table}").fetchall()
                names = [col[1] for col in source.execute(f"PRAGMA table_info({table})").fetchall()]
                sql = f"INSERT INTO {table} ({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})"
                for row in rows:
                    destination.conn.execute(sql, tuple(row))
                totals[table] = len(rows)
        return totals
    finally:
        source.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python migrate_sqlite_to_postgres.py /path/to/radon.db")
    if not os.getenv("DATABASE_URL"):
        raise SystemExit("DATABASE_URL missing. Configure it in your terminal; never paste it into GitHub.")
    db = Database(Path("unused.db"))
    if db.backend != "postgresql":
        raise SystemExit("Refusing to migrate: PostgreSQL backend not selected.")
    try:
        print("Imported counts:", migrate(sys.argv[1], db))
    finally:
        db.conn.close()
