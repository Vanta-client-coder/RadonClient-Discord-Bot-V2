"""PostgreSQL compatibility adapter for RadonClient's established database API.

Uses one connection for the single bot instance and PostgreSQL transactions.
No external network access occurs until DATABASE_URL is explicitly configured.
"""
import re


class HybridRow:
    def __init__(self, names, values):
        self._values = tuple(values)
        self._names = {name: idx for idx, name in enumerate(names)}

    def __getitem__(self, key):
        if isinstance(key, str):
            return self._values[self._names[key]]
        return self._values[key]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)


class PostgresCursor:
    def __init__(self, cursor):
        self.cursor = cursor
        self.rowcount = cursor.rowcount

    def _row(self, row):
        if row is None:
            return None
        return HybridRow([col.name for col in self.cursor.description], row)

    def fetchone(self):
        return self._row(self.cursor.fetchone())

    def fetchall(self):
        return [self._row(row) for row in self.cursor.fetchall()]


class PostgresConnection:
    """Emulates the subset of sqlite3.Connection used by Database."""

    def __init__(self, url):
        import psycopg
        self._conn = psycopg.connect(url, connect_timeout=10, autocommit=True)
        self._transaction = None

    def __enter__(self):
        self._transaction = self._conn.transaction()
        self._transaction.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        tx = self._transaction
        self._transaction = None
        return tx.__exit__(exc_type, exc, tb)

    def execute(self, sql, params=()):
        query = sql.strip()
        if re.match(r'^INSERT\s+OR\s+IGNORE\s+INTO\s+', query, re.I):
            query = re.sub(r'^INSERT\s+OR\s+IGNORE\s+INTO\s+', 'INSERT INTO ', query, count=1, flags=re.I)
            query = query.rstrip().rstrip(';') + ' ON CONFLICT DO NOTHING'
        query = query.replace('?', '%s')
        cursor = self._conn.execute(query, params)
        return PostgresCursor(cursor)

    def close(self):
        self._conn.close()


POSTGRES_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS warnings (warning_id TEXT PRIMARY KEY, guild_id TEXT NOT NULL, user_id TEXT NOT NULL, moderator_id TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS tickets (channel_id TEXT PRIMARY KEY, guild_id TEXT NOT NULL, owner_id TEXT NOT NULL, type_id TEXT NOT NULL, claimed_by TEXT, opened_at TEXT NOT NULL, closed_at TEXT, status TEXT NOT NULL DEFAULT 'open', first_auto_reply_done INTEGER NOT NULL DEFAULT 0, auto_support_feedback TEXT)""",
    """CREATE TABLE IF NOT EXISTS giveaways (message_id TEXT PRIMARY KEY, guild_id TEXT NOT NULL, channel_id TEXT NOT NULL, prize TEXT NOT NULL, winners INTEGER NOT NULL, host_id TEXT NOT NULL, ends_at BIGINT NOT NULL, status TEXT NOT NULL DEFAULT 'active', created_at BIGINT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS giveaway_entries (message_id TEXT NOT NULL, user_id TEXT NOT NULL, PRIMARY KEY(message_id, user_id))""",
    """CREATE TABLE IF NOT EXISTS license_sales_messages (license_key TEXT PRIMARY KEY, message_id TEXT NOT NULL, metadata_json TEXT NOT NULL DEFAULT '{}')""",
    """CREATE TABLE IF NOT EXISTS weekly_activity (guild_id TEXT NOT NULL, week TEXT NOT NULL, user_id TEXT NOT NULL, count INTEGER NOT NULL DEFAULT 0, last_at DOUBLE PRECISION NOT NULL DEFAULT 0, PRIMARY KEY(guild_id, week, user_id))""",
    """CREATE TABLE IF NOT EXISTS weekly_reports (guild_id TEXT NOT NULL, week TEXT NOT NULL, channel_id TEXT NOT NULL, message_id TEXT NOT NULL, PRIMARY KEY(guild_id, week))""",
    """CREATE TABLE IF NOT EXISTS weekly_invites (guild_id TEXT NOT NULL, week TEXT NOT NULL, user_id TEXT NOT NULL, inviter_id TEXT NOT NULL, PRIMARY KEY(guild_id, week, user_id))""",
    """ALTER TABLE tickets ADD COLUMN IF NOT EXISTS first_auto_reply_done INTEGER NOT NULL DEFAULT 0""",
    """ALTER TABLE tickets ADD COLUMN IF NOT EXISTS auto_support_feedback TEXT""",
    """ALTER TABLE license_sales_messages ADD COLUMN IF NOT EXISTS metadata_json TEXT NOT NULL DEFAULT '{}'""",
    """CREATE INDEX IF NOT EXISTS idx_tickets_guild_owner_status ON tickets(guild_id,owner_id,status)""",
    """CREATE INDEX IF NOT EXISTS idx_giveaways_due ON giveaways(status,ends_at)""",
    """CREATE INDEX IF NOT EXISTS idx_weekly_activity_rank ON weekly_activity(guild_id,week,count DESC)""",
)
