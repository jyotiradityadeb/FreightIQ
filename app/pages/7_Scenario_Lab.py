"""
FreightIQ Streamlit Page 4 — Scenario Lab
Interactive What-If Simulation & Decision Stress Testing
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
import plotly.graph_objects as go
from datetime import datetime, timedelta

from app.components.helpers import (
    inject_custom_css,
    render_top_shell,
    render_sidebar_status,
    render_disclaimer,
    get_cached_processed_data,
    usd_to_inr,
    format_inr
)
from backend.forecasting import generate_freight_forecast
from backend.scenario_engine import ScenarioRequest, ScenarioShock, run_scenario_simulation

st.set_page_config(page_title="FreightIQ — Scenario Lab", page_icon=None, layout="wide")

inject_custom_css()
render_sidebar_status()
render_top_shell(active_page_name="Scenario Lab")


# Header
st.markdown("<h1 style='margin-bottom: 2px;'>Scenario Lab</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #6B7280; font-size: 0.95rem; margin-bottom: 20px;'>Stress-test charter recommendations across simulated freight, congestion, and weather disruptions.</p>", unsafe_allow_html=True)

# Load Processed Dataset & Generate 30-day baseline forecast
try:
    df = get_cached_processed_data()
    fc_res = generate_freight_forecast(df, horizon=30, selected_model="Auto")
    forecast_df = fc_res["forecast_df"]
except Exception as e:
    st.error(f"Error loading forecasting engine for Scenario Lab: {e}")
    st.stop()

# Initialize session state for preset shocks
default_shocks = {
    "freight_shock": 0.0,
    "cong_shock": 0.0,
    "target_port": "Paradip",
    "avail_shock": 0.0,
    "comm_shock": 0.0,
    "weather_risk": "Low",
    "geo_risk": "Normal",
    "dem_shock": 0.0
}
for key, val in default_shocks.items():
    if key not in st.session_state:
        st.session_state[key] = val

# PRESET STRESS SCENARIO BUTTONS (Standard Secondary Action Buttons)
st.markdown("### Presets")
p1, p2, p3, p4, p5, p6 = st.columns(6)
with p1:
    if st.button("East Coast Disruption", use_container_width=True):
        st.session_state["freight_shock"] = 12.0
        st.session_state["cong_shock"] = 55.0
        st.session_state["target_port"] = "Paradip"
        st.session_state["avail_shock"] = -30.0
        st.session_state["weather_risk"] = "High"
        st.session_state["geo_risk"] = "Elevated"
        st.rerun()
with p2:
    if st.button("Freight Rate Spike", use_container_width=True):
        st.session_state["freight_shock"] = 15.0
        st.session_state["cong_shock"] = 0.0
        st.session_state["avail_shock"] = 0.0
        st.session_state["weather_risk"] = "Low"
        st.session_state["geo_risk"] = "Normal"
        st.rerun()
with p3:
    if st.button("Paradip Congestion", use_container_width=True):
        st.session_state["freight_shock"] = 0.0
        st.session_state["cong_shock"] = 50.0
        st.session_state["target_port"] = "Paradip"
        st.rerun()
with p4:
    if st.button("Vessel Shortage", use_container_width=True):
        st.session_state["freight_shock"] = 0.0
        st.session_state["avail_shock"] = -35.0
        st.rerun()
with p5:
    if st.button("Severe Weather Risk", use_container_width=True):
        st.session_state["weather_risk"] = "Severe"
        st.rerun()
with p6:
    if st.button("Market Relief", use_container_width=True):
        st.session_state["freight_shock"] = -10.0
        st.session_state["cong_shock"] = -20.0
        st.session_state["avail_shock"] = 20.0
        st.session_state["weather_risk"] = "Low"
        st.session_state["geo_risk"] = "Normal"
        st.rerun()

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# FORM LAYOUT: SCENARIO INPUTS (LEFT) vs IMPACT PREVIEW (RIGHT)
c_inputs, c_preview = st.columns([1.1, 0.9])

with c_inputs:
    with st.container(border=True):
        st.markdown("### Scenario Inputs")
        st.caption("Adjust disruption parameters to test decision stability")

        freight_shock_val = st.slider("Freight Shock (%)", -20.0, 30.0, float(st.session_state["freight_shock"]), 1.0)
        cong_shock_val = st.slider("Port Congestion Shock (%)", -50.0, 100.0, float(st.session_state["cong_shock"]), 5.0)
        avail_shock_val = st.slider("Vessel Availability Change (%)", -60.0, 50.0, float(st.session_state["avail_shock"]), 5.0)
        
        i1, i2 = st.columns(2)
        with i1:
            weather_val = st.selectbox("Weather Risk", ["Low", "Moderate", "High", "Severe"], index=["Low", "Moderate", "High", "Severe"].index(st.session_state["weather_risk"]))
        with i2:
            target_port_val = st.selectbox("Target Discharge Port", ["Paradip", "Visakhapatnam", "Kolkata/Haldia"], index=0)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        btn_run = st.button("Run Scenario Simulation", type="primary", use_container_width=True)

# Update session state values
st.session_state["freight_shock"] = freight_shock_val
st.session_state["cong_shock"] = cong_shock_val
st.session_state["target_port"] = target_port_val
st.session_state["avail_shock"] = avail_shock_val
st.session_state["weather_risk"] = weather_val

# Run scenario simulation
scenario_req = ScenarioRequest(
    cargo_type="Coking Coal",
    quantity_tonnes=75000.0,
    origin="Australia",
    destination=target_port_val,
    earliest_date=forecast_df["date"].min().strftime("%Y-%m-%d"),
    latest_date=forecast_df["date"].max().strftime("%Y-%m-%d"),
    vessel_class="Auto",
    risk_tolerance="Medium",
    shock=ScenarioShock(
        freight_rate_shock_pct=freight_shock_val,
        port_congestion_shock_pct=cong_shock_val,
        target_port=target_port_val,
        vessel_availability_shock_pct=avail_shock_val,
        weather_risk_level=weather_val,
        geopolitical_risk_level="Normal"
    )
)

sim_res = run_scenario_simulation(forecast_df, scenario_req)

with c_preview:
    with st.container(border=True):
        st.markdown("### Impact Preview")
        st.caption("Predicted impact on logistics cost and charter recommendation")

        if sim_res["success"]:
            stress_rec = sim_res["stressed_recommendation"]
            base_rec = sim_res["baseline_recommendation"]
            
            s_cost_inr = usd_to_inr(stress_rec["total_logistics_cost_usd"])
            b_cost_inr = usd_to_inr(base_rec["total_logistics_cost_usd"])
            cost_diff_pct = ((s_cost_inr - b_cost_inr) / b_cost_inr) * 100.0

            p1, p2, p3 = st.columns(3)
            with p1:
                st.caption("EXPECTED COST")
                st.markdown(f"**{format_inr(s_cost_inr)}**")
                st.caption(f"{cost_diff_pct:+.1f}% vs baseline")

            with p2:
                st.caption("RECOMMENDED WINDOW")
                st.markdown(f"**{stress_rec['charter_date']}**")
                st.caption(f"{stress_rec['vessel_class']} Vessel")

            with p3:
                st.caption("DECISION STATUS")
                status_color = ":green[✓ UNCHANGED]" if sim_res["decision_status"] == "Recommendation Unchanged" else ":orange[⚠ ALTERED]"
                st.markdown(f"**{status_color}**")
                st.caption("Recommendation State")

            st.divider()
            st.caption("DECISION EXPLANATION")
            st.write(sim_res["explanation"])

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# BELOW: COMPARISON CHART & TABLE
if sim_res["success"]:
    with st.container(border=True):
        st.markdown("### Baseline vs Stressed Scenario Comparison")
        comp_df = pd.DataFrame(sim_res["comparison_table"])
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

render_disclaimer()

