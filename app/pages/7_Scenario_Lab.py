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

st.set_page_config(
    page_title="FreightIQ — Scenario Lab",
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
    usd_to_inr
)
from backend.forecasting import generate_freight_forecast
from backend.schemas import ScenarioRequest, ScenarioShock
from backend.scenario_engine import run_scenario_simulation, format_inr_val

# 1. Inject Custom Industrial CSS
inject_custom_css()

# 2. Render Sidebar System Status
render_sidebar_status()

# 3. Top Shell Header
render_top_shell(active_page_name="Scenario Lab")

# 4. Page Header
st.markdown("### Scenario Lab")
st.caption("Stress-test charter decisions under changing freight, congestion and risk conditions.")

# 5. Load Processed Dataset & Generate 30-day baseline forecast
try:
    df = get_cached_processed_data()
    fc_res = generate_freight_forecast(df, horizon=30, selected_model="Auto")
    forecast_df = fc_res["forecast_df"]
except Exception as e:
    st.error(f"Error loading forecasting engine for Scenario Lab: {e}")
    st.stop()

# Initialize session state for preset shocks if not set
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

# 6. QUICK PRESET BUTTONS
st.markdown("### Quick Preset Stress Scenarios")
p_col1, p_col2, p_col3, p_col4, p_col5, p_col6, p_col7 = st.columns(7)

with p_col1:
    if st.button("East Coast Disruption", help="SIH Demo Preset: Paradip Congestion +55%, Availability -30%, Weather High"):
        st.session_state["freight_shock"] = 12.0
        st.session_state["cong_shock"] = 55.0
        st.session_state["target_port"] = "Paradip"
        st.session_state["avail_shock"] = -30.0
        st.session_state["weather_risk"] = "High"
        st.session_state["geo_risk"] = "Elevated"
        st.session_state["dem_shock"] = 15.0
        st.rerun()

with p_col2:
    if st.button("Freight Spike", help="Dry bulk rates surge +15%"):
        st.session_state["freight_shock"] = 15.0
        st.session_state["cong_shock"] = 0.0
        st.session_state["avail_shock"] = 0.0
        st.session_state["weather_risk"] = "Low"
        st.session_state["geo_risk"] = "Normal"
        st.rerun()

with p_col3:
    if st.button("Paradip Congestion", help="Paradip congestion +50%"):
        st.session_state["freight_shock"] = 0.0
        st.session_state["cong_shock"] = 50.0
        st.session_state["target_port"] = "Paradip"
        st.session_state["avail_shock"] = 0.0
        st.rerun()

with p_col4:
    if st.button("Vessel Shortage", help="Vessel availability drops -35%"):
        st.session_state["freight_shock"] = 0.0
        st.session_state["cong_shock"] = 0.0
        st.session_state["avail_shock"] = -35.0
        st.rerun()

with p_col5:
    if st.button("Severe Weather", help="Weather risk set to Severe"):
        st.session_state["weather_risk"] = "Severe"
        st.rerun()

with p_col6:
    if st.button("Combined Stress", help="Freight +12%, Congestion +35%, Avail -25%"):
        st.session_state["freight_shock"] = 12.0
        st.session_state["cong_shock"] = 35.0
        st.session_state["avail_shock"] = -25.0
        st.session_state["geo_risk"] = "Elevated"
        st.rerun()

with p_col7:
    if st.button("Market Relief", help="Freight -10%, Congestion -20%, Avail +20%"):
        st.session_state["freight_shock"] = -10.0
        st.session_state["cong_shock"] = -20.0
        st.session_state["avail_shock"] = 20.0
        st.session_state["weather_risk"] = "Low"
        st.session_state["geo_risk"] = "Normal"
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# 7. TWO-COLUMN LAYOUT: BASE SHIPMENT CONFIG (LEFT) vs SCENARIO SHOCKS (RIGHT)
col_left, col_right = st.columns([0.42, 0.58])

