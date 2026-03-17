import streamlit as st
import os
import pandas as pd
from services.company_service import (
    get_all_companies, update_company_status,
    delete_company, STATUS_OPTIONS
)
from services.log_service import log_action
from services.storage_service import (
    upload_file, download_file, delete_file
)
from utils.file_wa_utils import (
    make_wa_link, get_file_icon, is_image, is_pdf, get_mime_type
)

WA_TEMPLATE = """Yth. Bapak/Ibu {pic},

Perkenalkan kami dari BPJS Ketenagakerjaan ingin menghubungi Perusahaan {nama_perusahaan} terkait program kepesertaan BPJS.

Mohon kesediaan Bapak/Ibu untuk dapat dihubungi lebih lanjut.

Terima kasih."""


def _safe_filename(company_id: int, original_name: str) -> str:
    """Buat nama file yang aman: id_namafile.ext"""
    clean = original_name.replace(" ", "_")
    # Hindari karakter berbahaya
    import re
    clean = re.sub(r"[^\w.\-]", "_", clean)
    return f"{company_id}_{clean}"


# ── Render Lampiran ───────────────────────────────────────────────────────────

def render_lampiran(company_row: dict):
    lampiran = str(company_row.get("lampiran", "")).strip()
    company_id = company_row.get("id", 0)

    if not lampiran or lampiran in ["nan", "None", ""]:
        st.info("📭 Belum ada lampiran untuk perusahaan ini.")
        return

    icon = get_file_icon(lampiran)
    ext = os.path.splitext(lampiran)[1].upper()
    st.markdown(f"**File tersimpan:** {icon} `{lampiran}`")

    # ── GAMBAR: tombol lihat + tombol download ────────────────────
    if is_image(lampiran):
        col_lihat, col_dl, col_del = st.columns([2, 2, 1])

        with col_lihat:
            if st.button("🖼️ Lihat Gambar", use_container_width=True,
                         key=f"btn_lihat_{company_id}", type="primary"):
                # toggle preview
                key_show = f"show_img_{company_id}"
                st.session_state[key_show] = not st.session_state.get(key_show, False)

        with col_dl:
            # Fetch bytes untuk download
            if st.button("⬇️ Download", use_container_width=True,
                         key=f"btn_dl_{company_id}"):
                with st.spinner("Mengambil file..."):
                    ok, result = download_file(lampiran)
                if ok:
                    st.session_state[f"dl_bytes_{company_id}"] = result
                else:
                    st.error(f"❌ {result}")

        with col_del:
            if st.button("🗑️", use_container_width=True,
                         key=f"btn_del_lamp_{company_id}", help="Hapus lampiran"):
                st.session_state[f"confirm_del_lamp_{company_id}"] = True

        # Tombol download muncul setelah fetch
        if st.session_state.get(f"dl_bytes_{company_id}"):
            st.download_button(
                label=f"💾 Simpan {icon} {lampiran}",
                data=st.session_state[f"dl_bytes_{company_id}"],
                file_name=lampiran,
                mime=get_mime_type(lampiran),
                use_container_width=True,
                key=f"dl_save_{company_id}"
            )

        # Preview gambar inline
        if st.session_state.get(f"show_img_{company_id}", False):
            with st.spinner("Memuat gambar dari storage..."):
                ok, result = download_file(lampiran)
            if ok:
                st.image(result, caption=lampiran, use_container_width=True)
                if st.button("✖️ Tutup Gambar", key=f"btn_tutup_{company_id}"):
                    st.session_state[f"show_img_{company_id}"] = False
                    st.rerun()
            else:
                st.error(f"❌ Gagal memuat gambar: {result}")

    # ── PDF / WORD / EXCEL: langsung fetch & download ─────────────
    else:
        col_dl, col_del = st.columns([4, 1])

        with col_dl:
            if st.button(f"⬇️ Download {icon} {ext}",
                         use_container_width=True, key=f"btn_dl_{company_id}",
                         type="primary"):
                with st.spinner(f"Mengambil file {ext} dari storage..."):
                    ok, result = download_file(lampiran)
                if ok:
                    st.session_state[f"dl_bytes_{company_id}"] = result
                else:
                    st.error(f"❌ {result}")

        with col_del:
            if st.button("🗑️", use_container_width=True,
                         key=f"btn_del_lamp_{company_id}", help="Hapus lampiran"):
                st.session_state[f"confirm_del_lamp_{company_id}"] = True

        # Tombol simpan muncul setelah fetch berhasil
        if st.session_state.get(f"dl_bytes_{company_id}"):
            st.download_button(
                label=f"💾 Klik di sini untuk menyimpan {lampiran}",
                data=st.session_state[f"dl_bytes_{company_id}"],
                file_name=lampiran,
                mime=get_mime_type(lampiran),
                use_container_width=True,
                key=f"dl_save_{company_id}"
            )

    # ── Konfirmasi hapus ──────────────────────────────────────────
    if st.session_state.get(f"confirm_del_lamp_{company_id}", False):
        st.warning("⚠️ Yakin ingin menghapus lampiran ini?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Ya, hapus", key=f"confirm_yes_{company_id}", type="primary"):
                ok, msg = delete_file(lampiran)
                if ok:
                    update_company_status(
                        company_id,
                        company_row.get("status", STATUS_OPTIONS[0]),
                        company_row.get("keterangan") or "",
                        ""
                    )
                    log_action(st.session_state.get("username", "unknown"),
                               "delete_lampiran",
                               f"ID={company_id} | {lampiran}")
                    # Bersihkan session state terkait
                    for k in [f"dl_bytes_{company_id}", f"show_img_{company_id}",
                               f"confirm_del_lamp_{company_id}"]:
                        st.session_state.pop(k, None)
                    st.success("Lampiran berhasil dihapus.")
                    st.rerun()
                else:
                    st.error(msg)
        with c2:
            if st.button("❌ Batal", key=f"confirm_no_{company_id}"):
                st.session_state[f"confirm_del_lamp_{company_id}"] = False
                st.rerun()


