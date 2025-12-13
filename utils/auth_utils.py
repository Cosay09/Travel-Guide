# utils/auth_utils.py
import sqlite3
import hashlib
from config import DB_PATH


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(email: str, password: str) -> bool:
    """Return True if email/password is valid."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT password FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return False

    return row[0] == hash_password(password)


def register_user(name: str, email: str, password: str) -> bool:
    """Create a new user. Returns False if email exists."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (email, name, password) VALUES (?, ?, ?)",
            (email, name, hash_password(password))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