with col_left:
    st.markdown("### Base Shipment Configuration")
    with st.container():
        st.markdown("<div style='background-color: #101720; padding: 16px; border-radius: 6px; border: 1px solid #293541;'>", unsafe_allow_html=True)
        
        cfg_cargo = st.selectbox("Cargo Type", ["Coking Coal", "Iron Ore"], index=0)
        cfg_qty = st.number_input("Cargo Quantity (tonnes)", min_value=10000.0, max_value=200000.0, value=75000.0, step=5000.0)
        
        cfg_c1, cfg_c2 = st.columns(2)
        with cfg_c1:
            cfg_origin = st.selectbox("Origin Port", ["Australia", "Indonesia", "South Africa"], index=0)
        with cfg_c2:
            cfg_dest = st.selectbox("Destination Port", ["Paradip", "Visakhapatnam", "Kolkata/Haldia"], index=0)

        min_date = forecast_df["date"].min().date()
        max_date = forecast_df["date"].max().date()

        dt_col1, dt_col2 = st.columns(2)
        with dt_col1:
            cfg_start_dt = st.date_input("Earliest Charter Date", value=min_date, min_value=min_date, max_value=max_date)
        with dt_col2:
            cfg_end_dt = st.date_input("Latest Charter Date", value=max_date, min_value=min_date, max_value=max_date)

        cfg_vessel = st.selectbox("Vessel Class Preference", ["Auto", "Capesize", "Panamax", "Supramax"], index=0)
        cfg_risk = st.selectbox("Risk Preference", ["Balanced", "Conservative", "Flexible"], index=0)
        
        st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown("### Scenario Shock Controls")
    with st.container():
        st.markdown("<div style='background-color: #101720; padding: 16px; border-radius: 6px; border: 1px solid #293541;'>", unsafe_allow_html=True)
        
        sh_col1, sh_col2 = st.columns(2)
        with sh_col1:
            freight_shock_val = st.slider(
                "Freight Rate Change (%)",
                min_value=-20.0, max_value=30.0,
                value=float(st.session_state["freight_shock"]),
                step=1.0,
                help="Simulates dry bulk freight market price rise/fall"
            )
            
            cong_shock_val = st.slider(
                "Port Congestion Change (%)",
                min_value=-50.0, max_value=100.0,
                value=float(st.session_state["cong_shock"]),
                step=5.0,
                help="Simulates port waiting time surge or clearance"
            )
            
            target_port_val = st.selectbox(
                "Target Port for Congestion",
                ["Paradip", "Visakhapatnam", "Kolkata/Haldia", "All East Coast Ports"],
                index=["Paradip", "Visakhapatnam", "Kolkata/Haldia", "All East Coast Ports"].index(st.session_state["target_port"]) if st.session_state["target_port"] in ["Paradip", "Visakhapatnam", "Kolkata/Haldia", "All East Coast Ports"] else 0
            )

            comm_shock_val = st.slider(
                "Commodity Price Change (%)",
                min_value=-20.0, max_value=30.0,
                value=float(st.session_state["comm_shock"]),
                step=5.0,
                help="Procurement context input for coal/ore market pressure"
            )

        with sh_col2:
            avail_shock_val = st.slider(
                "Vessel Availability Change (%)",
                min_value=-60.0, max_value=50.0,
                value=float(st.session_state["avail_shock"]),
                step=5.0,
                help="Simulates vessel shortage or excess supply"
            )

            weather_val = st.selectbox(
                "Weather Risk",
                ["Low", "Moderate", "High", "Severe"],
                index=["Low", "Moderate", "High", "Severe"].index(st.session_state["weather_risk"])
            )

            geo_val = st.selectbox(
                "Geopolitical / Route Risk",
                ["Normal", "Elevated", "Major Disruption"],
                index=["Normal", "Elevated", "Major Disruption"].index(st.session_state["geo_risk"]) if st.session_state["geo_risk"] in ["Normal", "Elevated", "Major Disruption"] else 0
            )

            dem_shock_val = st.slider(
                "Demurrage Rate Change (%)",
                min_value=-20.0, max_value=50.0,
                value=float(st.session_state["dem_shock"]),
                step=5.0,
                help="Simulates contractual demurrage rate changes"
            )

        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 8. RUN SCENARIO SIMULATION
btn_run = st.button("Run Scenario Simulation", type="primary", use_container_width=True)

# Update session state with current slider values
st.session_state["freight_shock"] = freight_shock_val
st.session_state["cong_shock"] = cong_shock_val
st.session_state["target_port"] = target_port_val
st.session_state["avail_shock"] = avail_shock_val
st.session_state["comm_shock"] = comm_shock_val
st.session_state["weather_risk"] = weather_val
st.session_state["geo_risk"] = geo_val
st.session_state["dem_shock"] = dem_shock_val

req_risk_tol = "High" if cfg_risk == "Flexible" else ("Low" if cfg_risk == "Conservative" else "Medium")