# ── Render WA ─────────────────────────────────────────────────────────────────

def render_wa_section(company_row: dict):
    no_hp = str(company_row.get("no_hp", "")).strip()
    pic = str(company_row.get("pic", "PIC")).strip()
    nama = str(company_row.get("nama_perusahaan", "")).strip()

    if not no_hp or no_hp in ["nan", "None", ""]:
        st.warning("⚠️ Nomor HP tidak tersedia untuk perusahaan ini.")
        return

    st.markdown(f"""
    <div style="background:#e8f5e9; padding:12px; border-radius:8px;
                border-left:4px solid #25D366; margin-bottom:12px;">
        <b>📱 Nomor HP:</b> {no_hp}<br>
        <b>👤 PIC:</b> {pic}
    </div>
    """, unsafe_allow_html=True)

    default_msg = WA_TEMPLATE.format(pic=pic, nama_perusahaan=nama)
    custom_msg = st.text_area(
        "✏️ Edit pesan sebelum dikirim:",
        value=default_msg,
        height=160,
        key=f"wa_msg_{company_row.get('id', 0)}"
    )

    wa_url = make_wa_link(no_hp, custom_msg)
    wa_plain = make_wa_link(no_hp)

    col1, col2 = st.columns(2)
    with col1:
        if wa_url:
            st.markdown(
                f'<a href="{wa_url}" target="_blank" style="display:block; text-align:center;'
                f'background-color:#25D366; color:white; padding:12px 20px; border-radius:8px;'
                f'text-decoration:none; font-weight:bold; font-size:15px;">'
                f'💬 Chat dengan Pesan</a>',
                unsafe_allow_html=True
            )
    with col2:
        if wa_plain:
            st.markdown(
                f'<a href="{wa_plain}" target="_blank" style="display:block; text-align:center;'
                f'background-color:#128C7E; color:white; padding:12px 20px; border-radius:8px;'
                f'text-decoration:none; font-weight:bold; font-size:15px;">'
                f'📞 Buka Chat (Tanpa Pesan)</a>',
                unsafe_allow_html=True
            )

    st.caption("⚡ Membuka WhatsApp Web atau aplikasi WhatsApp di tab baru.")

    wa_key = f"wa_logged_{company_row.get('id', 0)}"
    if not st.session_state.get(wa_key, False):
        log_action(st.session_state.get("username", "unknown"), "open_whatsapp",
                   f"ID={company_row.get('id')} | {nama} | {no_hp}")
        st.session_state[wa_key] = True


# ── Upload Helper ─────────────────────────────────────────────────────────────

