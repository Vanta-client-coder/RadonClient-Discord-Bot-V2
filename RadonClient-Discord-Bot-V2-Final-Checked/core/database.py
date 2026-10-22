import sqlite3
from pathlib import Path
from threading import Lock


class Database:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = Lock()
        self._setup()

    def _setup(self):
        with self.lock, self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    warning_id TEXT PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    moderator_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    channel_id TEXT PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    type_id TEXT NOT NULL,
                    claimed_by TEXT,
                    opened_at TEXT NOT NULL,
                    closed_at TEXT,
                    status TEXT NOT NULL DEFAULT 'open'
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS giveaways (
                    message_id TEXT PRIMARY KEY,
                    guild_id TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    prize TEXT NOT NULL,
                    winners INTEGER NOT NULL,
                    host_id TEXT NOT NULL,
                    ends_at INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at INTEGER NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS giveaway_entries (
                    message_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    PRIMARY KEY(message_id, user_id)
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS license_sales_messages (
                    license_key TEXT PRIMARY KEY,
                    message_id TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
            """)
            columns = {row[1] for row in self.conn.execute("PRAGMA table_info(license_sales_messages)").fetchall()}
            if "metadata_json" not in columns:
                self.conn.execute("ALTER TABLE license_sales_messages ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}' ")

    def add_warning(self, warning_id, guild_id, user_id, moderator_id, reason, created_at):
        with self.lock, self.conn:
            self.conn.execute(
                "INSERT INTO warnings VALUES (?, ?, ?, ?, ?, ?)",
                (warning_id, str(guild_id), str(user_id), str(moderator_id), reason, created_at),
            )

    def get_warnings(self, guild_id, user_id):
        with self.lock:
            return self.conn.execute(
                "SELECT * FROM warnings WHERE guild_id=? AND user_id=? ORDER BY created_at DESC",
                (str(guild_id), str(user_id)),
            ).fetchall()

    def delete_warning(self, guild_id, user_id, warning_id):
        with self.lock, self.conn:
            cur = self.conn.execute(
                "DELETE FROM warnings WHERE guild_id=? AND user_id=? AND warning_id=?",
                (str(guild_id), str(user_id), warning_id),
            )
            return cur.rowcount > 0

    def create_ticket(self, channel_id, guild_id, owner_id, type_id, opened_at):
        with self.lock, self.conn:
            self.conn.execute(
                "INSERT INTO tickets(channel_id,guild_id,owner_id,type_id,opened_at,status) VALUES(?,?,?,?,?,'open')",
                (str(channel_id), str(guild_id), str(owner_id), type_id, opened_at),
            )

    def get_ticket(self, channel_id):
        with self.lock:
            return self.conn.execute(
                "SELECT * FROM tickets WHERE channel_id=? AND status='open'", (str(channel_id),)
            ).fetchone()

    def get_open_tickets_for_user(self, guild_id, owner_id):
        with self.lock:
            return self.conn.execute(
                "SELECT * FROM tickets WHERE guild_id=? AND owner_id=? AND status='open'",
                (str(guild_id), str(owner_id)),
            ).fetchall()

    def claim_ticket(self, channel_id, user_id):
        with self.lock, self.conn:
            self.conn.execute(
                "UPDATE tickets SET claimed_by=? WHERE channel_id=? AND status='open'",
                (str(user_id), str(channel_id)),
            )

    def close_ticket(self, channel_id, closed_at):
        with self.lock, self.conn:
            self.conn.execute(
                "UPDATE tickets SET status='closed', closed_at=? WHERE channel_id=?",
                (closed_at, str(channel_id)),
            )
    def create_giveaway(self, message_id, guild_id, channel_id, prize, winners, host_id, ends_at, created_at):
        with self.lock, self.conn:
            self.conn.execute(
                """INSERT INTO giveaways(message_id,guild_id,channel_id,prize,winners,host_id,ends_at,status,created_at)
                   VALUES(?,?,?,?,?,?,?,'active',?)""",
                (str(message_id), str(guild_id), str(channel_id), prize, int(winners), str(host_id), int(ends_at), int(created_at)),
            )

    def get_giveaway(self, message_id):
        with self.lock:
            return self.conn.execute(
                "SELECT * FROM giveaways WHERE message_id=?",
                (str(message_id),),
            ).fetchone()

    def get_due_giveaways(self, now_ts):
        with self.lock:
            return self.conn.execute(
                "SELECT * FROM giveaways WHERE status='active' AND ends_at<=? ORDER BY ends_at ASC",
                (int(now_ts),),
            ).fetchall()

    def set_giveaway_status(self, message_id, status, only_if_active=False):
        with self.lock, self.conn:
            if only_if_active:
                cur = self.conn.execute(
                    "UPDATE giveaways SET status=? WHERE message_id=? AND status='active'",
                    (status, str(message_id)),
                )
            else:
                cur = self.conn.execute(
                    "UPDATE giveaways SET status=? WHERE message_id=?",
                    (status, str(message_id)),
                )
            return cur.rowcount > 0

    def add_giveaway_entry(self, message_id, user_id):
        try:
            with self.lock, self.conn:
                self.conn.execute(
                    "INSERT INTO giveaway_entries(message_id,user_id) VALUES(?,?)",
                    (str(message_id), str(user_id)),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def get_giveaway_entries(self, message_id):
        with self.lock:
            return self.conn.execute(
                "SELECT user_id FROM giveaway_entries WHERE message_id=?",
                (str(message_id),),
            ).fetchall()

    def count_giveaway_entries(self, message_id):
        with self.lock:
            row = self.conn.execute(
                "SELECT COUNT(*) AS count FROM giveaway_entries WHERE message_id=?",
                (str(message_id),),
            ).fetchone()
            return int(row["count"]) if row else 0


    def get_sales_message_id(self, license_key):
        with self.lock:
            row = self.conn.execute(
                "SELECT message_id FROM license_sales_messages WHERE license_key=?",
                (str(license_key),),
            ).fetchone()
            return str(row["message_id"]) if row else None

    def get_sales_metadata_json(self, license_key):
        with self.lock:
            row = self.conn.execute(
                "SELECT metadata_json FROM license_sales_messages WHERE license_key=?",
                (str(license_key),),
            ).fetchone()
            return str(row["metadata_json"]) if row else "{}"

    def set_sales_state(self, license_key, message_id, metadata_json):
        with self.lock, self.conn:
            self.conn.execute(
                """INSERT INTO license_sales_messages(license_key,message_id,metadata_json) VALUES(?,?,?)
                   ON CONFLICT(license_key) DO UPDATE SET
                       message_id=excluded.message_id,
                       metadata_json=excluded.metadata_json""",
                (str(license_key), str(message_id), str(metadata_json)),
            )

    def set_sales_message_id(self, license_key, message_id):
        metadata_json = self.get_sales_metadata_json(license_key)
        self.set_sales_state(license_key, message_id, metadata_json)
