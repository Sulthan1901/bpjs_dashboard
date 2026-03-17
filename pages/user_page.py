import streamlit as st
from services.auth_service import get_all_users, create_user, delete_user, change_password
from services.log_service import log_action


def render():
    st.title("👥 Manajemen User")
    st.markdown("---")

    if st.session_state.get("role") != "admin":
        st.error("⛔ Halaman ini hanya dapat diakses oleh Admin.")
        return

    tab1, tab2 = st.tabs(["📋 Daftar User", "➕ Tambah User"])

    with tab1:
        users = get_all_users()
        st.markdown(f"**Total: {len(users)} user**")

        for u in users:
            with st.expander(f"👤 {u['username']} — *{u['role']}*"):
                st.markdown(f"- **ID:** {u['id']}")
                st.markdown(f"- **Role:** {u['role']}")
                st.markdown(f"- **Dibuat:** {u['created_at']}")

                col1, col2 = st.columns(2)
                with col1:
                    new_pw = st.text_input(f"Password baru untuk {u['username']}", type="password", key=f"pw_{u['id']}")
                    if st.button("🔑 Ganti Password", key=f"chpw_{u['id']}"):
                        if new_pw:
                            change_password(u["id"], new_pw)
                            log_action(st.session_state["username"], "change_password", f"User: {u['username']}")
                            st.success("Password berhasil diubah.")
                        else:
                            st.warning("Masukkan password baru.")
                with col2:
                    if u["username"] != "admin":
                        if st.button(f"🗑️ Hapus User", key=f"del_{u['id']}", type="secondary"):
                            delete_user(u["id"])
                            log_action(st.session_state["username"], "delete_user", f"User: {u['username']}")
                            st.success(f"User {u['username']} dihapus.")
                            st.rerun()

    with tab2:
        st.subheader("Tambah User Baru")
        with st.form("add_user_form"):
            new_username = st.text_input("Username *")
            new_password = st.text_input("Password *", type="password")
            new_role = st.selectbox("Role *", ["user", "admin"])
            submit = st.form_submit_button("➕ Tambah User", type="primary", use_container_width=True)

        if submit:
            if not new_username or not new_password:
                st.error("Username dan password wajib diisi.")
            else:
                ok, msg = create_user(new_username, new_password, new_role)
                if ok:
                    log_action(
                        st.session_state["username"],
                        "create_user",
                        f"New user: {new_username} | role: {new_role}"
                    )
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ Gagal: {msg}")