scenario_req = ScenarioRequest(
    cargo_type=cfg_cargo,
    quantity_tonnes=cfg_qty,
    origin=cfg_origin,
    destination=cfg_dest,
    earliest_date=cfg_start_dt.strftime("%Y-%m-%d"),
    latest_date=cfg_end_dt.strftime("%Y-%m-%d"),
    vessel_class=cfg_vessel,
    risk_tolerance=req_risk_tol,
    shock=ScenarioShock(
        freight_rate_shock_pct=freight_shock_val,
        port_congestion_shock_pct=cong_shock_val,
        target_port=target_port_val,
        vessel_availability_shock_pct=avail_shock_val,
        commodity_price_shock_pct=comm_shock_val,
        weather_risk_level=weather_val,
        geopolitical_risk_level=geo_val,
        demurrage_rate_shock_pct=dem_shock_val
    )
)

sim_res = run_scenario_simulation(forecast_df, scenario_req)

if not sim_res["success"]:
    st.error(f"Scenario Simulation Error: {sim_res.get('error')}")
    st.stop()

# 9. DECISION STATUS & EXPLANATION BANNER
st.markdown("---")
status_title = sim_res["decision_status"]
status_color = "#2E8B68" if status_title == "Recommendation Unchanged" else "#C98226"

with st.container(border=True):
    st.markdown(f"**SIMULATION RESULT: DECISION STATUS — {status_title.upper()}**")
    st.caption(sim_res['explanation'])

# 10. SIDE-BY-SIDE COMPARISON TABLE
st.markdown("### Baseline vs Stressed Scenario Comparison")
comp_df = pd.DataFrame(sim_res["comparison_table"])

# Format comparison table visually
comp_display = []
for _, row in comp_df.iterrows():
    metric = row["metric"]
    base_v = row["baseline"]
    stress_v = row["stress_scenario"]
    is_chg = row["changed"]

    comp_display.append({
        "Metric": metric,
        "Baseline": base_v,
        "Stressed Scenario": stress_v,
        "Status": "CHANGED" if is_chg else "Unchanged"
    })

df_comp_disp = pd.DataFrame(comp_display)
st.dataframe(
    df_comp_disp,
    use_container_width=True,
    column_config={
        "Metric": st.column_config.TextColumn("Metric", width="medium"),
        "Baseline": st.column_config.TextColumn("Baseline Option"),
        "Stressed Scenario": st.column_config.TextColumn("Stressed Option"),
        "Status": st.column_config.TextColumn("Variance Status")
    },
    hide_index=True
)

st.markdown("<br>", unsafe_allow_html=True)

# 11. COST BREAKDOWN STACKED BAR CHART & CONFIDENCE GAUGE
col_chart, col_conf = st.columns([0.65, 0.35])

