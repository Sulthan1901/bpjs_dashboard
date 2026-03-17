import pandas as pd
from database.db import get_connection, query_df


def log_action(username: str, action: str, detail: str = ""):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO activity_logs (username, action, detail) VALUES (%s, %s, %s)",
        (username, action, detail)
    )
    conn.commit()
    conn.close()


def get_logs(limit: int = 200) -> pd.DataFrame:
    df = query_df(
        "SELECT id, username, action, detail, timestamp FROM activity_logs ORDER BY timestamp DESC LIMIT %s",
        (limit,)
    )
    # Pastikan timestamp tampil sebagai string yang rapi
    if not df.empty and "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


def clear_logs():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM activity_logs")
    conn.commit()
    conn.close()
