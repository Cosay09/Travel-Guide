# utils/db_utils.py
import os
import sqlite3
from config import DB_PATH


def init_db():
    """Initialize required database tables."""
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()