with col_chart:
    st.markdown("### Total Expected Logistics Cost Breakdown (INR)")
    base_opt = sim_res["baseline_recommendation"]
    stress_opt = sim_res["stressed_recommendation"]

    # Calculate components in INR Lakhs
    b_freight_lakh = usd_to_inr(base_opt["freight_cost_usd"]) / 100_000.0
    s_freight_lakh = usd_to_inr(stress_opt["freight_cost_usd"]) / 100_000.0

    b_dem_lakh = usd_to_inr(base_opt["demurrage_cost_usd"]) / 100_000.0
    s_dem_lakh = usd_to_inr(stress_opt["demurrage_cost_usd"]) / 100_000.0

    b_cong_lakh = usd_to_inr(base_opt["congestion_cost_usd"]) / 100_000.0
    s_cong_lakh = usd_to_inr(stress_opt["congestion_cost_usd"]) / 100_000.0

    b_risk_lakh = usd_to_inr(base_opt["route_risk_penalty_usd"]) / 100_000.0
    s_risk_lakh = usd_to_inr(stress_opt["route_risk_penalty_usd"]) / 100_000.0

    fig_cost = go.Figure(data=[
        go.Bar(name='Freight Cost', x=['Baseline', 'Stressed Scenario'], y=[b_freight_lakh, s_freight_lakh], marker_color='#1E5A8A'),
        go.Bar(name='Demurrage Cost', x=['Baseline', 'Stressed Scenario'], y=[b_dem_lakh, s_dem_lakh], marker_color='#C98226'),
        go.Bar(name='Port Waiting', x=['Baseline', 'Stressed Scenario'], y=[b_cong_lakh, s_cong_lakh], marker_color='#A2ADBA'),
        go.Bar(name='Risk Penalty', x=['Baseline', 'Stressed Scenario'], y=[b_risk_lakh, s_risk_lakh], marker_color='#A63D40')
    ])

    fig_cost.update_layout(
        barmode='stack',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#101720',
        font=dict(color='#E9EEF4', family='IBM Plex Sans'),
        height=320,
        margin=dict(l=20, r=20, t=30, b=30),
        yaxis=dict(title='Cost (₹ Lakh)', gridcolor='#293541'),
        xaxis=dict(gridcolor='#293541'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig_cost, use_container_width=True)

with col_conf:
    st.markdown("### Decision Confidence")
    conf_score = sim_res["confidence_score"]
    conf_bd = sim_res["confidence_breakdown"]

    with st.container(border=True):
        st.metric("COMPOSITE CONFIDENCE SCORE", f"{conf_score:.0f} / 100")
        st.caption(conf_bd['explanation'])
        st.markdown(f"""
        - Weather Risk Penalty: -{conf_bd['weather_risk_deduction']} pts
        - Geopolitical Deduction: -{conf_bd['geopolitical_deduction']} pts
        - Congestion Volatility: -{conf_bd['congestion_volatility_deduction']} pts
        - Option Separation Margin: +{conf_bd['option_separation_bonus']} pts
        """)

st.markdown("<br>", unsafe_allow_html=True)

# 12. DECISION SENSITIVITY & THRESHOLD ANALYSIS
c_sens, c_thresh = st.columns([0.5, 0.5])

with c_sens:
    st.markdown("### Decision Sensitivity")
    st.markdown("<div style='color: #71808F; font-size: 0.8rem; margin-bottom: 10px;'>Impact of operational variable perturbations on total logistics cost.</div>", unsafe_allow_html=True)
    
    sens_df = pd.DataFrame(sim_res["sensitivity_analysis"])
    if not sens_df.empty:
        st.dataframe(
            sens_df[["variable", "influence_level", "cost_impact_pct"]],
            use_container_width=True,
            column_config={
                "variable": st.column_config.TextColumn("Variable"),
                "influence_level": st.column_config.TextColumn("Influence Rank"),
                "cost_impact_pct": st.column_config.NumberColumn("Cost Impact (%)", format="%.2f%%")
            },
            hide_index=True
        )

with c_thresh:
    st.markdown("### Threshold Analysis")
    st.markdown("<div style='color: #71808F; font-size: 0.8rem; margin-bottom: 10px;'>Prototype sensitivity estimates: conditions required to alter recommendation.</div>", unsafe_allow_html=True)
    
    thresh_df = pd.DataFrame(sim_res["threshold_analysis"])
    if not thresh_df.empty:
        st.dataframe(
            thresh_df[["variable", "tipping_point", "status"]],
            use_container_width=True,
            column_config={
                "variable": st.column_config.TextColumn("Variable"),
                "tipping_point": st.column_config.TextColumn("Estimated Tipping Point"),
                "status": st.column_config.TextColumn("System Status")
            },
            hide_index=True
        )

st.markdown("<br>", unsafe_allow_html=True)

# 13. PORT ALTERNATIVE ANALYSIS
st.markdown("### Port Alternative Analysis")
st.markdown("<div style='color: #71808F; font-size: 0.8rem; margin-bottom: 10px;'>Comparative evaluation across India East Coast discharge ports under current scenario shocks.</div>", unsafe_allow_html=True)

port_df = pd.DataFrame(sim_res["port_alternative_analysis"])
if not port_df.empty:
    st.dataframe(
        port_df[["port", "expected_cost_inr_formatted", "congestion_score", "draft_compatibility", "vessel_compatibility", "overall_rank"]],
        use_container_width=True,
        column_config={
            "port": st.column_config.TextColumn("Discharge Port"),
            "expected_cost_inr_formatted": st.column_config.TextColumn("Expected Cost (INR)"),
            "congestion_score": st.column_config.NumberColumn("Congestion Score", format="%.0f/100"),
            "draft_compatibility": st.column_config.TextColumn("Draft Compatibility"),
            "vessel_compatibility": st.column_config.TextColumn("Vessel Compatibility"),
            "overall_rank": st.column_config.TextColumn("Rank")
        },
        hide_index=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# 14. EXECUTIVE STRESS TEST REPORT EXPORT
from backend.reporting import generate_charter_decision_pdf

pdf_bytes = generate_charter_decision_pdf(
    recommendation=sim_res["stressed_recommendation"],
    scenario_result=sim_res,
    data_mode="DEMO"
)

st.download_button(
    label="Generate Stress Test Decision Report (PDF)",
    data=pdf_bytes,
    file_name=f"FreightIQ_Stress_Test_Report_{datetime.now().strftime('%Y-%m-%d_%H%M')}.pdf",
    mime="application/pdf",
    use_container_width=True
)

# 15. DISCLAIMER FOOTER
render_disclaimer()
