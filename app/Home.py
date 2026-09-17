"""
FreightIQ Primary Landing Page — Control Tower
Real-Time Disruption Intelligence & Maritime Charter Monitoring Command Centre
"""

import os
import sys

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Control Tower — FreightIQ",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

from app.navigation import (
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
    get_cached_processed_data,
    format_inr,
    usd_to_inr,
    get_active_shipment_context,
    update_active_shipment_context
)
from app.components.error_boundary import safe_render_section
from backend.forecasting import generate_freight_forecast
from backend.schemas import ScenarioShock
from backend.disruption_engine import evaluate_control_tower_state

# 1. Inject Custom Industrial CSS
inject_custom_css()

# 2. Render Sidebar System Status
render_sidebar_status()

# 3. Top Shell Header
render_top_shell(active_page_name="Control Tower")

# 4. Global Active Shipment Sync
shipment_ctx = get_active_shipment_context()

# Header Compact Banner
st.markdown(f"""
    <div style="background-color: #101720; border: 1px solid #293541; border-radius: 6px; padding: 10px 16px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
        <div style="display: flex; gap: 18px; align-items: center; font-size: 0.85rem;">
            <span style="color: #4F86C6; font-weight: 700;">ACTIVE SHIPMENT: {shipment_ctx.get('shipment_id', 'FIQ-2026-0001')}</span>
            <span style="color: #A2ADBA;">•</span>
            <span style="color: #E9EEF4; font-weight: 600;">{shipment_ctx.get('cargo_type', 'Coking Coal')} ({shipment_ctx.get('quantity_tonnes', 75000):,.0f} t)</span>
            <span style="color: #A2ADBA;">•</span>
            <span style="color: #71808F;">{shipment_ctx.get('origin', 'Australia')} → {shipment_ctx.get('destination', 'Paradip')}</span>
        </div>
        <div style="display: flex; gap: 14px; align-items: center; font-size: 0.78rem; color: #71808F;">
            <span>DATA MODE: <strong style="color: #D9822B;">DEMO [D]</strong></span>
            <span>PUBLIC API: <strong style="color: #2E8B68;">OPEN-METEO [P]</strong></span>
            <span>OPTIMIZER: <strong style="color: #2E8B68;">ACTIVE</strong></span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Session State for Disruption Demo
if "disruption_demo_active" not in st.session_state:
    st.session_state["disruption_demo_active"] = False

# Load Processed Dataset & Run Disruption Engine
try:
    df = get_cached_processed_data()
    fc_res = generate_freight_forecast(df, horizon=30, selected_model="Auto")
    forecast_df = fc_res["forecast_df"]

    shock_override = None
    if st.session_state["disruption_demo_active"]:
        shock_override = ScenarioShock(
            freight_rate_shock_pct=float(st.session_state.get("freight_shock", 12.0)),
            port_congestion_shock_pct=float(st.session_state.get("cong_shock", 55.0)),
            target_port=st.session_state.get("target_port", "Paradip"),
            vessel_availability_shock_pct=float(st.session_state.get("avail_shock", -30.0)),
            weather_risk_level=st.session_state.get("weather_risk", "High"),
            geopolitical_risk_level=st.session_state.get("geo_risk", "Elevated")
        )

    ct_data = evaluate_control_tower_state(forecast_df=forecast_df, shock_override=shock_override)
except Exception as e:
    st.error(f"Error executing Control Tower Disruption Engine: {e}")
    st.stop()

curr_rec = ct_data["current_recommendation"]
signals = ct_data["signal_states"]
stress_idx = ct_data["market_stress_index"]
stability_idx = ct_data["decision_stability"]

# FIRST VIEWPORT: 5 COMPACT EXECUTIVE KPI CARDS
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    rec_status = curr_rec["status"]
    s_color = "#2E8B68" if rec_status == "RECOMMENDATION VALID" else "#C98226"
    st.markdown(f"""
        <div style="background-color: #101720; border: 1px solid #293541; border-top: 3px solid {s_color}; border-radius: 6px; padding: 12px 14px;">
            <div style="font-size: 0.70rem; color: #71808F; font-weight: 700; text-transform: uppercase;">RECOMMENDED WINDOW</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #E9EEF4; margin: 4px 0;">{curr_rec['recommended_window']}</div>
            <div style="font-size: 0.75rem; color: #2E8B68; font-weight: 600;">{curr_rec['vessel_class']} Vessel</div>
        </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
        <div style="background-color: #101720; border: 1px solid #293541; border-top: 3px solid #4F86C6; border-radius: 6px; padding: 12px 14px;">
            <div style="font-size: 0.70rem; color: #71808F; font-weight: 700; text-transform: uppercase;">EXPECTED LOGISTICS COST</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #E9EEF4; margin: 4px 0;">{curr_rec['expected_total_cost_inr_formatted']}</div>
            <div style="font-size: 0.75rem; color: #71808F;">Confidence: {curr_rec['decision_confidence']:.0f}/100</div>
        </div>
    """, unsafe_allow_html=True)

with k3:
    str_val = stress_idx["score"]
    str_col = "#2E8B68" if str_val < 35 else ("#C98226" if str_val < 65 else "#B94A4A")
    st.markdown(f"""
        <div style="background-color: #101720; border: 1px solid #293541; border-top: 3px solid {str_col}; border-radius: 6px; padding: 12px 14px;">
            <div style="font-size: 0.70rem; color: #71808F; font-weight: 700; text-transform: uppercase;">MARKET STRESS INDEX</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: {str_col}; margin: 4px 0;">{str_val:.0f} / 100</div>
            <div style="font-size: 0.75rem; color: #71808F;">State: {stress_idx['state'].title()}</div>
        </div>
    """, unsafe_allow_html=True)

with k4:
    stb_val = stability_idx["score"]
    stb_col = "#2E8B68" if stb_val >= 75 else ("#C98226" if stb_val >= 55 else "#B94A4A")
    st.markdown(f"""
        <div style="background-color: #101720; border: 1px solid #293541; border-top: 3px solid {stb_col}; border-radius: 6px; padding: 12px 14px;">
            <div style="font-size: 0.70rem; color: #71808F; font-weight: 700; text-transform: uppercase;">DECISION ROBUSTNESS</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: {stb_col}; margin: 4px 0;">{stb_val:.0f} / 100</div>
            <div style="font-size: 0.75rem; color: #71808F;">{stability_idx['interpretation']}</div>
        </div>
    """, unsafe_allow_html=True)

with k5:
    st.markdown("""
        <div style="background-color: #101720; border: 1px solid #293541; border-top: 3px solid #D9822B; border-radius: 6px; padding: 12px 14px;">
            <div style="font-size: 0.70rem; color: #71808F; font-weight: 700; text-transform: uppercase;">DATA COVERAGE</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #E9EEF4; margin: 4px 0;">88% Coverage</div>
            <div style="font-size: 0.75rem; color: #71808F;">1 Live [P] • 4 Demo [D]</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# MAIN VIEWPORT LAYOUT: MAP (LEFT 60%) vs PORT STATUS & SIGNALS (RIGHT 40%)
c_map, c_info = st.columns([0.60, 0.40])

def render_control_tower_map():
    st.markdown("#### Maritime Passage & Port Operations Map")
    
    # Coordinates for key nodes
    map_data = pd.DataFrame([
        {"node": "Hay Point (Origin)", "lat": -21.2833, "lon": 149.3000, "type": "Origin Port", "status": "Normal Operations", "size": 14},
        {"node": "Malacca Strait", "lat": 2.5000, "lon": 101.5000, "type": "Chokepoint", "status": "Clear Passage", "size": 10},
        {"node": "Paradip (Primary)", "lat": 20.2644, "lon": 86.6744, "type": "Discharge Port", "status": "Congestion 64/100 (39h wait)", "size": 16},
        {"node": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185, "type": "Discharge Port", "status": "Manageable (26h wait)", "size": 12},
        {"node": "Dhamra", "lat": 20.8000, "lon": 86.9700, "type": "Discharge Port", "status": "Normal Queue (22h wait)", "size": 12},
        {"node": "Haldia / Kolkata", "lat": 22.0258, "lon": 88.0583, "type": "Discharge Port", "status": "Draft Restricted (44h wait)", "size": 12}
    ])

    fig_map = go.Figure()

    # Route line
    route_lats = [-21.2833, 2.5000, 20.2644]
    route_lons = [149.3000, 101.5000, 86.6744]
    fig_map.add_trace(go.Scattergeo(
        lat=route_lats, lon=route_lons,
        mode="lines",
        line=dict(width=2, color="#4F86C6", dash="dot"),
        name="Voyage Corridor (Hay Point → Paradip)",
        hoverinfo="skip"
    ))

    # Node markers
    for _, r in map_data.iterrows():
        color = "#2E8B68" if "Normal" in r["status"] or "Clear" in r["status"] else ("#C98226" if "Manageable" in r["status"] or "Queue" in r["status"] else "#B94A4A")
        fig_map.add_trace(go.Scattergeo(
            lat=[r["lat"]], lon=[r["lon"]],
            mode="markers+text",
            marker=dict(size=r["size"], color=color, line=dict(width=1, color="#E9EEF4")),
            text=[r["node"].split()[0]],
            textposition="top center",
            hoverinfo="text",
            hovertext=f"<b>{r['node']}</b><br>Type: {r['type']}<br>Status: {r['status']}",
            showlegend=False
        ))

    fig_map.update_geos(
        showland=True, landcolor="#151E28",
        showocean=True, oceancolor="#0C1017",
        showlakes=False,
        showcountries=True, countrycolor="#293541",
        projection_type="equirectangular",
        center=dict(lat=5.0, lon=115.0),
        projection_scale=2.2
    )

    fig_map.update_layout(
        paper_bgcolor="#101720",
        plot_bgcolor="#101720",
        margin=dict(l=0, r=0, t=10, b=0),
        height=360
    )

    st.plotly_chart(fig_map, use_container_width=True)

with c_map:
    safe_render_section("Control Tower Map", render_control_tower_map)

with c_info:
    st.markdown("#### Port Operational Status & Signal Feed")
    
    # Port Queue Table
    port_status_rows = [
        {"Port": "Paradip (Target)", "Congestion": "64 / 100", "Wait": "39 hrs", "Badge": "D"},
        {"Port": "Visakhapatnam", "Congestion": "48 / 100", "Wait": "26 hrs", "Badge": "D"},
        {"Port": "Haldia / Kolkata", "Congestion": "71 / 100", "Wait": "44 hrs", "Badge": "D"},
        {"Port": "Gangavaram", "Congestion": "32 / 100", "Wait": "18 hrs", "Badge": "D"}
    ]
    st.dataframe(
        pd.DataFrame(port_status_rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Port": st.column_config.TextColumn("Port Node"),
            "Congestion": st.column_config.TextColumn("Congestion Index"),
            "Wait": st.column_config.TextColumn("Avg Wait Time"),
            "Badge": st.column_config.TextColumn("Mode")
        }
    )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Latest Signals Feed")

    st.markdown("""
        <div style="background-color: #151E28; border: 1px solid #293541; border-radius: 4px; padding: 10px; font-size: 0.78rem; display: flex; flex-direction: column; gap: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div><span style="color: #4F86C6; font-weight: 700;">[D]</span> <span style="color: #E9EEF4;">Paradip port queue updated</span></div>
                <span style="color: #71808F;">21:32 IST • DEMO</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #293541; padding-top: 6px;">
                <div><span style="color: #2E8B68; font-weight: 700;">[P]</span> <span style="color: #E9EEF4;">Marine weather risk score refreshed</span></div>
                <span style="color: #71808F;">21:29 IST • PUBLIC LIVE</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #293541; padding-top: 6px;">
                <div><span style="color: #4F86C6; font-weight: 700;">[D]</span> <span style="color: #E9EEF4;">Baltic Panamax freight rate benchmark</span></div>
                <span style="color: #71808F;">21:21 IST • DEMO</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    # Action Controls
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Simulate Disruption", type="primary", use_container_width=True, help="Trigger East Coast port congestion stress scenario"):
            st.session_state["disruption_demo_active"] = True
            st.session_state["freight_shock"] = 12.0
            st.session_state["cong_shock"] = 55.0
            st.session_state["target_port"] = "Paradip"
            st.session_state["avail_shock"] = -30.0
            st.session_state["weather_risk"] = "High"
            st.session_state["geo_risk"] = "Elevated"
            st.rerun()
    with b2:
        if st.button("Reset Baseline", use_container_width=True):
            st.session_state["disruption_demo_active"] = False
            st.session_state["freight_shock"] = 0.0
            st.session_state["cong_shock"] = 0.0
            st.session_state["avail_shock"] = 0.0
            st.session_state["weather_risk"] = "Low"
            st.session_state["geo_risk"] = "Normal"
            st.rerun()
    with b3:
        if st.button("Scenario Lab", use_container_width=True):
            navigate_to(SCENARIO_PAGE)

render_disclaimer()
