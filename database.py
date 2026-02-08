import sqlite3
import hashlib
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path="/root/daily_brief/data/briefs.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mentions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source TEXT,
                    raw_text TEXT,
                    analysis_toon_phrase TEXT,
                    url TEXT,
                    hash TEXT UNIQUE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_wraps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE,
                    wrap_text TEXT
                )
            """)
            conn.commit()

    def add_mention(self, source, raw_text, analysis, title_hash, url=None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO mentions (source, raw_text, analysis_toon_phrase, hash, url) VALUES (?, ?, ?, ?, ?)",
                    (source, raw_text, analysis, title_hash, url)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # Hash already exists
            return False

    def is_duplicate(self, title_hash):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Check if hash exists in the last 24 hours
            yesterday = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("SELECT 1 FROM mentions WHERE hash = ? AND timestamp > ?", (title_hash, yesterday))
            return cursor.fetchone() is not None

    def get_recent_toon_phrases(self, limit=5):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT analysis_toon_phrase, url FROM mentions ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            return [f"{row[0]} [Source: {row[1]}]" if row[1] else row[0] for row in cursor.fetchall()]

    def get_daily_phrases(self, date_str):
        # date_str in 'YYYY-MM-DD' format
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT analysis_toon_phrase, url FROM mentions WHERE date(timestamp) = ?",
                (date_str,)
            )
            return [f"{row[0]} [Source: {row[1]}]" if row[1] else row[0] for row in cursor.fetchall()]

    def save_daily_wrap(self, date_str, wrap_text):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO daily_wraps (date, wrap_text) VALUES (?, ?)",
                (date_str, wrap_text)
            )
            conn.commit()

    @staticmethod
    def generate_hash(text):
        return hashlib.md5(text.encode('utf-8')).hexdigest()
