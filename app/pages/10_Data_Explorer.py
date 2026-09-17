"""
FreightIQ Streamlit Page 5: Data Explorer
"""

import os
import sys

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Data Explorer — FreightIQ", page_icon=None, layout="wide")

from app.components.helpers import (
    inject_custom_css,
    render_top_shell,
    render_sidebar_status,
    render_disclaimer,
    get_cached_processed_data,
    format_inr,
    usd_to_inr
)
from app.components.cards import render_compact_kpi_card
from app.components.charts import apply_industrial_theme
from backend.data_loader import validate_user_csv

inject_custom_css()
render_sidebar_status()
render_top_shell(active_page_name="Data Explorer")

df = get_cached_processed_data()

# Header
st.markdown("""
    <div style="margin-bottom: 18px;">
        <div style="font-size: 1.6rem; font-weight: 700; color: #E9EEF4;">Data Explorer</div>
        <div style="color: #71808F; font-size: 0.85rem;">Prototype modelling dataset and data-quality review</div>
    </div>
""", unsafe_allow_html=True)

# Top Metrics Row
d1, d2, d3, d4 = st.columns(4)
with d1:
    render_compact_kpi_card("OBSERVATIONS", f"{len(df):,}", "Daily time series records")
with d2:
    render_compact_kpi_card("FEATURES", f"{len(df.columns)}", "Engineered parameters")
with d3:
    render_compact_kpi_card("START DATE", df["date"].min().strftime("%d-%b-%Y"), "Earliest observation")
with d4:
    render_compact_kpi_card("END DATE", df["date"].max().strftime("%d-%b-%Y"), "Latest observation")

st.markdown("<br>", unsafe_allow_html=True)

# Tabs without emojis
tab_data, tab_corr, tab_quality, tab_upload = st.tabs([
    "Dataset",
    "Correlation",
    "Quality",
    "Upload"
])

with tab_data:
    st.markdown("### Modelling Dataset")
    
    col_dl1, col_dl2 = st.columns([3, 1])
    with col_dl2:
        csv_bytes = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Processed CSV",
            data=csv_bytes,
            file_name="FreightIQ_modelling_dataset.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Format presentation dataframe with Indian dates & converted INR rates
    display_df = df.copy()
    display_df["Date"] = display_df["date"].dt.strftime("%d-%b-%Y")
    display_df["Freight Rate (₹/t)"] = display_df["freight_rate"].apply(lambda x: round(usd_to_inr(x), 0))
    display_df["Iron Ore (₹/t)"] = display_df["iron_ore_price"].apply(lambda x: round(usd_to_inr(x), 0))
    display_df["Coking Coal (₹/t)"] = display_df["coking_coal_price"].apply(lambda x: round(usd_to_inr(x), 0))

    cols_order = [
        "Date", "Freight Rate (₹/t)", "bdi", "capesize_index", "panamax_index",
        "Iron Ore (₹/t)", "Coking Coal (₹/t)", "port_congestion_score",
        "avg_waiting_hours", "vessel_availability_count", "weather_risk_score", "event_risk_score"
    ]
    existing_cols = [c for c in cols_order if c in display_df.columns]

    st.dataframe(display_df[existing_cols], use_container_width=True)

with tab_corr:
    st.markdown("### Feature Correlation Matrix")
    
    numeric_cols = [c for c in [
        "freight_rate", "bdi", "capesize_index", "panamax_index",
        "iron_ore_price", "coking_coal_price", "port_congestion_score",
        "avg_waiting_hours", "vessel_availability_count", "weather_risk_score", "event_risk_score"
    ] if c in df.columns]

    if len(numeric_cols) > 1:
        corr = df[numeric_cols].corr()
        fig_corr = px.imshow(
            corr,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="Blues",
            title="Pearson Feature Correlation Matrix"
        )
        apply_industrial_theme(fig_corr, height=450)
        st.plotly_chart(fig_corr, use_container_width=True)

with tab_quality:
    st.markdown("### Missing Values Audit")
    
    missing_df = pd.DataFrame({
        "Feature Column": df.columns,
        "Missing Count": df.isnull().sum().values,
        "Missing Percentage (%)": (df.isnull().sum().values / len(df) * 100.0),
        "Data Type": [str(df[c].dtype) for c in df.columns]
    })
    st.dataframe(missing_df, use_container_width=True)

with tab_upload:
    st.markdown("### Upload Custom Dataset")
    st.markdown("Upload custom CSV observations to replace synthetic demo data. Schema validation checks required columns automatically.")

    uploaded_file = st.file_uploader("Upload CSV Dataset", type=["csv"])

    if uploaded_file is not None:
        try:
            user_raw_df = pd.read_csv(uploaded_file)
            is_valid, missing_cols, user_clean_df = validate_user_csv(user_raw_df)

            if is_valid:
                st.success(f"CSV uploaded successfully. All required columns detected ({len(user_clean_df)} rows).")
            else:
                st.warning(f"Missing expected columns: {missing_cols}. Missing fields imputed with defaults for modelling compatibility.")

            st.dataframe(user_clean_df.head(10), use_container_width=True)
        except Exception as e:
            st.error(f"Failed to parse CSV file: {e}")

render_disclaimer()
