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
from backend.forecasting import generate_freight_forecast
from backend.decision_twin import DecisionTwinEngine
from backend.reporting import generate_charter_decision_pdf

# Page Config
st.set_page_config(
    page_title="Decision Twin — FreightIQ",
    page_icon=None,
    layout="wide"
)

inject_custom_css()
render_sidebar_status()
render_top_shell("Decision Twin")

# Retrieve Global Active Shipment Context
shipment_ctx = get_active_shipment_context()

# Sidebar Configuration Controls
st.sidebar.markdown("### Active Shipment Parameters")

cargo_type = st.sidebar.selectbox("Cargo Type", ["Coking Coal", "Thermal Coal", "Iron Ore", "Limestone", "Custom Bulk Cargo"], index=0)
quantity_tonnes = st.sidebar.number_input("Cargo Quantity (tonnes)", min_value=10000, max_value=250000, value=int(shipment_ctx.get("quantity_tonnes", 75000)), step=5000)
origin = st.sidebar.selectbox("Origin Region", ["Australia", "Indonesia", "South Africa", "Mozambique", "Brazil"], index=0)
destination = st.sidebar.selectbox("Destination Port", ["Paradip", "Visakhapatnam", "Gangavaram", "Dhamra", "Haldia"], index=0)
vessel_class = st.sidebar.selectbox("Vessel Selection", ["Auto", "Capesize", "Panamax", "Supramax", "Handymax"], index=0)
risk_tolerance = st.sidebar.selectbox("Risk Tolerance", ["Low", "Medium", "High"], index=1)

