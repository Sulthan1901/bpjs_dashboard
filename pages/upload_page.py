import streamlit as st
import pandas as pd
import io
from services.company_service import bulk_insert_companies, clear_all_companies, REQUIRED_COLUMNS
from services.log_service import log_action


def render():
    st.title("📤 Upload Data CSV")
    st.markdown("---")

    st.markdown("""
    ### Panduan Upload
    - File harus berformat **CSV** (`.csv`)
    - Kolom yang diperlukan:

    ```
    kode_wilayah, kode_kantor, nama_kantor, nama_pembina, npp,
    nama_perusahaan, alamat, kabupaten, pic, no_hp,
    total_tk, tk_dibawah_umk, status, keterangan, lampiran
    ```
    - Kolom `status` harus berisi salah satu dari: *Sudah Ada Balasan, Sudah Dihubungi Belum Balas, Nomor Tidak Bisa Dihubungi, Belum Dihubungi*
    - Kolom yang tidak ada akan diisi otomatis dengan nilai kosong
    """)

    # Download template
    st.markdown("#### 📥 Download Template CSV")
    template_df = pd.DataFrame(columns=REQUIRED_COLUMNS)
    csv_bytes = template_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Template",
        data=csv_bytes,
        file_name="template_bpjs_monitoring.csv",
        mime="text/csv"
    )

    st.markdown("---")
    st.markdown("#### 📂 Upload File CSV")

    replace_mode = st.checkbox("🔄 Hapus semua data lama sebelum upload", value=False)

    uploaded = st.file_uploader("Pilih file CSV", type=["csv"])

    if uploaded:
        try:
            # Try different encodings
            for enc in ["utf-8", "utf-8-sig", "latin1", "cp1252"]:
                try:
                    df = pd.read_csv(io.BytesIO(uploaded.read()), encoding=enc)
                    uploaded.seek(0)
                    break
                except Exception:
                    uploaded.seek(0)

            st.markdown(f"**Preview data ({len(df)} baris, {len(df.columns)} kolom):**")
            st.dataframe(df.head(10), use_container_width=True, hide_index=True)

            # Validate columns
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
            missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
            if missing_cols:
                st.warning(f"⚠️ Kolom berikut tidak ditemukan dan akan diisi kosong: **{', '.join(missing_cols)}**")

            if st.button("✅ Proses Upload", type="primary", use_container_width=True):
                if replace_mode:
                    clear_all_companies()
                    st.info("Data lama telah dihapus.")

                count = bulk_insert_companies(df)
                log_action(
                    st.session_state.get("username", "unknown"),
                    "upload_csv",
                    f"File: {uploaded.name} | {count} baris berhasil dimasukkan"
                )
                st.success(f"🎉 **{count} data perusahaan** berhasil diupload!")
                st.balloons()

        except Exception as e:
            st.error(f"❌ Gagal memproses file: {e}")
