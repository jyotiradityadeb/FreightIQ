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

st.set_page_config(page_title="FreightIQ — Market Intelligence", page_icon=None, layout="wide")

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
from app.components.charts import (
    plot_freight_trend,
    plot_commodity_signals,
    plot_congestion_and_vessels
)

inject_custom_css()
render_sidebar_status()
render_top_shell(active_page_name="Market Intelligence")

df = get_cached_processed_data()

# Date Window Filter in Sidebar
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
st.markdown("<h1 style='margin-bottom: 2px;'>Market Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #6B7280; font-size: 0.95rem; margin-bottom: 20px;'>Financial market indicators, commodity price signals, and port congestion metrics.</p>", unsafe_allow_html=True)

# SMALL SUMMARY STRIP (Clean SaaS Bordered Container)
ore_inr = usd_to_inr(latest['iron_ore_price'])
coal_inr = usd_to_inr(latest['coking_coal_price'])

with st.container(border=True):
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        st.caption("BDI / FREIGHT")
        st.markdown(f"**{latest['bdi']:,.0f} BDI**")
        st.caption(f"{format_inr(usd_to_inr(latest['freight_rate']))}/t")
    with s2:
        st.caption("COKING COAL")
        st.markdown(f"**{format_inr(coal_inr)} / t**")
        st.caption("Premium Hard Coking")
    with s3:
        st.caption("IRON ORE")
        st.markdown(f"**{format_inr(ore_inr)} / t**")
        st.caption("62% Fe CFR China")
    with s4:
        st.caption("PARADIP CONGESTION")
        st.markdown(f"**{latest['port_congestion_score']:.0f} / 100**")
        st.caption(f"{latest['avg_waiting_hours']:.0f}h avg wait")
    with s5:
        st.caption("AVAILABLE VESSELS")
        st.markdown(f"**{latest['vessel_availability_count']} Vessels**")
        st.caption("Open East Coast AU")

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# MAIN MARKET CHART
with st.container(border=True):
    st.markdown("### Freight Market Benchmark & Commodity Signals")
    fig_f = plot_freight_trend(filtered_df, title="")
    st.plotly_chart(fig_f, use_container_width=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# TWO-COLUMN LAYOUT: SIGNALS vs MARKET EVENTS
c_signals, c_events = st.columns([1, 1])

with c_signals:
    with st.container(border=True):
        st.markdown("### Market Signals")
        st.caption("Key driver metrics and status indicators")
        
        signals_data = [
            {"Signal": "Baltic Panamax Index", "Current Value": f"{latest['panamax_index']:,.0f}", "7D Trend": "Softening (-1.2%)", "Status": "Normal"},
            {"Signal": "Capesize Index", "Current Value": f"{latest['capesize_index']:,.0f}", "7D Trend": "Rising (+3.4%)", "Status": "Watch"},
            {"Signal": "Coking Coal CFR India", "Current Value": format_inr(coal_inr), "7D Trend": "Flat (0.0%)", "Status": "Stable"},
            {"Signal": "Iron Ore Fines 62%", "Current Value": format_inr(ore_inr), "7D Trend": "Softening (-0.8%)", "Status": "Stable"},
            {"Signal": "Bunker VLSFO Singapore", "Current Value": "₹54,200 / t", "7D Trend": "Softening (-0.5%)", "Status": "Favorable"}
        ]
        st.dataframe(pd.DataFrame(signals_data), use_container_width=True, hide_index=True)

with c_events:
    with st.container(border=True):
        st.markdown("### Market Events & Operational News")
        st.caption("Recent market developments impacting East Coast freight")

        events = [
            {"Date": "17 Sep 2026", "Event": "Paradip Coal Berth maintenance scheduled for 22-24 Sep; queue expected to rise to 48h."},
            {"Date": "15 Sep 2026", "Event": "Queensland rail haulage bottlenecks resolved; vessel loading rates back to 4,200 t/h."},
            {"Date": "12 Sep 2026", "Event": "Singapore VLSFO bunker prices drop ₹450/t following lower crude oil futures."},
            {"Date": "08 Sep 2026", "Event": "Visakhapatnam inner harbor dredging complete; draft constraint relaxed to 16.5m."}
        ]
        
        for ev in events:
            st.markdown(f"""
                <div style="border-bottom: 1px solid #F1F5F9; padding-bottom: 8px; margin-bottom: 8px;">
                    <div style="font-size: 0.75rem; color: #6B7280; font-weight: 600;">{ev['Date']}</div>
                    <div style="font-size: 0.875rem; color: #111827;">{ev['Event']}</div>
                </div>
            """, unsafe_allow_html=True)

render_disclaimer()