def handle_upload_lampiran(uploaded_file, company_id: int, company_row: dict) -> str | None:
    """
    Upload file ke Supabase Storage, return storage filename jika sukses.
    """
    safe_name = _safe_filename(company_id, uploaded_file.name)
    file_bytes = uploaded_file.getbuffer()

    with st.spinner(f"Mengupload {uploaded_file.name} ke Supabase Storage..."):
        ok, result = upload_file(bytes(file_bytes), safe_name)

    if ok:
        log_action(
            st.session_state.get("username", "unknown"),
            "upload_lampiran",
            f"ID={company_id} | {company_row.get('nama_perusahaan')} | {safe_name}"
        )
        return result  # storage filename/path
    else:
        st.error(f"❌ {result}")
        return None


# ── Main Render ───────────────────────────────────────────────────────────────

def render():
    st.title("📋 Monitoring Perusahaan Binaan")
    st.markdown("---")

    df = get_all_companies()
    if df.empty:
        st.info("Belum ada data perusahaan. Silakan upload CSV terlebih dahulu.")
        return

    # ── Filter & Search ──────────────────────────────────────────
    with st.expander("🔍 Filter Data", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_status = st.multiselect("Filter Status", options=STATUS_OPTIONS, default=STATUS_OPTIONS)
        with col2:
            kabupaten_list = ["Semua"] + sorted(df["kabupaten"].dropna().unique().tolist())
            filter_kab = st.selectbox("Filter Kabupaten", kabupaten_list)
        with col3:
            pembina_list = ["Semua"] + sorted(df["nama_pembina"].dropna().unique().tolist())
            filter_pembina = st.selectbox("Filter Pembina", pembina_list)

    filtered = df.copy()
    if filter_status:
        filtered = filtered[filtered["status"].isin(filter_status)]
    if filter_kab != "Semua":
        filtered = filtered[filtered["kabupaten"] == filter_kab]
    if filter_pembina != "Semua":
        filtered = filtered[filtered["nama_pembina"] == filter_pembina]

    search = st.text_input("🔎 Cari nama perusahaan / NPP / PIC")
    if search:
        mask = (
            filtered["nama_perusahaan"].str.contains(search, case=False, na=False) |
            filtered["npp"].str.contains(search, case=False, na=False) |
            filtered["pic"].str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]

    st.markdown(f"**Total data: {len(filtered)} perusahaan**")

    # ── Tabel ────────────────────────────────────────────────────
    display_cols = ["id", "nama_kantor", "nama_pembina", "npp", "nama_perusahaan",
                    "kabupaten", "pic", "no_hp", "total_tk", "tk_dibawah_umk",
                    "status", "keterangan", "lampiran"]
    existing_cols = [c for c in display_cols if c in filtered.columns]
    st.dataframe(filtered[existing_cols].reset_index(drop=True),
                 use_container_width=True, hide_index=True, height=280)

    st.markdown("---")
    if filtered.empty:
        st.warning("Tidak ada data untuk ditampilkan.")
        return

    # ── Pilih Perusahaan ─────────────────────────────────────────
    company_options = {
        f"[{row['id']}] {row['nama_perusahaan']}  ·  {row['status']}": row['id']
        for _, row in filtered.iterrows()
    }
    selected_label = st.selectbox("🏢 Pilih Perusahaan untuk dikelola:", list(company_options.keys()))
    selected_id = company_options[selected_label]
    company_row = df[df["id"] == selected_id].iloc[0].to_dict()

    # ── Info Card ────────────────────────────────────────────────
    status_color = {
        "Sudah Ada Balasan": "#2ecc71",
        "Sudah Dihubungi Belum Balas": "#f39c12",
        "Nomor Tidak Bisa Dihubungi": "#e74c3c",
        "Belum Dihubungi": "#95a5a6"
    }.get(company_row.get("status", ""), "#95a5a6")

    st.markdown(f"""
    <div style="background:#f8faff; padding:16px; border-radius:10px;
                border-left:5px solid {status_color}; margin-bottom:16px;">
        <h4 style="margin:0 0 6px 0; color:#1a3c5e;">🏢 {company_row['nama_perusahaan']}</h4>
        <div style="display:flex; gap:24px; flex-wrap:wrap; color:#555; font-size:14px;">
            <span>📌 <b>Kab:</b> {company_row.get('kabupaten','—')}</span>
            <span>🆔 <b>NPP:</b> {company_row.get('npp','—')}</span>
            <span>👤 <b>PIC:</b> {company_row.get('pic','—')}</span>
            <span>📱 <b>HP:</b> {company_row.get('no_hp','—')}</span>
            <span>👷 <b>Total TK:</b> {company_row.get('total_tk',0)}</span>
            <span>⚠️ <b>Bawah UMK:</b> {company_row.get('tk_dibawah_umk',0)}</span>
        </div>
        <div style="margin-top:8px;">
            <span style="background:{status_color}; color:white; padding:3px 10px;
                         border-radius:12px; font-size:13px; font-weight:bold;">
                {company_row.get('status','—')}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────
    tab_edit, tab_lampiran, tab_wa = st.tabs([
        "✏️ Edit Status & Keterangan",
        "📎 Lampiran",
        "💬 WhatsApp"
    ])

    # ── Tab Edit ─────────────────────────────────────────────────
    with tab_edit:
        with st.form("edit_form"):
            current_status = (company_row["status"]
                              if company_row.get("status") in STATUS_OPTIONS
                              else STATUS_OPTIONS[0])
            new_status = st.selectbox("Status *", STATUS_OPTIONS,
                                      index=STATUS_OPTIONS.index(current_status))
            new_keterangan = st.text_area(
                "Keterangan (bebas diisi)",
                value=company_row.get("keterangan") or "",
                placeholder="Contoh: perusahaan meminta waktu, nomor PIC berubah, sudah kirim email..."
            )
            uploaded_file = st.file_uploader(
                "Upload / Ganti Lampiran (opsional)",
                type=["pdf", "jpg", "jpeg", "png", "xlsx", "docx"]
            )
            col_s, col_d = st.columns([3, 1])
            with col_s:
                submit = st.form_submit_button("💾 Simpan Perubahan", use_container_width=True, type="primary")
            with col_d:
                delete_btn = st.form_submit_button("🗑️ Hapus Data", use_container_width=True)

        if submit:
            lampiran_path = company_row.get("lampiran") or ""
            if uploaded_file:
                new_path = handle_upload_lampiran(uploaded_file, selected_id, company_row)
                if new_path:
                    lampiran_path = new_path
            update_company_status(selected_id, new_status, new_keterangan, lampiran_path)
            log_action(st.session_state.get("username", "unknown"), "edit_company",
                       f"ID={selected_id} | {company_row['nama_perusahaan']} | status={new_status}")
            st.success("✅ Data berhasil diperbarui!")
            st.rerun()

        if delete_btn:
            if st.session_state.get("role") == "admin":
                delete_company(selected_id)
                log_action(st.session_state.get("username", "unknown"), "delete_company",
                           f"ID={selected_id} | {company_row['nama_perusahaan']}")
                st.success("Data berhasil dihapus.")
                st.rerun()
            else:
                st.error("Hanya admin yang dapat menghapus data.")

    # ── Tab Lampiran ─────────────────────────────────────────────
    with tab_lampiran:
        st.subheader("📎 Lampiran Perusahaan")
        st.caption("File disimpan di Supabase Storage — aman & persist meskipun app di-restart.")
        render_lampiran(company_row)

        st.markdown("---")
        st.markdown("##### 📤 Upload Lampiran Baru")
        new_lampiran = st.file_uploader(
            "Pilih file (PDF, gambar, Excel, Word) — maks 5MB",
            type=["pdf", "jpg", "jpeg", "png", "xlsx", "docx"],
            key="lampiran_tab_upload"
        )
        if new_lampiran:
            # Cek ukuran file (5MB limit)
            file_size_mb = len(new_lampiran.getbuffer()) / (1024 * 1024)
            if file_size_mb > 5:
                st.error(f"❌ File terlalu besar ({file_size_mb:.1f} MB). Maksimal 5 MB.")
            else:
                st.caption(f"Ukuran: {file_size_mb:.2f} MB")
                if st.button("💾 Simpan Lampiran ke Supabase", type="primary"):
                    new_path = handle_upload_lampiran(new_lampiran, selected_id, company_row)
                    if new_path:
                        update_company_status(
                            selected_id,
                            company_row.get("status", STATUS_OPTIONS[0]),
                            company_row.get("keterangan") or "",
                            new_path
                        )
                        st.success(f"✅ Lampiran **{new_lampiran.name}** berhasil disimpan ke Supabase Storage!")
                        st.rerun()

    # ── Tab WhatsApp ─────────────────────────────────────────────
    with tab_wa:
        st.subheader("💬 Kirim Pesan via WhatsApp")
        render_wa_section(company_row)
