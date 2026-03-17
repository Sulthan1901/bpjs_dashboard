import pandas as pd
from database.db import get_connection, query_df

STATUS_OPTIONS = [
    "Belum Dihubungi",
    "Sudah Dihubungi Belum Balas",
    "Nomor Tidak Bisa Dihubungi",
    "Sudah Ada Balasan",
]

REQUIRED_COLUMNS = [
    "kode_wilayah", "kode_kantor", "nama_kantor", "nama_pembina",
    "npp", "nama_perusahaan", "alamat", "kabupaten", "pic", "no_hp",
    "total_tk", "tk_dibawah_umk", "status", "keterangan", "lampiran"
]

# Kolom yang harus bertipe int
INT_COLUMNS = ["total_tk", "tk_dibawah_umk"]


def _fix_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Pastikan kolom numerik bertipe int, bukan string."""
    for col in INT_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def get_all_companies() -> pd.DataFrame:
    df = query_df("SELECT * FROM companies ORDER BY id")
    return _fix_dtypes(df)


def get_company_by_id(company_id: int) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM companies WHERE id = %s", (company_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def update_company_status(company_id: int, status: str, keterangan: str, lampiran: str = None):
    conn = get_connection()
    c = conn.cursor()
    if lampiran:
        c.execute(
            """UPDATE companies
               SET status = %s, keterangan = %s, lampiran = %s, updated_at = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (status, keterangan, lampiran, company_id)
        )
    else:
        c.execute(
            """UPDATE companies
               SET status = %s, keterangan = %s, updated_at = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (status, keterangan, company_id)
        )
    conn.commit()
    conn.close()


def bulk_insert_companies(df: pd.DataFrame) -> int:
    conn = get_connection()
    c = conn.cursor()

    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df["status"] = df["status"].apply(
        lambda x: x if x in STATUS_OPTIONS else "Belum Dihubungi"
    )

    # Paksa kolom int + ganti NaN → None untuk PostgreSQL
    for col in INT_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df = df.where(pd.notnull(df), None)

    inserted = 0
    for _, row in df.iterrows():
        c.execute("""
            INSERT INTO companies (
                kode_wilayah, kode_kantor, nama_kantor, nama_pembina,
                npp, nama_perusahaan, alamat, kabupaten, pic, no_hp,
                total_tk, tk_dibawah_umk, status, keterangan, lampiran
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            row.get("kode_wilayah"), row.get("kode_kantor"),
            row.get("nama_kantor"), row.get("nama_pembina"),
            row.get("npp"), row.get("nama_perusahaan"),
            row.get("alamat"), row.get("kabupaten"),
            row.get("pic"), row.get("no_hp"),
            int(row.get("total_tk") or 0),
            int(row.get("tk_dibawah_umk") or 0),
            row.get("status") or "Belum Dihubungi",
            row.get("keterangan"), row.get("lampiran")
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def get_status_summary() -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT status, COUNT(*) as count FROM companies GROUP BY status")
    rows = c.fetchall()
    conn.close()
    summary = {s: 0 for s in STATUS_OPTIONS}
    for row in rows:
        if row["status"] in summary:
            summary[row["status"]] = int(row["count"])
    summary["total"] = sum(summary.values())
    return summary


def get_companies_by_kabupaten() -> pd.DataFrame:
    df = query_df(
        "SELECT kabupaten, COUNT(*) as jumlah FROM companies GROUP BY kabupaten ORDER BY jumlah DESC"
    )
    if not df.empty:
        df["jumlah"] = df["jumlah"].astype(int)
    return df


def get_companies_by_pembina() -> pd.DataFrame:
    df = query_df(
        "SELECT nama_pembina, COUNT(*) as jumlah FROM companies GROUP BY nama_pembina ORDER BY jumlah DESC"
    )
    if not df.empty:
        df["jumlah"] = df["jumlah"].astype(int)
    return df


def get_tk_distribution() -> pd.DataFrame:
    df = query_df(
        """SELECT nama_perusahaan, total_tk, tk_dibawah_umk
           FROM companies WHERE total_tk > 0
           ORDER BY total_tk DESC LIMIT 20"""
    )
    return _fix_dtypes(df)


def delete_company(company_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM companies WHERE id = %s", (company_id,))
    conn.commit()
    conn.close()


def clear_all_companies():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM companies")
    conn.commit()
    conn.close()
