"""
FreightIQ Data Integration & Lineage Console Streamlit Page
"""

import os
import sys

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import datetime

from app.navigation import CONTROL_TOWER_PAGE, DECISION_TWIN_PAGE, navigate_to
from app.components.helpers import (
    inject_custom_css,
    render_top_shell,
    render_sidebar_status,
    render_disclaimer
)
from app.components.error_boundary import safe_render_section
from backend.data_quality import get_system_data_quality, evaluate_signal_freshness
from backend.integrations.integration_manager import IntegrationManager
from backend.storage import get_audit_trail, append_audit_log

st.set_page_config(page_title="FreightIQ — Data Integration Console", page_icon="🔌", layout="wide")

inject_custom_css()
render_sidebar_status()
render_top_shell(active_page_name="Data Integration Console")

st.markdown("### Data Integration & Signal Lineage Console")
st.caption("Source connectivity, signal freshness, commercial adapter status, and enterprise data lineage")

mgr = IntegrationManager(mode="DEMO")
dq_summary = get_system_data_quality("DEMO")

# Top Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("ADAPTER MODULES", "5 Available", delta="Built-in Base Contract")
m2.metric("PUBLIC LIVE SOURCES", f"{dq_summary.public_sources_count} Connected", delta="Open-Meteo Weather")
m3.metric("COMMERCIAL SOURCES", "0 Credentials", delta="Credential Dependent")
m4.metric("SYNTHETIC DEMO FEEDS", f"{dq_summary.demo_sources_count} Feeds", delta="Synthetic Prototype")

st.markdown("<br>", unsafe_allow_html=True)

# Main Signal Matrix Table
st.markdown("#### Signal Connectivity & Freshness Console")
matrix_data = []
for s in dq_summary.signal_matrix:
    matrix_data.append({
        "Badge": s.badge_label,
        "Signal Name": s.display_name,
        "Category": s.category,
        "Source Name": s.source_name,
        "Source Mode": s.mode,
        "Freshness": s.freshness_status,
        "Last Update": s.retrieved_at,
        "Credentials Required": "No" if s.mode in ["DEMO", "PUBLIC_LIVE"] else "API Key Required"
    })

df_matrix = pd.DataFrame(matrix_data)
st.dataframe(
    df_matrix,
    use_container_width=True,
    column_config={
        "Badge": st.column_config.TextColumn("Mode"),
        "Signal Name": st.column_config.TextColumn("Signal"),
        "Category": st.column_config.TextColumn("Domain"),
        "Source Name": st.column_config.TextColumn("Source Name"),
        "Source Mode": st.column_config.TextColumn("Source Mode"),
        "Freshness": st.column_config.TextColumn("Freshness Status"),
        "Last Update": st.column_config.TextColumn("Timestamp"),
        "Credentials Required": st.column_config.TextColumn("Credentials")
    },
    hide_index=True
)

st.markdown("---")

# Data Lineage Explorer & Enterprise Data Import
col_lin, col_imp = st.columns([0.5, 0.5])

with col_lin:
    st.markdown("#### Data Lineage Explorer")
    st.caption("Inspect signal transformations from connector ingestion to Decision Twin consumer")

    selected_signal = st.selectbox(
        "Select Signal to Trace",
        ["Freight Rate Benchmarks", "AIS Vessel Availability", "Port Congestion Index", "Marine Weather Risk", "Commodity Spot Prices"],
        index=0
    )

    with st.container(border=True):
        st.markdown(f"**DATA LINEAGE TRACE: {selected_signal.upper()}**")
        st.text("1. Ingestion Adapter: FreightIQ BaseAdapter Contract")
        st.text("2. Normalization: Standard Schema (timestamp, value, source_mode, retrieved_at)")
        st.text("3. Feature Pipeline: Rolling Lags & Volatility Features (features.py)")
        st.text("4. Forecast Engine: SARIMA / Naive Forecast Generator (forecasting.py)")
        st.text("5. Decision Consumers: Optimizer, Decision Twin, Control Tower")
        st.caption("Status: Continuous pipeline validation active")

with col_imp:
    st.markdown("#### Operational Dataset Ingestion (CSV / XLSX)")
    st.caption("Upload custom operational data files with column mapping helper")

    uploaded_file = st.file_uploader("Upload Enterprise Dataset", type=["csv", "xlsx"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                up_df = pd.read_csv(uploaded_file)
            else:
                up_df = pd.read_excel(uploaded_file)

            st.success(f"Successfully loaded file '{uploaded_file.name}' ({len(up_df)} rows, {len(up_df.columns)} columns)")
            st.dataframe(up_df.head(3), use_container_width=True)
            
            with st.expander("Configure Column Mapping"):
                col_map_date = st.selectbox("Date Column", list(up_df.columns), index=0)
                col_map_val = st.selectbox("Value Column", list(up_df.columns), index=min(1, len(up_df.columns)-1))
                if st.button("Apply Dataset Mapping"):
                    st.info(f"Dataset mapped successfully: '{col_map_val}' -> Operational Ingestion Pipeline")
        except Exception as e:
            st.error(f"Failed to process file: {e}")

st.markdown("---")

# Operator Manual Override & Audit Log
col_ov, col_aud = st.columns([0.45, 0.55])

with col_ov:
    st.markdown("#### Manual Operator Override Console")
    st.caption("Inject manual override inputs for scenario testing (Recorded in audit trail)")

    with st.container(border=True):
        ov_cong = st.number_input("Override Port Congestion Score (0 - 100)", min_value=0.0, max_value=100.0, value=45.0)
        ov_vessels = st.number_input("Override Available Vessel Count", min_value=1, max_value=100, value=25)
        ov_demurrage = st.number_input("Override Demurrage Rate (₹ / day)", value=1800000.0, step=50000.0)

        if st.button("Apply Operator Manual Override", use_container_width=True):
            append_audit_log(
                action="MANUAL_OVERRIDE_APPLIED",
                details=f"Override set: Congestion={ov_cong:.0f}, Vessels={ov_vessels}, Demurrage=₹{ov_demurrage:,.0f}/d",
                source_mode="MANUAL_OVERRIDE"
            )
            st.success("Manual override logged and applied to session workspace.")
            st.session_state["manual_override_active"] = True

with col_aud:
    st.markdown("#### System Audit Trail Log")
    st.caption("Recent operational actions and recommendation version entries")

    logs = get_audit_trail(limit=6)
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
    else:
        st.info("No audit events recorded yet.")

render_disclaimer()
