import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from database.db import init_db
from services.auth_service import authenticate
from services.log_service import log_action

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="BPJS Binaan Monitoring",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Initialize DB ─────────────────────────────────────────────
init_db()

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a3c5e 0%, #0d2137 100%);
}

[data-testid="stSidebar"] * {
    color: #e8f4fd !important;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label {
    color: #a8d8f0 !important;
}

/* username text */
.sidebar-user {
    font-weight:600;
}

/* role badge */
.role-badge {
    background:#e6e6e6;
    color:black !important;
    padding:3px 8px;
    border-radius:6px;
    font-size:12px;
    margin-left:6px;
}

/* metric container */
.metric-container {
    background: #f0f7ff;
    border-radius: 10px;
    padding: 15px;
    border-left: 4px solid #1a3c5e;
}

.stMetric {
    background: white;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

h1 { color: #1a3c5e; }
h2 { color: #2c5f8a; }

/* buttons */
.stButton > button {
    background: #1a3c5e;
    color: white;
    border: none;
}

/* disable hover change */
.stButton > button:hover {
    background: #1a3c5e !important;
    color: white !important;
    border: none !important;
}

.stButton > button:focus {
    background: #1a3c5e !important;
    box-shadow: none !important;
}

.stButton > button:active {
    background: #1a3c5e !important;
}

</style>
""", unsafe_allow_html=True)


# ── Session State Init ────────────────────────────────────────
if "username" not in st.session_state:
    st.session_state["username"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None


# ── Login Page ────────────────────────────────────────────────
def show_login():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align:center; margin-bottom: 30px;'>
            <h3 style='color:#2c5f8a;'>Monitoring Dashboard</h3>
            <p style='color:#666;'>Sistem Monitoring Komunikasi Perusahaan Binaan BPJS</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Masukkan username")
            password = st.text_input("🔒 Password", type="password", placeholder="Masukkan password")
            submit = st.form_submit_button("🔐 Masuk", use_container_width=True, type="primary")

        if submit:
            user = authenticate(username, password)
            if user:
                st.session_state["username"] = user["username"]
                st.session_state["role"] = user["role"]
                log_action(user["username"], "login", "Login berhasil")
                st.success(f"Selamat datang, {user['username']}!")
                st.rerun()
            else:
                st.error("❌ Username atau password salah.")


# ── Main App ──────────────────────────────────────────────────
def show_app():
    from pages import home_page, monitoring_page, upload_page, analytics_page, log_page, user_page

    # Sidebar navigation
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align:center; padding: 15px 0; border-bottom: 1px solid #2c5f8a; margin-bottom: 15px;'>
            <div style='font-weight: bold; font-size: 14px;'>Monitoring Binaan BPJS Ketenagakerjaan</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
<div class="sidebar-user">
👤 {st.session_state['username']}
<span class="role-badge">{st.session_state['role']}</span>
</div>
""", unsafe_allow_html=True)
        st.markdown("---")

        menu_items = {
            "🏠 Dashboard": "home",
            "📋 Monitoring": "monitoring",
            "📤 Upload CSV": "upload",
            "📊 Analytics": "analytics",
            "📜 Activity Log": "logs",
        }

        if st.session_state["role"] == "admin":
            menu_items["👥 Manajemen User"] = "users"

        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "home"

        for label, key in menu_items.items():
            is_active = st.session_state["current_page"] == key
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state["current_page"] = key
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            log_action(st.session_state["username"], "logout", "")
            st.session_state["username"] = None
            st.session_state["role"] = None
            st.session_state["current_page"] = "home"
            st.rerun()

    # Page routing
    page = st.session_state.get("current_page", "home")
    if page == "home":
        home_page.render()
    elif page == "monitoring":
        monitoring_page.render()
    elif page == "upload":
        upload_page.render()
    elif page == "analytics":
        analytics_page.render()
    elif page == "logs":
        log_page.render()
    elif page == "users":
        user_page.render()


# ── Entry Point ───────────────────────────────────────────────
if st.session_state.get("username"):
    show_app()
else:
    show_login()
