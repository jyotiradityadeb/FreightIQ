"""
FreightIQ Charter Decision Twin Streamlit Page

Evaluates charter decisions across 1,000 stochastic Monte Carlo futures
to provide robust decision support, hindsight regret surfaces, and counterfactual thresholds.
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
import plotly.express as px

from app.navigation import (
    CONTROL_TOWER_PAGE,
    DECISION_TWIN_PAGE,
    CHARTER_PAGE,
    SCENARIO_PAGE,
    navigate_to
)
from app.components.helpers import (
    inject_custom_css,
    render_top_shell,
    render_sidebar_status,
    render_disclaimer,
    format_inr,
    usd_to_inr,
    get_cached_processed_data,
    get_active_shipment_context,
    update_active_shipment_context
)
from app.components.error_boundary import safe_render_section
from backend.config import DEMO_USD_INR_RATE
from backend.forecasting import generate_freight_forecast
from backend.decision_twin import DecisionTwinEngine, get_or_compute_decision_twin
from backend.reporting import generate_charter_decision_pdf


# Page Config
st.set_page_config(page_title="FreightIQ — Decision Twin", page_icon=None, layout="wide")

inject_custom_css()
render_sidebar_status()
render_top_shell("Decision Twin")

# Retrieve Global Active Shipment Context
shipment_ctx = get_active_shipment_context()

# Header
st.markdown("<h1 style='margin-bottom: 2px;'>Decision Twin</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #6B7280; font-size: 0.95rem; margin-bottom: 20px;'>Stress-test charter recommendations across simulated market conditions.</p>", unsafe_allow_html=True)
st.caption("Source: simulated futures on synthetic demo state — not real-market scenario data")

# Sidebar Controls
cargo_type = st.sidebar.selectbox("Cargo Type", ["Coking Coal", "Thermal Coal", "Iron Ore", "Custom Bulk Cargo"], index=0)
quantity_tonnes = st.sidebar.number_input("Quantity (t)", min_value=10000, max_value=250000, value=int(shipment_ctx.get("quantity_tonnes", 75000)), step=5000)
origin = st.sidebar.selectbox("Origin Region", ["Australia", "Indonesia", "South Africa"], index=0)
destination = st.sidebar.selectbox("Destination Port", ["Paradip", "Visakhapatnam", "Haldia"], index=0)

# Sync Active Context
update_active_shipment_context(
    cargo_type=cargo_type,
    quantity_tonnes=quantity_tonnes,
    origin=origin,
    destination=destination
)

# Retrieve active scenario from session state
active_scenario = st.session_state.get("active_scenario", {})
if active_scenario.get("is_active"):
    st.info(f"⚡ Active Scenario Applied: **{active_scenario.get('scenario_name', 'Custom Shock')}**")

# Load Data & Run / Retrieve Engine Result
feat_df = get_cached_processed_data()
fc_res = generate_freight_forecast(feat_df, horizon=30, selected_model="Auto")
forecast_df = fc_res["forecast_df"]


res = get_or_compute_decision_twin(
    shipment_ctx=get_active_shipment_context(),
    active_scenario=active_scenario,
    forecast_df=forecast_df,
    simulations_count=1000,
    seed=42
)

if not res.get("success"):
    st.warning(f"⚠ Optimization Infeasible: {res.get('error', 'No feasible candidate under this simulated state.')}")
    if "disclaimer" in res:
        st.info(res["disclaimer"])
    render_disclaimer()
    st.stop()

hero = res["hero_summary"]

# TOP: RECOMMENDATION SUMMARY (Clean SaaS Surface)
with st.container(border=True):
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.caption("RECOMMENDED ACTION")
        st.markdown(f"### {hero['recommended_vessel']} / {hero['recommended_date']}")
        st.caption("Recommended vessel & charter window (simulated)")
    with r2:
        st.caption("EXPECTED LOGISTICS COST")
        st.markdown(f"<h3 style='color: #1667D9;'>₹{hero['expected_cost_inr_cr']:.2f} Cr</h3>", unsafe_allow_html=True)
        st.caption("Mean across 1,000 futures")
    with r3:
        st.caption("DECISION ROBUSTNESS")
        st.markdown(f"<h3 style='color: #10B981;'>{hero['robustness_score']} / 100</h3>", unsafe_allow_html=True)
        sims_cnt = res.get("simulations_count", 1000)
        st.caption(f"Composite robustness score across {sims_cnt:,} simulated futures")

    with r4:
        st.caption("EXPECTED REGRET")
        st.markdown(f"### ₹{hero['expected_regret_inr_lakh']:.1f} Lakh")
        st.caption("Minimal downside regret")

    st.divider()

    btn_l, btn_r = st.columns([2, 1])
    with btn_r:
        dt_rec = {
            "shipment_id": shipment_ctx.get("shipment_id", "FIQ-2026-0001"),
            "cargo_type": cargo_type,
            "quantity_tonnes": quantity_tonnes,
            "origin": origin,
            "destination": destination,
            "recommended_vessel": hero['recommended_vessel'],
            "recommended_window": hero['recommended_date'],
            "expected_total_cost_usd": hero['expected_cost_inr_cr'] * 10000000.0 / DEMO_USD_INR_RATE if 'DEMO_USD_INR_RATE' in globals() else 2200000.0
        }
        pdf_bytes = generate_charter_decision_pdf(
            recommendation=dt_rec,
            decision_twin_result=res,
            scenario_result=active_scenario if active_scenario.get("is_active") else None,
            data_mode="DEMO"
        )
        st.download_button(
            label="Download Decision Twin Report (PDF)",
            data=pdf_bytes,
            file_name=f"FreightIQ_Decision_Twin_Report_{pd.Timestamp.now().strftime('%Y-%m-%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)


# MIDDLE: DECISION SURFACE
with st.container(border=True):
    st.markdown("### Decision Surface")
    st.caption("Expected risk-adjusted total logistics cost across candidate choices and charter dates")

    heatmap_matrix = res["heatmap_matrix"]
    y_labels = [row["combo"] for row in heatmap_matrix]
    x_labels = [c["date_str"][-5:] for c in heatmap_matrix[0]["cells"]]

    z_values = []
    text_values = []
    hover_texts = []
    for row in heatmap_matrix:
        z_row = []
        t_row = []
        h_row = []
        for cell in row["cells"]:
            if cell["feasible"] and cell["mean_cost_inr_cr"] is not None:
                z_row.append(cell["mean_cost_inr_cr"])
                t_row.append(f"₹{cell['mean_cost_inr_cr']:.2f}Cr")
                h_text = f"<b>{row['combo']}</b><br>Cost: ₹{cell['mean_cost_inr_cr']:.2f} Cr<br>Win Freq: {cell['win_freq_pct']:.1f}%"
            else:
                z_row.append(np.nan)
                t_row.append("N/A")
                h_text = "Infeasible"
            h_row.append(h_text)
        z_values.append(z_row)
        text_values.append(t_row)
        hover_texts.append(h_row)

    fig_heat = go.Figure(data=go.Heatmap(
        z=z_values,
        x=x_labels,
        y=y_labels,
        text=text_values,
        hoverinfo="text",
        hovertext=hover_texts,
        texttemplate="%{text}",
        textfont={"size": 10, "color": "#111827"},
        colorscale=[[0.0, "#EFF6FF"], [0.5, "#93C5FD"], [1.0, "#1667D9"]],
        showscale=False
    ))
    fig_heat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        xaxis=dict(gridcolor="#F1F5F9", tickfont=dict(color="#6B7280")),
        yaxis=dict(gridcolor="#F1F5F9", tickfont=dict(color="#6B7280"))
    )
    st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# BELOW: SIMULATED FREIGHT FUTURES
with st.container(border=True):
    st.markdown("### Simulated Freight Futures")
    st.caption("Stochastic freight trajectories with 10–90% simulation envelope across 1,000 futures")

    fan_data = res["fan_chart_data"]
    dates = fan_data["dates"]
    fig_fan = go.Figure()

    q10_inr = [usd_to_inr(v) for v in fan_data["q10"]]
    q90_inr = [usd_to_inr(v) for v in fan_data["q90"]]
    q50_inr = [usd_to_inr(v) for v in fan_data["q50"]]

    fig_fan.add_trace(go.Scatter(
        x=dates + dates[::-1],
        y=q90_inr + q10_inr[::-1],
        fill='toself',
        fillcolor='rgba(22, 103, 217, 0.10)',
        line=dict(color='rgba(0,0,0,0)'),
        hoverinfo='skip',
        name='10–90% Envelope'
    ))

    fig_fan.add_trace(go.Scatter(
        x=dates, y=q50_inr, mode='lines',
        line=dict(color='#1667D9', width=2.5),
        name='Median Forecast Path (₹/t)'
    ))

    fig_fan.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        legend=dict(orientation="h", y=1.05, x=1),
        xaxis=dict(gridcolor="#F1F5F9", tickfont=dict(color="#6B7280")),
        yaxis=dict(gridcolor="#F1F5F9", tickfont=dict(color="#6B7280"))
    )
    st.plotly_chart(fig_fan, use_container_width=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# BELOW: WHAT WOULD CHANGE THIS DECISION?
with st.container(border=True):
    st.markdown("### What Would Change This Decision?")
    st.caption("Quantitative counterfactual tipping points indicating when recommendation alters (Model-derived heuristic threshold)")

    cf_list = res.get("counterfactuals", [])
    if cf_list:
        cols = st.columns(min(len(cf_list), 4))
        for idx, cf in enumerate(cf_list[:4]):
            with cols[idx]:
                st.markdown(f"**{cf['trigger_event']}**")
                st.caption(f"Current: {cf['current_val']} • Tipping Point: {cf['threshold_val']}")
                st.write(cf['action'])
    else:
        st.caption("No counterfactual tipping points derived for this state.")

render_disclaimer()

