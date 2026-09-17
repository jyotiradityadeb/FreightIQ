"""
FreightIQ Charter Procurement Workbench Streamlit Page
"""

import os
import sys

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from app.navigation import CONTROL_TOWER_PAGE, DECISION_TWIN_PAGE, SCENARIO_PAGE, navigate_to
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
from app.components.cards import (
    render_charter_recommendation_panel,
    render_scenario_comparison_table,
    render_route_visualization_card
)
from app.components.error_boundary import safe_render_section
from backend.domain.commodities import COMMODITY_CATALOGUE, create_custom_commodity
from backend.domain.vessels import VESSEL_MASTER
from backend.domain.ports import PORT_MASTER
from backend.domain.routes import ROUTE_MASTER, get_route_info
from backend.forecasting import generate_freight_forecast
from backend.optimizer import optimize_charter_timing
from backend.reporting import generate_charter_decision_pdf
from backend.storage import save_shipment, log_decision_version

st.set_page_config(page_title="FreightIQ — Charter Workbench", page_icon=None, layout="wide")

inject_custom_css()
render_sidebar_status()
render_top_shell(active_page_name="Charter Workbench")

df = get_cached_processed_data()
today_dt = df["date"].iloc[-1].to_pydatetime()
shipment_ctx = get_active_shipment_context()

# Header
st.markdown("<h1 style='margin-bottom: 2px;'>Charter Workbench</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color: #6B7280; font-size: 0.95rem; margin-bottom: 20px;'>Commercial procurement solver for active shipment <strong class='fiq-mono'>{shipment_ctx.get('shipment_id', 'FIQ-2026-0001')}</strong></p>", unsafe_allow_html=True)

# TOP PROCUREMENT TOOLBAR (Clean SaaS Card Surface)
with st.container(border=True):
    t1, t2, t3, t4, t5, t6 = st.columns([1.5, 1.2, 1.2, 1.2, 1.5, 1])
    
    with t1:
        cargo_type = st.selectbox("Cargo", ["Coking Coal", "Iron Ore Fines", "Thermal Coal", "Specialty Sponge Iron"], index=0)
    with t2:
        quantity_tonnes = st.number_input("Quantity (t)", min_value=10000.0, max_value=250000.0, value=75000.0, step=5000.0)
    with t3:
        origin = st.selectbox("Origin Port", ["Australia", "Indonesia", "South Africa"], index=0)
    with t4:
        destination = st.selectbox("Destination Port", ["Paradip", "Visakhapatnam", "Haldia", "Gangavaram"], index=0)
    with t5:
        earliest_date = st.date_input("Laycan Window", value=[today_dt + timedelta(days=1), today_dt + timedelta(days=15)])
        if isinstance(earliest_date, list) and len(earliest_date) == 2:
            e_dt, l_dt = earliest_date
        else:
            e_dt, l_dt = today_dt + timedelta(days=1), today_dt + timedelta(days=15)
    with t6:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        run_opt = st.button("Solve Candidates", type="primary", use_container_width=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# Sync active shipment context
update_active_shipment_context(
    cargo_type=cargo_type,
    quantity_tonnes=quantity_tonnes,
    origin=origin,
    destination=destination
)

# Run Forecasting Engine & Optimizer
fc_res = generate_freight_forecast(df, horizon=30, selected_model="Auto")
opt_res = optimize_charter_timing(
    forecast_df=fc_res["forecast_df"],
    cargo_type=cargo_type,
    quantity_tonnes=quantity_tonnes,
    origin=origin,
    destination=destination,
    earliest_date=e_dt.strftime("%Y-%m-%d"),
    latest_date=l_dt.strftime("%Y-%m-%d"),
    vessel_class="Auto",
    demurrage_rate=22000.0,
    risk_tolerance="Medium"
)

if opt_res["success"]:
    rec = opt_res["recommendation"]
    save_shipment(shipment_ctx)
    log_decision_version(shipment_ctx.get("shipment_id", "FIQ-2026-0001"), rec)

    # MAIN SECTION: CANDIDATE PROCUREMENT TABLE
    with st.container(border=True):
        top_l, top_r = st.columns([2, 1])
        with top_l:
            st.markdown("### Feasible Charter Candidate Matrix")
            st.caption("Ranked commercial options evaluated across predicted freight, port queue demurrage, and route risk")
        with top_r:
            pdf_bytes = generate_charter_decision_pdf(recommendation=rec, data_mode="DEMO")
            st.download_button(
                label="Download Procurement Report (PDF)",
                data=pdf_bytes,
                file_name=f"FreightIQ_Charter_Decision_{datetime.now().strftime('%Y-%m-%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        cand_list = opt_res.get("all_evaluated_candidates", [])
        if cand_list:
            matrix_rows = []
            for idx, c in enumerate(cand_list[:8], start=1):
                c_cost_inr = usd_to_inr(c["total_logistics_cost_usd"])
                c_f_inr = usd_to_inr(c["freight_cost_usd"])
                unit_inr = usd_to_inr(c["unit_freight_usd_per_tonne"])
                status_label = "Recommended" if idx == 1 else "Feasible"
                
                matrix_rows.append({
                    "Rank": f"#{idx}",
                    "Vessel": c["vessel_class"],
                    "Laycan Window": c["charter_date"],
                    "Route": f"{origin} → {destination}",
                    "Freight Rate (₹/t)": f"₹{unit_inr:,.0f} / t",
                    "Expected Logistics Cost": format_inr(c_cost_inr),
                    "Risk": "Low" if idx == 1 else "Moderate",
                    "Status": status_label
                })

            st.dataframe(pd.DataFrame(matrix_rows), use_container_width=True, hide_index=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # LOWER SECTION: RECOMMENDATION DETAILS & ROUTE SPECS
    c_left, c_right = st.columns([1.2, 1])
    with c_left:
        safe_render_section("Charter Recommendation Panel", lambda: render_charter_recommendation_panel(rec))
    with c_right:
        safe_render_section("Route Visualization", lambda: render_route_visualization_card(origin, destination))
        safe_render_section("Scenario Comparison", lambda: render_scenario_comparison_table(opt_res["scenarios"]))

else:
    st.warning("⚠ Optimization Infeasible: No feasible charter option found for the selected constraints.")
    if "infeasibility_reasons" in opt_res:
        for r in opt_res["infeasibility_reasons"]:
            st.info(f"• {r}")

render_disclaimer()

