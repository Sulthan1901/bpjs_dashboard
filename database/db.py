import psycopg2
import psycopg2.extras
import pandas as pd
import streamlit as st


def get_connection():
    """Koneksi PostgreSQL dari Supabase via st.secrets."""
    conn = psycopg2.connect(
        st.secrets["supabase"]["database_url"],
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn


def query_df(sql: str, params=None) -> pd.DataFrame:
    """
    Eksekusi SELECT query dan kembalikan sebagai DataFrame.
    Gunakan ini sebagai pengganti pd.read_sql_query agar
    kompatibel dengan psycopg2 + RealDictCursor.
    """
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(sql, params or ())
        rows = c.fetchall()
        if not rows:
            # Ambil nama kolom dari cursor description meski kosong
            cols = [desc[0] for desc in c.description] if c.description else []
            return pd.DataFrame(columns=cols)
        df = pd.DataFrame([dict(r) for r in rows])
        return df
    finally:
        conn.close()


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY,
            kode_wilayah TEXT,
            kode_kantor TEXT,
            nama_kantor TEXT,
            nama_pembina TEXT,
            npp TEXT,
            nama_perusahaan TEXT,
            alamat TEXT,
            kabupaten TEXT,
            pic TEXT,
            no_hp TEXT,
            total_tk INTEGER DEFAULT 0,
            tk_dibawah_umk INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Belum Dihubungi',
            keterangan TEXT,
            lampiran TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id SERIAL PRIMARY KEY,
            username TEXT,
            action TEXT,
            detail TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed default admin jika belum ada
    from services.auth_service import hash_password
    c.execute("SELECT id FROM users WHERE username = %s", ("admin",))
    if not c.fetchone():
        c.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            ("admin", hash_password("admin123"), "admin")
        )

    conn.commit()
    conn.close()
