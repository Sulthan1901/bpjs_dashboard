import hashlib
import os
from database.db import get_connection


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split(":")
        return hashlib.sha256((salt + password).encode()).hexdigest() == hashed
    except Exception:
        return False


def authenticate(username: str, password: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = %s", (username,))
    row = c.fetchone()
    conn.close()
    if row and verify_password(password, row["password_hash"]):
        return dict(row)
    return None


def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, role, created_at FROM users ORDER BY id")
    rows = c.fetchall()
    conn.close()
    # Konversi RealDictRow → dict biasa, cast created_at ke string
    result = []
    for r in rows:
        d = dict(r)
        if d.get("created_at"):
            d["created_at"] = str(d["created_at"])
        result.append(d)
    return result


def create_user(username: str, password: str, role: str):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            (username, hash_password(password), role)
        )
        conn.commit()
        return True, "User berhasil dibuat."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def delete_user(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()


def change_password(user_id: int, new_password: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET password_hash = %s WHERE id = %s",
        (hash_password(new_password), user_id)
    )
    conn.commit()
    conn.close()
