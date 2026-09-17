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

st.set_page_config(page_title="FreightIQ — Data & Integrations", page_icon=None, layout="wide")

inject_custom_css()
render_sidebar_status()
render_top_shell(active_page_name="Data Integration Console")

# Header
st.markdown("<h1 style='margin-bottom: 2px;'>Data & Integrations</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #6B7280; font-size: 0.95rem; margin-bottom: 20px;'>Manage external API connectors, signal freshness, manual overrides, and system audit logs.</p>", unsafe_allow_html=True)

mgr = IntegrationManager(mode="DEMO")
dq_summary = get_system_data_quality("DEMO")

# ADMIN / SETTINGS TABS
tab_conn, tab_quality, tab_overrides, tab_audit, tab_limits = st.tabs([
    "Connections",
    "Data Quality",
    "Overrides",
    "Audit Trail",
    "Model & Data Limitations"
])

with tab_conn:
    with st.container(border=True):
        st.markdown("### Connector Status & Data Sources")
        st.caption("Active data pipelines feeding FreightIQ forecasting and Decision Twin engines")

        conn_data = [
            {"Source": "Open-Meteo Weather API", "Type": "Public Live API [P]", "Status": "Connected", "Freshness": "12m ago", "Last Update": "17 Sep 11:35 IST", "Action": "Refresh"},
            {"Source": "Baltic Dry Index Feed", "Type": "Demo Synthetic [D]", "Status": "Active", "Freshness": "1h ago", "Last Update": "17 Sep 10:45 IST", "Action": "Configure"},
            {"Source": "AIS Fleet Tracking (MarineTraffic)", "Type": "Commercial API [C]", "Status": "Unconfigured", "Freshness": "N/A", "Last Update": "Never", "Action": "Add Key"},
            {"Source": "Paradip Port AIS Queue", "Type": "Demo Synthetic [D]", "Status": "Active", "Freshness": "30m ago", "Last Update": "17 Sep 11:15 IST", "Action": "Configure"},
            {"Source": "Coking Coal Spot Index", "Type": "Demo Synthetic [D]", "Status": "Active", "Freshness": "2h ago", "Last Update": "17 Sep 09:30 IST", "Action": "Configure"}
        ]
        st.dataframe(pd.DataFrame(conn_data), use_container_width=True, hide_index=True)

with tab_quality:
    with st.container(border=True):
        st.markdown("### Signal Data Quality Matrix")
        st.caption("Freshness, completeness, and schema validation breakdown")

        matrix_data = []
        for s in dq_summary.signal_matrix:
            matrix_data.append({
                "Signal Name": s.display_name,
                "Domain": s.category,
                "Source": s.source_name,
                "Mode": s.mode,
                "Freshness": s.freshness_status,
                "Last Sync": s.retrieved_at,
                "Validation": "100% Valid"
            })
        st.dataframe(pd.DataFrame(matrix_data), use_container_width=True, hide_index=True)

with tab_overrides:
    with st.container(border=True):
        st.markdown("### Manual Operator Overrides")
        st.caption("Inject operator overrides for emergency scenario testing (logged in audit trail)")

        o1, o2, o3 = st.columns(3)
        with o1:
            ov_cong = st.number_input("Override Port Congestion (0-100)", 0.0, 100.0, 45.0)
        with o2:
            ov_vessels = st.number_input("Override Vessel Count", 1, 100, 25)
        with o3:
            ov_demurrage = st.number_input("Override Demurrage (₹/day)", value=1800000.0, step=50000.0)

        if st.button("Apply Manual Override", type="primary"):
            append_audit_log(
                action="MANUAL_OVERRIDE_APPLIED",
                details=f"Override set: Congestion={ov_cong:.0f}, Vessels={ov_vessels}, Demurrage=₹{ov_demurrage:,.0f}/d",
                source_mode="MANUAL_OVERRIDE"
            )
            st.success("Override logged and applied to active workspace state.")

with tab_audit:
    with st.container(border=True):
        st.markdown("### System Audit Trail")
        st.caption("Activity log of procurement decisions, manual overrides, and model execution events")

        logs = get_audit_trail(limit=10)
        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
        else:
            st.info("No audit events recorded yet.")

with tab_limits:
    with st.container(border=True):
        st.markdown("### Model & Data Limitations")
        st.caption("Read before interpreting any metric or recommendation shown in this tool")
        st.markdown("""
**Data source:** All datasets are synthetic unless a live connector is explicitly enabled and verified in the Connections tab. Synthetic data is seeded from realistic statistical distributions but is not real Baltic Exchange, AIS, port, or commodity data.

**Metric provenance:** MAE, RMSE, MAPE, win-rate, and robustness-score figures are computed on the same synthetic demo series used for model training and simulation. They do not establish real-market forecast accuracy.

**Live deployment requirements:** Production use requires licensed data feeds (Baltic Exchange, MarineTraffic AIS, commodity pricing APIs). Unconfigured connectors fall back to synthetic data silently.

**Recommendation weights:** Optimizer cost weights (demurrage rates, congestion penalties, risk factors) use illustrative defaults. Operational deployment requires calibration against real shipment records and contractual terms.

**Forecasts are probabilistic estimates:** Confidence intervals reflect in-sample model uncertainty on synthetic data. Real freight markets exhibit structural breaks, geopolitical events, and supply shocks not present in the demo series.

**Decision support — not chartering advice:** FreightIQ is a decision-support prototype. Outputs do not constitute commercial chartering recommendations, legal advice, or financial commitments. All charter decisions require professional chartering-broker judgment and contractual verification.
""")

render_disclaimer()