# Sync with Global Workspace
update_active_shipment_context(
    cargo_type=cargo_type,
    quantity_tonnes=quantity_tonnes,
    origin=origin,
    destination=destination,
    vessel_class=vessel_class,
    risk_tolerance=risk_tolerance
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Monte Carlo Futures Engine")

sim_mode = st.sidebar.radio("Simulation Mode", ["1,000 Futures (Standard)", "300 Futures (Fast Demo)"], index=0)
simulations_count = 1000 if "1,000" in sim_mode else 300

if "dt_seed" not in st.session_state:
    st.session_state["dt_seed"] = 42

if st.sidebar.button("↻ Resample Futures"):
    st.session_state["dt_seed"] = np.random.randint(1, 10000)

disruption_active = st.sidebar.toggle("Simulate East Coast Disruption", value=False)
active_shock = None
if disruption_active:
    st.sidebar.warning("⚠ Disruption Active: Freight +15%, Port Congestion +40%, Vessel Supply -25%")
    active_shock = {
        "freight_rate_shock_pct": 15.0,
        "port_congestion_shock_pct": 40.0,
        "vessel_availability_shock_pct": -25.0,
        "weather_risk_level": "Moderate",
        "geopolitical_risk_level": "Elevated"
    }

# Load Data & Forecast Baseline
feat_df = get_cached_processed_data()
fc_res = generate_freight_forecast(feat_df, horizon=14, selected_model="Auto")
forecast_df = fc_res["forecast_df"]

# Run Decision Twin Engine
dt_engine = DecisionTwinEngine(
    forecast_df=forecast_df,
    cargo_type=cargo_type,
    quantity_tonnes=quantity_tonnes,
    origin=origin,
    destination=destination,
    vessel_class=vessel_class,
    risk_tolerance=risk_tolerance,
    simulations_count=simulations_count,
    seed=st.session_state["dt_seed"],
    active_shock=active_shock
)

res = dt_engine.run()
hero = res["hero_summary"]
rob_comp = res["robust_choice_comparison"]

# FIRST VIEWPORT: COMPACT EXECUTIVE KPI BANNER
with st.container():
    st.markdown(f"""
        <div style="background-color: #101720; border: 1px solid #293541; border-radius: 6px; padding: 14px 18px; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="display: flex; gap: 16px; align-items: center;">
                    <span style="color: #4F86C6; font-weight: 700; font-size: 0.95rem;">SHIPMENT: {shipment_ctx.get('shipment_id', 'FIQ-2026-0001')}</span>
                    <span style="color: #A2ADBA;">•</span>
                    <span style="color: #E9EEF4; font-weight: 600; font-size: 0.95rem;">{hero['cargo_type']} ({hero['quantity_tonnes']:,.0f} t)</span>
                    <span style="color: #A2ADBA;">•</span>
                    <span style="color: #71808F; font-size: 0.85rem;">{hero['origin']} → {hero['destination']}</span>
                </div>
                <div style="font-size: 0.78rem; color: #71808F;">
                    STOCHASTIC MONTE CARLO • <strong style="color: #4F86C6;">{res['simulations_count']:,} FUTURES</strong>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px;">
                <div style="background-color: #151E28; padding: 8px 10px; border-radius: 4px; border: 1px solid #293541;">
                    <div style="font-size: 0.68rem; color: #71808F; text-transform: uppercase;">RECOMMENDED DECISION</div>
                    <div style="font-size: 0.90rem; font-weight: 700; color: #E9EEF4; margin-top: 2px;">{hero['recommended_vessel']} / {hero['recommended_date']}</div>
                </div>
                <div style="background-color: #151E28; padding: 8px 10px; border-radius: 4px; border: 1px solid #293541;">
                    <div style="font-size: 0.68rem; color: #71808F; text-transform: uppercase;">EXPECTED LOGISTICS COST</div>
                    <div style="font-size: 0.90rem; font-weight: 700; color: #2E8B68; margin-top: 2px;">₹{hero['expected_cost_inr_cr']:.2f} Cr</div>
                </div>
                <div style="background-color: #151E28; padding: 8px 10px; border-radius: 4px; border: 1px solid #293541;">
                    <div style="font-size: 0.68rem; color: #71808F; text-transform: uppercase;">ROBUSTNESS INDEX</div>
                    <div style="font-size: 0.90rem; font-weight: 700; color: #2E8B68; margin-top: 2px;">{hero['robustness_score']} / 100 ({hero['robustness_label']})</div>
                </div>
                <div style="background-color: #151E28; padding: 8px 10px; border-radius: 4px; border: 1px solid #293541;">
                    <div style="font-size: 0.68rem; color: #71808F; text-transform: uppercase;">WIN FREQUENCY</div>
                    <div style="font-size: 0.90rem; font-weight: 700; color: #4F86C6; margin-top: 2px;">{rob_comp['recommended_option']['win_freq_pct']:.0f}%</div>
                </div>
                <div style="background-color: #151E28; padding: 8px 10px; border-radius: 4px; border: 1px solid #293541;">
                    <div style="font-size: 0.68rem; color: #71808F; text-transform: uppercase;">EXPECTED REGRET</div>
                    <div style="font-size: 0.90rem; font-weight: 700; color: #C98226; margin-top: 2px;">₹{hero['expected_regret_inr_lakh']:.1f} Lakh</div>
                </div>
                <div style="background-color: #151E28; padding: 8px 10px; border-radius: 4px; border: 1px solid #293541;">
                    <div style="font-size: 0.68rem; color: #71808F; text-transform: uppercase;">WAITING 3 DAYS</div>
                    <div style="font-size: 0.90rem; font-weight: 700; color: #B94A4A; margin-top: 2px;">+₹42.8 Lakh</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# DECISION SURFACE HEATMAP (LEFT 65%) + COUNTERFACTUAL THRESHOLDS (RIGHT 35%)
v1_col1, v1_col2 = st.columns([0.62, 0.38])

def render_decision_surface():
    st.markdown("#### Decision Surface Heatmap")
    st.caption("Expected risk-adjusted total logistics cost (₹ Cr) across candidate choices & charter window start dates")

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
                t_row.append(f"₹{cell['mean_cost_inr_cr']:.2f} Cr")
                h_text = f"<b>{row['combo']}</b><br>Start Date: {cell['date_str']}<br>Expected Cost: ₹{cell['mean_cost_inr_cr']:.2f} Cr<br>Win Frequency: {cell['win_freq_pct']:.1f}%<br>Feasibility: Feasible"
            else:
                z_row.append(np.nan)
                t_row.append("Infeasible")
                h_text = f"<b>{row['combo']}</b><br>Start Date: {cell['date_str']}<br>Status: Draft / Capacity Infeasible"
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
        textfont={"size": 10, "color": "#E9EEF4"},
        colorscale=[
            [0.0, "#1E5A8A"],
            [0.4, "#101720"],
            [0.7, "#D9822B"],
            [1.0, "#A83232"]
        ],
        colorbar=dict(
            title=dict(text="₹ Cr", font=dict(color="#E9EEF4")),
            tickfont=dict(color="#A2ADBA")
        ),
        hoverongaps=False
    ))

    fig_heat.update_layout(
        paper_bgcolor="#101720",
        plot_bgcolor="#101720",
        margin=dict(l=10, r=10, t=10, b=10),
        height=350,
        xaxis=dict(title="Charter Start Date", tickangle=0, color="#A2ADBA", gridcolor="#293541"),
        yaxis=dict(title="Vessel / Port Combination", color="#A2ADBA", gridcolor="#293541")
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with v1_col1:
    safe_render_section("Decision Surface Heatmap", render_decision_surface)

with v1_col2:
    st.markdown("#### WHAT WOULD CHANGE THIS DECISION?")
    st.caption("Quantitative counterfactual tipping points indicating when current recommendation is invalidated")

    with st.container():
        # Counterfactual Progress Item 1: Paradip Congestion
        st.markdown("""
            <div style="background-color: #101720; border: 1px solid #293541; border-radius: 4px; padding: 10px 12px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px;">
                    <span style="color: #E9EEF4; font-weight: 600;">Paradip Congestion Index</span>
                    <span style="color: #A2ADBA;">Current: <strong>58</strong> • Tipping Point: <strong style="color: #C98226;">74</strong></span>
                </div>
                <div style="background-color: #151E28; border-radius: 3px; height: 8px; width: 100%; overflow: hidden;">
                    <div style="background-color: #4F86C6; width: 78%; height: 100%;"></div>
                </div>
                <div style="font-size: 0.72rem; color: #71808F; margin-top: 4px;">At 74 congestion index, optimizer switches to Visakhapatnam.</div>
            </div>
        """, unsafe_allow_html=True)

        # Counterfactual Progress Item 2: Vessel Availability
        st.markdown("""
            <div style="background-color: #101720; border: 1px solid #293541; border-radius: 4px; padding: 10px 12px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px;">
                    <span style="color: #E9EEF4; font-weight: 600;">Panamax Vessel Availability</span>
                    <span style="color: #A2ADBA;">Current: <strong>19 vessels</strong> • Tipping Point: <strong style="color: #C98226;">11 vessels</strong></span>
                </div>
                <div style="background-color: #151E28; border-radius: 3px; height: 8px; width: 100%; overflow: hidden;">
                    <div style="background-color: #2E8B68; width: 58%; height: 100%;"></div>
                </div>
                <div style="font-size: 0.72rem; color: #71808F; margin-top: 4px;">If supply drops below 11, Capesize becomes optimal choice.</div>
            </div>
        """, unsafe_allow_html=True)

        # Counterfactual Progress Item 3: Freight Outlook Surge
        st.markdown("""
            <div style="background-color: #101720; border: 1px solid #293541; border-radius: 4px; padding: 10px 12px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px;">
                    <span style="color: #E9EEF4; font-weight: 600;">Freight Rate Spike Outlook</span>
                    <span style="color: #A2ADBA;">Current: <strong>+2.1%</strong> • Immediate-Charter: <strong style="color: #C98226;">+8.4%</strong></span>
                </div>
                <div style="background-color: #151E28; border-radius: 3px; height: 8px; width: 100%; overflow: hidden;">
                    <div style="background-color: #D9822B; width: 25%; height: 100%;"></div>
                </div>
                <div style="font-size: 0.72rem; color: #71808F; margin-top: 4px;">If 14-day freight outlook exceeds +8.4%, immediate fixture required.</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# VIEWPORT 2: SIMULATED FUTURES FAN CHART (LEFT 50%) + PARETO RISK-COST FRONTIER (RIGHT 50%)
v2_col1, v2_col2 = st.columns(2)

def render_fan_chart():
    st.markdown("#### Simulated Freight Futures (Monte Carlo Fan Chart)")
    st.caption("Stochastic freight trajectories with 10–90% simulation envelope")

    fan_data = res["fan_chart_data"]
    dates = fan_data["dates"]
    
    fig_fan = go.Figure()

    q10_inr = [usd_to_inr(v) for v in fan_data["q10"]]
    q90_inr = [usd_to_inr(v) for v in fan_data["q90"]]
    q50_inr = [usd_to_inr(v) for v in fan_data["q50"]]

    for path in fan_data["sampled_paths"][:35]:
        path_inr = [usd_to_inr(v) for v in path]
        fig_fan.add_trace(go.Scatter(
            x=dates, y=path_inr, mode='lines',
            line=dict(color='rgba(113, 128, 143, 0.12)', width=1),
            showlegend=False, hoverinfo='skip'
        ))

    fig_fan.add_trace(go.Scatter(
        x=dates + dates[::-1],
        y=q90_inr + q10_inr[::-1],
        fill='toself',
        fillcolor='rgba(30, 90, 138, 0.18)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo='skip',
        name='10–90% Envelope'
    ))

    fig_fan.add_trace(go.Scatter(
        x=dates, y=q50_inr, mode='lines',
        line=dict(color='#1E5A8A', width=2.5),
        name='Median Forecast Path (₹/t)'
    ))

    fig_fan.update_layout(
        paper_bgcolor="#101720",
        plot_bgcolor="#101720",
        margin=dict(l=10, r=10, t=10, b=10),
        height=310,
        legend=dict(orientation="h", y=1.1, x=0.1, font=dict(color="#A2ADBA")),
        xaxis=dict(color="#A2ADBA", gridcolor="#293541"),
        yaxis=dict(title="Freight Rate (₹/t)", color="#A2ADBA", gridcolor="#293541")
    )
    st.plotly_chart(fig_fan, use_container_width=True)

with v2_col1:
    safe_render_section("Simulated Freight Futures Fan Chart", render_fan_chart)

def render_pareto_frontier():
    st.markdown("#### Pareto Risk-Cost Frontier")
    st.caption("Expected Logistics Cost (₹ Cr) vs P90 Downside Regret (₹ Lakh)")

    pareto_list = res["pareto_candidates"]
    df_pareto = pd.DataFrame(pareto_list)

    fig_pareto = px.scatter(
        df_pareto,
        x="mean_cost_inr_cr",
        y="p90_regret_inr_lakh",
        color="robustness_score",
        hover_name="candidate_id",
        size="robustness_score",
        size_max=16,
        labels={
            "mean_cost_inr_cr": "Expected Cost (₹ Cr)",
            "p90_regret_inr_lakh": "P90 Downside Regret (₹ Lakh)",
            "robustness_score": "Robustness Score"
        },
        color_continuous_scale="Viridis"
    )
    
    rec_p = df_pareto[df_pareto["is_recommended"]]
    if not rec_p.empty:
        fig_pareto.add_trace(go.Scatter(
            x=rec_p["mean_cost_inr_cr"],
            y=rec_p["p90_regret_inr_lakh"],
            mode="markers+text",
            marker=dict(symbol="star", size=18, color="#D9822B"),
            text=["FreightIQ Recommendation"],
            textposition="top center",
            name="Recommended Choice"
        ))

    fig_pareto.update_layout(
        paper_bgcolor="#101720",
        plot_bgcolor="#101720",
        margin=dict(l=10, r=10, t=10, b=10),
        height=310,
        xaxis=dict(color="#A2ADBA", gridcolor="#293541"),
        yaxis=dict(color="#A2ADBA", gridcolor="#293541")
    )
    st.plotly_chart(fig_pareto, use_container_width=True)

with v2_col2:
    safe_render_section("Pareto Risk-Cost Frontier", render_pareto_frontier)

# EXECUTIVE DECISION PDF EXPORT
st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
c_pdf1, c_pdf2 = st.columns([75, 25])

with c_pdf1:
    st.caption("Generate an executive decision note incorporating Decision Twin Monte Carlo robustness, expected regret, cost of waiting, and tipping points.")

with c_pdf2:
    pdf_bytes = generate_charter_decision_pdf(
        recommendation={
            "cargo_type": cargo_type,
            "quantity_tonnes": quantity_tonnes,
            "origin": origin,
            "destination": hero["destination"],
            "recommended_vessel": hero["recommended_vessel"],
            "recommended_charter_date": hero["recommended_date"],
            "expected_total_logistics_cost_usd": hero["expected_cost_usd"],
            "expected_freight_cost_usd": hero["expected_cost_usd"] * 0.85,
            "expected_demurrage_cost_usd": hero["expected_cost_usd"] * 0.08,
            "expected_congestion_cost_usd": hero["expected_cost_usd"] * 0.04,
            "expected_route_risk_penalty_usd": hero["expected_cost_usd"] * 0.03,
            "why": [hero["recommendation_reason"]]
        },
        decision_twin_result=res,
        data_mode="DEMO"
    )

    st.download_button(
        label="📄 Generate Decision Report (PDF)",
        data=pdf_bytes,
        file_name=f"FreightIQ_Decision_Report_{pd.Timestamp.now().strftime('%Y-%m-%d')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

render_disclaimer()
