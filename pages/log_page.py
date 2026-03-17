import streamlit as st
from services.log_service import get_logs, clear_logs


def render():
    st.title("📜 Activity Log")
    st.markdown("---")

    logs_df = get_logs(limit=500)

    if logs_df.empty:
        st.info("Belum ada aktivitas tercatat.")
        return

    # Filter
    col1, col2 = st.columns(2)
    with col1:
        users = ["Semua"] + sorted(logs_df["username"].dropna().unique().tolist())
        filter_user = st.selectbox("Filter User", users)
    with col2:
        actions = ["Semua"] + sorted(logs_df["action"].dropna().unique().tolist())
        filter_action = st.selectbox("Filter Aksi", actions)

    filtered = logs_df.copy()
    if filter_user != "Semua":
        filtered = filtered[filtered["username"] == filter_user]
    if filter_action != "Semua":
        filtered = filtered[filtered["action"] == filter_action]

    st.markdown(f"**{len(filtered)} log ditampilkan**")
    st.dataframe(
        filtered[["timestamp", "username", "action", "detail"]].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        height=450
    )

    st.markdown("---")
    if st.session_state.get("role") == "admin":
        if st.button("🗑️ Hapus Semua Log", type="secondary"):
            clear_logs()
            st.success("Log berhasil dihapus.")
            st.rerun()
