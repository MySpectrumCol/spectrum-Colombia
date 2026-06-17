import os
import sqlite3
from contextlib import contextmanager


DATABASE_PATH = os.getenv("DATABASE_PATH", "spectrum.db")


def init_db() -> None:
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS results (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                ud REAL NOT NULL,
                d REAL NOT NULL,
                c REAL NOT NULL,
                i REAL NOT NULL,
                ui REAL NOT NULL,
                dominant_axis TEXT NOT NULL,
                dominant TEXT NOT NULL,
                summary TEXT NOT NULL,
                share_text TEXT NOT NULL,
                ip_hash TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        existing_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(results)").fetchall()
        }
        optional_columns = {
            "summary": "TEXT",
            "share_text": "TEXT",
            "ip_hash": "TEXT",
            "self_label": "TEXT",
            "card_image_path": "TEXT",
            "attempt_number": "INTEGER DEFAULT 1",
        }
        for column, column_type in optional_columns.items():
            if column not in existing_columns:
                conn.execute(f"ALTER TABLE results ADD COLUMN {column} {column_type}")

        # Crear tabla de sesiones
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                expires_at REAL NOT NULL
            )
            """
        )

        # Crear tabla de rate limits
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rate_limits (
                ip_hash TEXT NOT NULL,
                hit_timestamp REAL NOT NULL
            )
            """
        )

        # Crear índices para acelerar búsquedas y limpieza
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rate_limits_hit ON rate_limits(ip_hash, hit_timestamp)")

        conn.commit()



@contextmanager
def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
