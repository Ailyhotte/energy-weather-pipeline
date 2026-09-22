# src/dashboard/app.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats
from sqlalchemy import text

from src.config import engine

# Page configuration
st.set_page_config(
    page_title="Weather & Energy Dashboard",
    layout="wide",
)


@st.cache_data(ttl=600)
def load_data():
    """Load datamart data by joining fact and dimension tables."""
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

    # Build a complete datetime value for time axes
    df["datetime"] = pd.to_datetime(df["full_date"]) + pd.to_timedelta(
        df["hour"], unit="h"
    )
    return df


# --- DATA LOADING ---
try:
    df_raw = load_data()
except Exception as e:
    st.error(f"❌ Error connecting to the database: {e}")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filters")

# Region filter
regions = ["All"] + list(df_raw["region_name"].unique())
selected_region = st.sidebar.selectbox("Select a region", regions)

# Date filter
min_date = df_raw["full_date"].min()
max_date = df_raw["full_date"].max()

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# Apply filters
df_filtered = df_raw.copy()

if selected_region != "All":
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
    df_filtered["region_name"] = "National Average"

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df_filtered[
        (df_filtered["full_date"] >= start_date)
        & (df_filtered["full_date"] <= end_date)
    ]

# --- HEADER AND KPIs ---
st.title("Weather & Energy data Analysis")
st.markdown("Explore weather data alongside regional electricity consumption.")

col1, col2, col3, col4 = st.columns(4)

avg_temp = df_filtered["temp_mean_celsius"].mean()
total_conso = (
    df_raw["consumption_mw"].sum()
    if selected_region == "All"
    else df_filtered["consumption_mw"].sum()
)
max_conso = (
    df_raw["consumption_mw"].max()
    if selected_region == "All"
    else df_filtered["consumption_mw"].max()
)
records_count = len(df_raw) if selected_region == "All" else len(df_filtered)

col1.metric("Average Temperature", f"{avg_temp:.1f} °C")
col2.metric("Total Consumption", f"{total_conso / 1000:.1f} GWh")
col3.metric("Peak Consumption", f"{max_conso:.0f} MW")
col4.metric("Data Points", f"{records_count:,}")

st.divider()

# --- CHARTS ---
tab1 = st.tabs(["Time Evolution"])[0]

with tab1:
    st.subheader("Consumption and Temperature Over Time")

    # Dual Y-axis: consumption (MW) and temperature (°C)
    fig_time = go.Figure()

    fig_time.add_trace(
        go.Scatter(
            x=df_filtered["datetime"],
            y=df_filtered["consumption_mw"],
            name="Consumption (MW)",
            line=dict(color="#1f77b4", width=2),
        )
    )

    fig_time.add_trace(
        go.Scatter(
            x=df_filtered["datetime"],
            y=df_filtered["temp_mean_celsius"],
            name="Temperature (°C)",
            line=dict(color="#ff7f0e", width=2, dash="dot"),
            yaxis="y2",
        )
    )

    fig_time.update_layout(
        xaxis=dict(title="Date & Time"),
        yaxis=dict(title=dict(text="Consumption (MW)", font=dict(color="#1f77b4"))),
        yaxis2=dict(
            title=dict(text="Temperature (°C)", font=dict(color="#ff7f0e")),
            overlaying="y",
            side="right",
        ),
        legend=dict(x=0.01, y=0.99),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
    )

    st.plotly_chart(fig_time, width="stretch")

    # --- CORRELATION ANALYSIS ---
    st.markdown("### Temperature vs. Consumption Correlation")

    # Drop missing values in target columns to prevent SciPy errors
    df_corr = df_filtered.dropna(subset=["temp_mean_celsius", "consumption_mw"])

    # Ensure we have enough data points and variation to compute correlation
    if (
        len(df_corr) >= 3
        and df_corr["temp_mean_celsius"].std() > 0
        and df_corr["consumption_mw"].std() > 0
    ):
        pearson_r, pearson_p = stats.pearsonr(
            df_corr["temp_mean_celsius"], df_corr["consumption_mw"]
        )
        spearman_r, spearman_p = stats.spearmanr(
            df_corr["temp_mean_celsius"], df_corr["consumption_mw"]
        )

        corr_col1, corr_col2, corr_col3 = st.columns(3)

        # Interpret Pearson coefficient
        p_strength = (
            "Strong Negative"
            if pearson_r < -0.7  # type: ignore
            else (
                "Moderate Negative"
                if pearson_r < -0.3  # type: ignore
                else (
                    "Weak / None"
                    if -0.3 <= pearson_r <= 0.3  # type: ignore
                    else "Moderate Positive" if pearson_r < 0.7 else "Strong Positive"  # type: ignore
                )
            )
        )
        corr_col1.metric(
            label="Pearson Correlation (Linear)",
            value=f"{pearson_r:.2f}",
            delta=p_strength,
            delta_color="off",
            help="Measures linear relationship (-1 to +1).",
        )

        # Interpret Spearman coefficient
        s_strength = (
            "Strong Monotone"
            if abs(spearman_r) > 0.7  # type: ignore
            else "Moderate Monotone" if abs(spearman_r) > 0.3 else "Weak / None"  # type: ignore
        )
        corr_col2.metric(
            label="Spearman Correlation (Rank)",
            value=f"{spearman_r:.2f}",
            delta=s_strength,
            delta_color="off",
            help="Measures monotonic relationship (-1 to +1), robust to non-linear trends.",
        )

        # Statistical significance badge
        p_val_text = (
            "p < 0.001 (Statistically Significant)"
            if pearson_p < 0.001  # type: ignore
            else f"p = {pearson_p:.4f}"
        )
        corr_col3.metric(
            label="Statistical Significance",
            value="Valid" if pearson_p < 0.05 else "Not Significant",  # type: ignore
            delta=p_val_text,
            delta_color="normal" if pearson_p < 0.05 else "inverse",  # type: ignore
            help="p-value < 0.05 indicates the correlation is statistically meaningful and not due to random noise.",
        )

    else:
        st.warning(
            "⚠️ Not enough data points or variance in the selected range to calculate correlation."
        )

st.divider()

## --- Footer ---

with st.bottom:
    st.caption("Made with Streamlit by Elliot.")
    st.caption(
        "Data sources: Open-Meteo @ https://open-meteo.com & ODRE @ https://odre.opendatasoft.com/explore/dataset/eco2mix-regional-tr."
    )
