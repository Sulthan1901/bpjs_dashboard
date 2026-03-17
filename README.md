# BPJS Binaan Monitoring Dashboard

Streamlit + Supabase (PostgreSQL + Storage)

## Stack
- **Frontend:** Streamlit
- **Database:** Supabase PostgreSQL
- **File Storage:** Supabase Storage (bucket: `lampiran`)
- **Charts:** Plotly

---

## Setup Supabase (lakukan sekali)

### A. Database
1. Buat project baru di https://supabase.com
2. Region: **Southeast Asia (Singapore)**
3. **Project Settings → Database → URI** → copy connection string

### B. Storage Bucket
1. Sidebar kiri → **Storage** → **New Bucket**
2. Nama: `lampiran`
3. Public: **OFF** (private)
4. Klik **Create bucket**

### C. Credentials
Dari **Project Settings → API**, ambil:
- **Project URL** → `url`
- **service_role key** (bukan anon!) → `service_role_key`

---

## Konfigurasi Lokal

Buat file `.streamlit/secrets.toml`:

```toml
[supabase]
database_url    = "postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres"
url             = "https://[REF].supabase.co"
service_role_key = "eyJhbGci..."
```

Jalankan:
```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Deploy ke Streamlit Cloud

1. Push ke GitHub (**jangan** include `secrets.toml`)
2. https://share.streamlit.io → deploy repo
3. **Advanced settings → Secrets** → paste:
```toml
[supabase]
database_url     = "..."
url              = "..."
service_role_key = "..."
```

---

## Login Default
- **Username:** `admin`  
- **Password:** `admin123`

> ⚠️ Ganti password setelah pertama login!

---

## Cara Kerja Lampiran

| Aksi | Mekanisme |
|------|-----------|
| Upload | File → Supabase Storage bucket `lampiran` |
| Download | Fetch bytes dari Storage → st.download_button |
| Preview gambar | Fetch bytes → st.image inline |
| Buka di browser | Signed URL (berlaku 1 jam) |
| Hapus | Delete dari Storage + clear DB field |

File disimpan dengan nama `{id_perusahaan}_{nama_file}` untuk menghindari konflik.

---

## Struktur Proyek
```
bpjs_dashboard/
├── app.py
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── secrets.toml          ← JANGAN di-commit!
├── database/
│   └── db.py                 ← Koneksi PostgreSQL
├── services/
│   ├── auth_service.py
│   ├── company_service.py
│   ├── log_service.py
│   └── storage_service.py    ← Supabase Storage API
├── pages/
│   ├── home_page.py
│   ├── monitoring_page.py    ← Download/preview/delete lampiran
│   ├── upload_page.py
│   ├── analytics_page.py
│   ├── log_page.py
│   └── user_page.py
└── utils/
    ├── helpers.py
    └── file_wa_utils.py
```
