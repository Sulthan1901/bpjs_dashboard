import streamlit as st


def require_login():
    """Returns True if user is logged in, else shows login page."""
    return "username" in st.session_state and st.session_state["username"]


def get_current_user():
    return st.session_state.get("username", "")


def get_current_role():
    return st.session_state.get("role", "user")


def format_number(n):
    return f"{n:,}"
