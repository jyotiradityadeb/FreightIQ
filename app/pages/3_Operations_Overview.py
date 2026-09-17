"""
FreightIQ Streamlit Page 2 — Operations Overview
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

st.set_page_config(
    page_title="FreightIQ — Operations Overview",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

from app.components.helpers import (
    inject_custom_css,
    render_top_shell,
    render_sidebar_status,
    render_disclaimer,
    get_cached_processed_data,
    format_inr,
    usd_to_inr,
    format_hours
)
from app.components.cards import (
    render_compact_kpi_card,
    render_charter_recommendation_panel,
    render_forecast_interpretation_box
)
from app.components.charts import (
    plot_freight_trend,
    plot_forecast_with_ci
)
from backend.forecasting import generate_freight_forecast
from backend.optimizer import optimize_charter_timing
from backend.vessel_forecast import forecast_vessel_availability

# 1. Inject Custom Industrial CSS
inject_custom_css()

# 2. Render Sidebar System Status
render_sidebar_status()

# 3. Top Shell Header
render_top_shell(active_page_name="Operations Overview")

# 4. Page Title Header
st.markdown("### Operations Overview")
st.caption("Freight market outlook and current charter recommendation")

# 5. Load Data & Engine Outputs
try:
    df = get_cached_processed_data()
    latest_row = df.iloc[-1]

    # Generate 14-Day Forecast
    fc_res = generate_freight_forecast(df, horizon=14, selected_model="Auto")
    fc_df = fc_res["forecast_df"]
    expected_14_rate_usd = fc_df["predicted_freight_rate"].iloc[-1]
    expected_14_rate_inr = usd_to_inr(expected_14_rate_usd)
    latest_rate_inr = usd_to_inr(latest_row["freight_rate"])

    pct_change_14 = ((expected_14_rate_usd - latest_row["freight_rate"]) / latest_row["freight_rate"]) * 100.0

    # Vessel Forecast
    vessel_res = forecast_vessel_availability(df, horizon=14)

    # 6. TOP KPI ROW (4 Compact Cards)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        freight_7d_avg_usd = df["freight_rate"].tail(7).mean()
        diff_7d_pct = ((latest_row["freight_rate"] - freight_7d_avg_usd) / freight_7d_avg_usd) * 100.0
        symbol = "↓" if diff_7d_pct < 0 else "↑"
        render_compact_kpi_card(
            label="FREIGHT RATE",
            value_str=f"{format_inr(latest_rate_inr)} / tonne",
            subtext_str=f"{symbol} {abs(diff_7d_pct):.1f}% vs 7-day average",
            subtext_color="#2E8B68" if diff_7d_pct <= 0 else "#C98226"
        )

    with col2:
        fc_trend_str = "Softening" if pct_change_14 < 0 else "Rising"
        render_compact_kpi_card(
            label="14-DAY OUTLOOK",
            value_str=f"{pct_change_14:+.1f}%",
            subtext_str=f"{fc_trend_str} ({format_inr(expected_14_rate_inr)}/t)",
            subtext_color="#2E8B68" if pct_change_14 <= 0 else "#C98226"
        )

    with col3:
        render_compact_kpi_card(
            label="VESSEL AVAILABILITY",
            value_str=f"{latest_row['vessel_availability_count']} vessels",
            subtext_str=f"Supply Trend: {vessel_res['trend']}",
            subtext_color="#2E8B68"
        )

    with col4:
        cong_score = latest_row['port_congestion_score']
        cong_status = "Elevated" if cong_score > 60 else "Manageable"
        render_compact_kpi_card(
            label="PORT WAITING TIME",
            value_str=format_hours(latest_row['avg_waiting_hours']),
            subtext_str=f"Status: {cong_status} ({cong_score:.0f}/100)",
            subtext_color="#C98226" if cong_score > 60 else "#A2ADBA"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 7. SECOND ROW: LEFT (65%) Freight Market Outlook, RIGHT (35%) Charter Recommendation
    c_chart, c_rec = st.columns([0.65, 0.35])

    with c_chart:
        st.markdown("### Freight Market Outlook")
        fig_fc = plot_forecast_with_ci(
            df,
            fc_df,
            title=f"Freight Rate Forecast ({fc_res['selected_model']})",
            lookback_days=90
        )
        st.plotly_chart(fig_fc, use_container_width=True)

        render_forecast_interpretation_box(
            title="Forecast Interpretation",
            text=f"Freight rates are projected to {fc_trend_str.lower()} over the next 14 days based on {fc_res['selected_model']} model analysis (demo-series MAE: {format_inr(usd_to_inr(fc_res['metrics']['MAE'])) + '/tonne' if fc_res['metrics'].get('MAE') is not None else 'unavailable'})."
        )

    with c_rec:
        st.markdown("### Charter Recommendation")
        
        opt_res = optimize_charter_timing(
            forecast_df=fc_df,
            cargo_type="Coking Coal",
            quantity_tonnes=75000.0,
            origin="Australia",
            destination="Paradip",
            vessel_class="Auto"
        )

        if opt_res["success"]:
            render_charter_recommendation_panel(opt_res["recommendation"])

except Exception as e:
    st.error(f"Error loading Operations Overview: {e}")

# 8. Disclaimer
render_disclaimer()
