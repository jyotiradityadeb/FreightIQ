"""
FreightIQ Streamlit Page 2: Freight Rate Forecasting
"""

import os
import sys

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Forecasting — FreightIQ", page_icon=None, layout="wide")

from app.components.helpers import (
    inject_custom_css,
    render_top_shell,
    render_sidebar_status,
    render_disclaimer,
    get_cached_processed_data,
    format_inr,
    usd_to_inr
)
from app.components.cards import render_forecast_interpretation_box
from app.components.charts import plot_forecast_with_ci
from backend.forecasting import generate_freight_forecast, HAS_PROPHET

inject_custom_css()
render_sidebar_status()
render_top_shell(active_page_name="Forecasting")

df = get_cached_processed_data()

# Header
st.markdown("### Freight Rate Forecasting")
st.caption("Short-horizon freight outlook for charter planning [D] Demo Feed")

# Configuration Row
c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    model_options = ["Auto", "SARIMA", "Naive Baseline"]
    if HAS_PROPHET:
        model_options.append("Prophet")
    selected_model = st.selectbox("Forecast Model", model_options, index=0)

with c2:
    horizon = st.select_slider("Forecast Horizon", options=[7, 14, 30], value=14)

with c3:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    run_fc_btn = st.button("Run Forecast", use_container_width=True)

st.markdown("---")

# Generate Forecast
fc_res = generate_freight_forecast(df, horizon=horizon, selected_model=selected_model)
fc_df = fc_res["forecast_df"]
metrics = fc_res["metrics"]

mae_inr = usd_to_inr(metrics["MAE"])
rmse_inr = usd_to_inr(metrics["RMSE"])

# Layout: Left Main Chart, Right Validation Metrics
col_chart, col_metrics = st.columns([0.65, 0.35])

with col_chart:
    st.markdown("### Freight Rate Forecast")
    fig_fc = plot_forecast_with_ci(
        df,
        fc_df,
        title=f"Forecast Horizon: {horizon} Days ({fc_res['selected_model']})",
        lookback_days=90
    )
    st.plotly_chart(fig_fc, use_container_width=True)

    render_forecast_interpretation_box(
        title="Forecast Interpretation",
        text=f"Freight rates are expected to soften moderately over the next {horizon} days, with uncertainty increasing toward the end of the forecast horizon. Selected model ({fc_res['selected_model']}) achieved lowest validation MAE of {format_inr(mae_inr)}/tonne."
    )

with col_metrics:
    st.markdown("### Validation Metrics")
    
    st.markdown(f"""
        <div style="background-color: #151E28; border: 1px solid #293541; border-radius: 6px; padding: 14px 18px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #293541; padding-bottom: 8px;">
                <span style="color: #71808F; font-size: 0.8rem;">Selected Algorithm</span>
                <span style="color: #4F86C6; font-weight: 600; font-size: 0.85rem;">{fc_res['selected_model']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #293541; padding-bottom: 8px;">
                <span style="color: #71808F; font-size: 0.8rem;">Mean Absolute Error (MAE)</span>
                <span style="color: #E9EEF4; font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 0.85rem;">{format_inr(mae_inr)} / tonne</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #293541; padding-bottom: 8px;">
                <span style="color: #71808F; font-size: 0.8rem;">Root Mean Squared Error (RMSE)</span>
                <span style="color: #E9EEF4; font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 0.85rem;">{format_inr(rmse_inr)} / tonne</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #71808F; font-size: 0.8rem;">Mean Absolute Pct Error (MAPE)</span>
                <span style="color: #2E8B68; font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 0.85rem;">{metrics['MAPE']:.2f}%</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### Model Comparison")
    
    comp_rows = []
    for m in fc_res["comparison_table"]:
        m_mae = usd_to_inr(m["MAE"])
        m_rmse = usd_to_inr(m["RMSE"])
        comp_rows.append({
            "Model": m["Model"],
            "MAE (₹/t)": f"₹{m_mae:.0f}",
            "RMSE (₹/t)": f"₹{m_rmse:.0f}",
            "MAPE": f"{m['MAPE (%)']:.2f}%",
            "Status": "Selected" if m["Selected"] == "Yes" else "Evaluated"
        })

    st.dataframe(comp_rows, use_container_width=True)

render_disclaimer()
