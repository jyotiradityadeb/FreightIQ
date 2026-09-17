"""
FreightIQ Streamlit Page 1: Market Intelligence
"""

import os
import sys

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Market Intelligence — FreightIQ", page_icon=None, layout="wide")

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
from app.components.cards import render_compact_kpi_card
from app.components.charts import (
    plot_freight_trend,
    plot_commodity_signals,
    plot_congestion_and_vessels
)

inject_custom_css()
render_sidebar_status()
render_top_shell(active_page_name="Market Intelligence")

df = get_cached_processed_data()

# Date Window Filter
st.sidebar.header("Filter Date Range")
min_d = df["date"].min().to_pydatetime()
max_d = df["date"].max().to_pydatetime()

selected_dates = st.sidebar.date_input(
    "Date Window",
    value=[min_d, max_d],
    min_value=min_d,
    max_value=max_d
)

if isinstance(selected_dates, list) and len(selected_dates) == 2:
    start_dt, end_dt = selected_dates
    filtered_df = df[(df["date"] >= pd.to_datetime(start_dt)) & (df["date"] <= pd.to_datetime(end_dt))]
else:
    filtered_df = df

latest = filtered_df.iloc[-1]

# Header
st.markdown("### Market Intelligence")
st.caption("Dry-bulk freight, commodity and East Coast port indicators [D] Demo Data")

# TOP SUMMARY STRIP
st.markdown("""
    <div style="background-color: #151E28; border: 1px solid #293541; border-radius: 6px; padding: 12px 18px; margin-bottom: 20px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; font-size: 0.82rem;">
        <div>
            <span style="color: #71808F;">Market Regime:</span> <strong style="color: #2E8B68; margin-left: 4px;">Moderately Bullish</strong>
        </div>
        <div>
            <span style="color: #71808F;">Freight Momentum:</span> <strong style="color: #C98226; margin-left: 4px;">Softening</strong>
        </div>
        <div>
            <span style="color: #71808F;">Port Risk:</span> <strong style="color: #C98226; margin-left: 4px;">Elevated</strong>
        </div>
        <div>
            <span style="color: #71808F;">Vessel Supply:</span> <strong style="color: #E9EEF4; margin-left: 4px;">Stable</strong>
        </div>
    </div>
""", unsafe_allow_html=True)

# KPI STRIP (5 Cards)
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    render_compact_kpi_card("BALTIC DRY INDEX", f"{latest['bdi']:,.0f}", "BDI Benchmark")
with c2:
    render_compact_kpi_card("CAPESIZE INDEX", f"{latest['capesize_index']:,.0f}", "Capesize 180k Index")
with c3:
    render_compact_kpi_card("PANAMAX INDEX", f"{latest['panamax_index']:,.0f}", "Panamax 75k Index")
with c4:
    ore_inr = usd_to_inr(latest['iron_ore_price'])
    render_compact_kpi_card("IRON ORE", f"{format_inr(ore_inr)} / t", "Demo converted to INR")
with c5:
    coal_inr = usd_to_inr(latest['coking_coal_price'])
    render_compact_kpi_card("COKING COAL", f"{format_inr(coal_inr)} / t", "Demo converted to INR")

st.markdown("<br>", unsafe_allow_html=True)

# CHARTS ROW 1: Freight & BDI, Commodity Price Signals
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### Freight Rate & Baltic Dry Index")
    fig_f = plot_freight_trend(filtered_df, title="Freight Rate (₹ / tonne)")
    st.plotly_chart(fig_f, use_container_width=True)

with col_right:
    st.markdown("### Commodity Price Signals")
    fig_comm = plot_commodity_signals(filtered_df)
    st.plotly_chart(fig_comm, use_container_width=True)

st.markdown("---")

# CHART / TABLE ROW 2: Port Congestion Comparison & Regional Vessel Supply
p_left, p_right = st.columns(2)

with p_left:
    st.markdown("### Port Congestion Comparison")
    
    port_table_data = [
        {"Port": "Paradip", "Congestion": "64 / 100", "Waiting Time": "39 h", "Trend": "Improving", "Risk": "Moderate"},
        {"Port": "Visakhapatnam", "Congestion": "48 / 100", "Waiting Time": "26 h", "Trend": "Stable", "Risk": "Low"},
        {"Port": "Haldia", "Congestion": "71 / 100", "Waiting Time": "44 h", "Trend": "Worsening", "Risk": "High"}
    ]
    
    st.dataframe(port_table_data, use_container_width=True)

with p_right:
    st.markdown("### Regional Vessel Availability")
    fig_vessel = plot_congestion_and_vessels(filtered_df)
    st.plotly_chart(fig_vessel, use_container_width=True)

render_disclaimer()
