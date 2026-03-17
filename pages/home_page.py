import streamlit as st
import plotly.express as px
import pandas as pd
from services.company_service import get_status_summary, get_all_companies, STATUS_OPTIONS


def render():
    st.title("🏠 Dashboard Monitoring BPJS Binaan")
    st.markdown("---")

    summary = get_status_summary()
    total = summary["total"]

    # KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📋 Total Perusahaan", total)
    with col2:
        val = summary.get("Sudah Ada Balasan", 0)
        pct = f"{val/total*100:.1f}%" if total else "0%"
        st.metric("✅ Sudah Ada Balasan", val, delta=pct)
    with col3:
        val = summary.get("Sudah Dihubungi Belum Balas", 0)
        pct = f"{val/total*100:.1f}%" if total else "0%"
        st.metric("📞 Dihubungi Belum Balas", val, delta=pct)
    with col4:
        val = summary.get("Nomor Tidak Bisa Dihubungi", 0)
        pct = f"{val/total*100:.1f}%" if total else "0%"
        st.metric("❌ Tidak Bisa Dihubungi", val, delta=pct)
    with col5:
        val = summary.get("Belum Dihubungi", 0)
        pct = f"{val/total*100:.1f}%" if total else "0%"
        st.metric("⏳ Belum Dihubungi", val, delta=pct)

    st.markdown("---")

    if total == 0:
        st.info("Belum ada data perusahaan. Silakan upload CSV terlebih dahulu.")
        return

    col_chart, col_bar = st.columns([1, 1])

    with col_chart:
        st.subheader("Distribusi Status")
        pie_data = {k: v for k, v in summary.items() if k != "total" and v > 0}
        fig_pie = px.pie(
            values=list(pie_data.values()),
            names=list(pie_data.keys()),
            color_discrete_sequence=["#2ecc71", "#f39c12", "#e74c3c", "#95a5a6"],
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=True, margin=dict(t=10, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        st.subheader("Jumlah per Status")
        bar_df = pd.DataFrame([
            {"Status": k, "Jumlah": v}
            for k, v in summary.items() if k != "total"
        ])
        color_map = {
            "Sudah Ada Balasan": "#2ecc71",
            "Sudah Dihubungi Belum Balas": "#f39c12",
            "Nomor Tidak Bisa Dihubungi": "#e74c3c",
            "Belum Dihubungi": "#95a5a6"
        }
        fig_bar = px.bar(
            bar_df, x="Status", y="Jumlah",
            color="Status", color_discrete_map=color_map,
            text="Jumlah"
        )
        fig_bar.update_layout(showlegend=False, xaxis_tickangle=-20, margin=dict(t=10, b=10))
        fig_bar.update_traces(textposition="outside")
        st.plotly_chart(fig_bar, use_container_width=True)

    # Recent activity
    st.markdown("---")
    st.subheader("📊 Ringkasan Data")
    df = get_all_companies()
    if not df.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Top 5 Kabupaten**")
            top_kab = df.groupby("kabupaten").size().reset_index(name="jumlah").sort_values("jumlah", ascending=False).head(5)
            st.dataframe(top_kab, use_container_width=True, hide_index=True)
        with col_b:
            st.markdown("**Top 5 Pembina**")
            top_pem = df.groupby("nama_pembina").size().reset_index(name="jumlah").sort_values("jumlah", ascending=False).head(5)
            st.dataframe(top_pem, use_container_width=True, hide_index=True)
