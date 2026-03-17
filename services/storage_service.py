"""
Supabase Storage Service
Handles upload, download, delete, dan signed URL untuk lampiran.
Menggunakan Supabase REST API langsung (tanpa SDK) agar tidak perlu dependency tambahan.
"""

import streamlit as st
import requests
import os
from utils.file_wa_utils import get_mime_type

BUCKET = "lampiran"


def _headers(content_type: str = "application/json") -> dict:
    """Build auth headers untuk Supabase Storage REST API."""
    return {
        "Authorization": f"Bearer {st.secrets['supabase']['service_role_key']}",
        "apikey": st.secrets["supabase"]["service_role_key"],
        "Content-Type": content_type,
    }


def _storage_url(path: str = "") -> str:
    base = st.secrets["supabase"]["url"].rstrip("/")
    return f"{base}/storage/v1/object/{BUCKET}/{path}"


def _signed_url_endpoint(path: str) -> str:
    base = st.secrets["supabase"]["url"].rstrip("/")
    return f"{base}/storage/v1/object/sign/{BUCKET}/{path}"


# ── Upload ────────────────────────────────────────────────────────────────────

def upload_file(file_bytes: bytes, filename: str) -> tuple[bool, str]:
    """
    Upload file ke Supabase Storage.
    Returns (success: bool, storage_path: str | error_message: str)
    """
    mime = get_mime_type(filename)
    url = _storage_url(filename)

    # Coba upsert (update jika sudah ada, insert jika belum)
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {st.secrets['supabase']['service_role_key']}",
            "apikey": st.secrets["supabase"]["service_role_key"],
            "Content-Type": mime,
            "x-upsert": "true",
        },
        data=file_bytes,
        timeout=30,
    )

    if resp.status_code in (200, 201):
        return True, filename
    else:
        err = resp.json().get("message", resp.text)
        return False, f"Upload gagal: {err}"


# ── Download / Get bytes ───────────────────────────────────────────────────────

def download_file(filename: str) -> tuple[bool, bytes | str]:
    """
    Download file dari Supabase Storage.
    Returns (success: bool, file_bytes | error_message)
    """
    url = _storage_url(filename)
    resp = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {st.secrets['supabase']['service_role_key']}",
            "apikey": st.secrets["supabase"]["service_role_key"],
        },
        timeout=30,
    )
    if resp.status_code == 200:
        return True, resp.content
    else:
        return False, f"File tidak ditemukan atau gagal diunduh (status {resp.status_code})"


# ── Signed URL (untuk preview / akses sementara) ─────────────────────────────

def get_signed_url(filename: str, expires_in: int = 3600) -> tuple[bool, str]:
    """
    Buat signed URL yang berlaku selama `expires_in` detik (default 1 jam).
    Returns (success: bool, signed_url | error_message)
    """
    endpoint = _signed_url_endpoint(filename)
    resp = requests.post(
        endpoint,
        headers=_headers("application/json"),
        json={"expiresIn": expires_in},
        timeout=15,
    )
    if resp.status_code == 200:
        data = resp.json()
        signed_path = data.get("signedURL") or data.get("signedUrl", "")
        if signed_path:
            base = st.secrets["supabase"]["url"].rstrip("/")
            # signed_path mungkin sudah full URL atau relative
            if signed_path.startswith("http"):
                return True, signed_path
            return True, f"{base}{signed_path}"
        return False, "Signed URL tidak ditemukan dalam response"
    else:
        err = resp.json().get("message", resp.text)
        return False, f"Gagal membuat signed URL: {err}"


# ── Delete ────────────────────────────────────────────────────────────────────

def delete_file(filename: str) -> tuple[bool, str]:
    """
    Hapus file dari Supabase Storage.
    Returns (success: bool, message)
    """
    base = st.secrets["supabase"]["url"].rstrip("/")
    url = f"{base}/storage/v1/object/{BUCKET}"
    resp = requests.delete(
        url,
        headers=_headers("application/json"),
        json={"prefixes": [filename]},
        timeout=15,
    )
    if resp.status_code == 200:
        return True, "File berhasil dihapus."
    else:
        err = resp.json().get("message", resp.text)
        return False, f"Gagal menghapus file: {err}"


# ── List files ────────────────────────────────────────────────────────────────

def list_files(prefix: str = "") -> list[dict]:
    """List semua file dalam bucket, opsional filter by prefix."""
    base = st.secrets["supabase"]["url"].rstrip("/")
    url = f"{base}/storage/v1/object/list/{BUCKET}"
    resp = requests.post(
        url,
        headers=_headers("application/json"),
        json={"prefix": prefix, "limit": 1000, "offset": 0},
        timeout=15,
    )
    if resp.status_code == 200:
        return resp.json()
    return []
