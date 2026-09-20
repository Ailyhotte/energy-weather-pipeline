# src/dashboard/app.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import text

from src.config import engine

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Météo & Énergie",
    page_icon="⚡",
    layout="wide",
)


@st.cache_data(ttl=600)
def load_data():
    """Charge les données du datamart en joignant les tables de faits et dimensions."""
    query = """
    SELECT 
        d.full_date,
        f.hour,
        r.region_name,
        f.temp_mean_celsius,
        f.precipitation_mm,
        f.wind_speed_kmh,
        f.consumption_mw
    FROM analytics.fact_weather_energy f
    JOIN analytics.dim_region r ON f.region_id = r.region_id
    JOIN analytics.dim_date d ON f.date_key = d.date_key
    ORDER BY d.full_date, f.hour;
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), con=conn)

    # Reconstitution d'un datetime complet pour les axes de temps
    df["datetime"] = pd.to_datetime(df["full_date"]) + pd.to_timedelta(
        df["hour"], unit="h"
    )
    return df


# --- CHARGEMENT DES DONNÉES ---
try:
    df_raw = load_data()
except Exception as e:
    st.error(f"❌ Erreur lors de la connexion à la base de données : {e}")
    st.stop()

# --- BARRE LATÉRALE : FILTRES ---
st.sidebar.header("🔍 Filtres")

# Filtre Région
regions = ["Toutes"] + list(df_raw["region_name"].unique())
selected_region = st.sidebar.selectbox("Sélectionner une région", regions)

# Filtre Dates
min_date = df_raw["full_date"].min()
max_date = df_raw["full_date"].max()

date_range = st.sidebar.date_input(
    "Période",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# Application des filtres
df_filtered = df_raw.copy()

if selected_region != "Toutes":
    df_filtered = df_filtered[df_filtered["region_name"] == selected_region]
else:
    df_filtered = df_filtered.groupby(
        ["full_date", "hour", "datetime"], as_index=False
    ).agg(
        {
            "temp_mean_celsius": "mean",
            "precipitation_mm": "mean",
            "wind_speed_kmh": "mean",
            "consumption_mw": "mean",
        }
    )
    df_filtered["region_name"] = "Moyenne Nationale"

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df_filtered[
        (df_filtered["full_date"] >= start_date)
        & (df_filtered["full_date"] <= end_date)
    ]

# --- EN-TÊTE ET KPI ---
st.title("Analyse données Météo & Consommation Électrique")
st.markdown(
    "Visualisation croisée des données météorologiques et de la consommation d'électricité régionale."
)

col1, col2, col3, col4 = st.columns(4)

avg_temp = df_filtered["temp_mean_celsius"].mean()
total_conso = (
    df_raw["consumption_mw"].sum()
    if selected_region == "Toutes"
    else df_filtered["consumption_mw"].sum()
)
max_conso = (
    df_raw["consumption_mw"].max()
    if selected_region == "Toutes"
    else df_filtered["consumption_mw"].max()
)
records_count = len(df_raw) if selected_region == "Toutes" else len(df_filtered)

col1.metric("Température Moyenne", f"{avg_temp:.1f} °C")
col2.metric("Consommation Totale", f"{total_conso / 1000:.1f} GWh")
col3.metric("Pic de Consommation", f"{max_conso:.0f} MW")
col4.metric("Points de données", f"{records_count:,}")

st.divider()

# --- GRAPHIQUES ---
tab1, tab2 = st.tabs(["Évolution Temporelle", "Thermo-sensibilité"])

with tab1:
    st.subheader("Consommation et Température au fil du temps")

    # Double axe Y : Consommation (MW) et Température (°C)
    fig_time = go.Figure()

    fig_time.add_trace(
        go.Scatter(
            x=df_filtered["datetime"],
            y=df_filtered["consumption_mw"],
            name="Consommation (MW)",
            line=dict(color="#1f77b4", width=2),
        )
    )

    fig_time.add_trace(
        go.Scatter(
            x=df_filtered["datetime"],
            y=df_filtered["temp_mean_celsius"],
            name="Température (°C)",
            line=dict(color="#ff7f0e", width=2, dash="dot"),
            yaxis="y2",
        )
    )

    fig_time.update_layout(
        xaxis=dict(title="Date & Heure"),
        yaxis=dict(title=dict(text="Consommation (MW)", font=dict(color="#1f77b4"))),
        yaxis2=dict(
            title=dict(text="Température (°C)", font=dict(color="#ff7f0e")),
            overlaying="y",
            side="right",
        ),
        legend=dict(x=0.01, y=0.99),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
    )

    st.plotly_chart(fig_time, width="stretch")

with tab2:
    st.subheader("Impact de la température sur la consommation")

    fig_scatter = px.scatter(
        df_filtered,
        x="temp_mean_celsius",
        y="consumption_mw",
        color="region_name" if selected_region == "Toutes" else "hour",
        labels={
            "temp_mean_celsius": "Température (°C)",
            "consumption_mw": "Consommation (MW)",
            "region_name": "Région",
            "hour": "Heure de la journée",
        },
        title="Relation Température / Consommation",
        trendline="ols",  # Ligne de tendance linéaire
    )

    st.plotly_chart(fig_scatter, width="stretch")
