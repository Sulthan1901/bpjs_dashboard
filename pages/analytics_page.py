import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from services.company_service import (
    get_companies_by_kabupaten, get_companies_by_pembina,
    get_tk_distribution, get_all_companies, STATUS_OPTIONS
)


def render():
    st.title("📊 Analytics & Visualisasi")
    st.markdown("---")

    df = get_all_companies()
    if df.empty:
        st.info("Belum ada data perusahaan untuk dianalisis.")
        return

    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Per Kabupaten", "👤 Per Pembina", "👷 Tenaga Kerja", "📈 Tren Status"
    ])

    with tab1:
        st.subheader("Distribusi Perusahaan per Kabupaten")
        kab_df = get_companies_by_kabupaten()
        if not kab_df.empty:
            fig = px.bar(
                kab_df, x="jumlah", y="kabupaten",
                orientation="h",
                color="jumlah",
                color_continuous_scale="Blues",
                text="jumlah",
                labels={"jumlah": "Jumlah Perusahaan", "kabupaten": "Kabupaten"}
            )
            fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            # Status breakdown per kabupaten
            st.subheader("Status per Kabupaten")
            kab_status = df.groupby(["kabupaten", "status"]).size().reset_index(name="jumlah")
            fig2 = px.bar(
                kab_status, x="kabupaten", y="jumlah", color="status",
                color_discrete_map={
                    "Sudah Ada Balasan": "#2ecc71",
                    "Sudah Dihubungi Belum Balas": "#f39c12",
                    "Nomor Tidak Bisa Dihubungi": "#e74c3c",
                    "Belum Dihubungi": "#95a5a6"
                },
                labels={"jumlah": "Jumlah", "kabupaten": "Kabupaten", "status": "Status"}
            )
            fig2.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.subheader("Distribusi Perusahaan per Pembina")
        pem_df = get_companies_by_pembina()
        if not pem_df.empty:
            fig = px.bar(
                pem_df.head(20), x="jumlah", y="nama_pembina",
                orientation="h",
                color="jumlah",
                color_continuous_scale="Greens",
                text="jumlah",
                labels={"jumlah": "Jumlah Perusahaan", "nama_pembina": "Nama Pembina"}
            )
            fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            # Status breakdown per pembina
            st.subheader("Progress Status per Pembina")
            pem_status = df.groupby(["nama_pembina", "status"]).size().reset_index(name="jumlah")
            fig2 = px.bar(
                pem_status, x="nama_pembina", y="jumlah", color="status",
                barmode="stack",
                color_discrete_map={
                    "Sudah Ada Balasan": "#2ecc71",
                    "Sudah Dihubungi Belum Balas": "#f39c12",
                    "Nomor Tidak Bisa Dihubungi": "#e74c3c",
                    "Belum Dihubungi": "#95a5a6"
                }
            )
            fig2.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.subheader("Distribusi Tenaga Kerja")
        tk_df = get_tk_distribution()
        if not tk_df.empty:
            fig = px.scatter(
                tk_df,
                x="total_tk",
                y="tk_dibawah_umk",
                hover_name="nama_perusahaan",
                size="total_tk",
                color="tk_dibawah_umk",
                color_continuous_scale="Reds",
                labels={
                    "total_tk": "Total TK",
                    "tk_dibawah_umk": "TK di Bawah UMK"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

            # Percentage below UMK
            df_tk = df[df["total_tk"] > 0].copy()
            df_tk["pct_bawah_umk"] = (df_tk["tk_dibawah_umk"] / df_tk["total_tk"] * 100).round(1)
            high_risk = df_tk[df_tk["pct_bawah_umk"] > 50].sort_values("pct_bawah_umk", ascending=False).head(10)

            if not high_risk.empty:
                st.subheader("⚠️ Perusahaan dengan TK Bawah UMK > 50%")
                st.dataframe(
                    high_risk[["nama_perusahaan", "kabupaten", "total_tk", "tk_dibawah_umk", "pct_bawah_umk"]],
                    use_container_width=True, hide_index=True
                )

    with tab4:
        st.subheader("Ringkasan Pencapaian Monitoring")
        total = len(df)
        selesai = len(df[df["status"] == "Sudah Ada Balasan"])
        progress_pct = (selesai / total * 100) if total > 0 else 0

        st.markdown(f"### Overall Progress: {progress_pct:.1f}%")
        st.progress(progress_pct / 100)

        # Funnel chart
        funnel_data = [
            {"Stage": "Total Perusahaan", "Count": total},
            {"Stage": "Sudah Dihubungi", "Count": len(df[df["status"] != "Belum Dihubungi"])},
            {"Stage": "Ada Respons", "Count": len(df[df["status"].isin(["Sudah Ada Balasan", "Sudah Dihubungi Belum Balas"])])},
            {"Stage": "Sudah Ada Balasan", "Count": selesai},
        ]
        funnel_df = pd.DataFrame(funnel_data)
        fig = go.Figure(go.Funnel(
            y=funnel_df["Stage"],
            x=funnel_df["Count"],
            textinfo="value+percent initial",
            marker_color=["#3498db", "#f39c12", "#9b59b6", "#2ecc71"]
        ))
        fig.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
