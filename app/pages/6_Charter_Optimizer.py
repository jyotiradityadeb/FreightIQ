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

st.set_page_config(page_title="FreightIQ — Charter Procurement Workbench", page_icon="⚓", layout="wide")

inject_custom_css()
render_sidebar_status()
render_top_shell(active_page_name="Charter Procurement Workbench")

df = get_cached_processed_data()
today_dt = df["date"].iloc[-1].to_pydatetime()
shipment_ctx = get_active_shipment_context()

# Header
st.markdown("### Procurement Workbench")
st.caption(f"Active Workspace Shipment ID: **{shipment_ctx.get('shipment_id', 'FIQ-2026-0001')}** • Multi-candidate optimization & commercial terms solver")

# 40 / 60 Layout
col_params, col_results = st.columns([0.38, 0.62])

with col_params:
    st.markdown("#### Shipment & Commercial Terms")
    
    with st.container(border=True):
        st.markdown("**CARGO SELECTION**")
        cargo_mode = st.radio("Cargo Mode", ["Commodity Catalogue", "Custom Bulk Cargo"], index=0, horizontal=True)

        if cargo_mode == "Commodity Catalogue":
            commodity_options = [c.display_name for c in COMMODITY_CATALOGUE.values()]
            sel_comm_name = st.selectbox("Select Commodity", commodity_options, index=0)
            
            # Retrieve selected commodity model
            comm_obj = next(c for c in COMMODITY_CATALOGUE.values() if c.display_name == sel_comm_name)
            cargo_type = comm_obj.display_name
            quantity_tonnes = st.number_input("Cargo Quantity (tonnes)", min_value=10000.0, max_value=250000.0, value=float(comm_obj.typical_lot_min), step=5000.0)
            default_laytime = 72.0
            default_demurrage_usd = comm_obj.default_demurrage_rate_usd_day
        else:
            custom_cargo_name = st.text_input("Custom Cargo Name", value="Specialty Sponge Iron")
            quantity_tonnes = st.number_input("Cargo Quantity (tonnes)", min_value=5000.0, max_value=250000.0, value=45000.0, step=5000.0)
            stowage_factor = st.number_input("Stowage Factor (m³/t)", min_value=0.5, max_value=3.0, value=1.2, step=0.1)
            pref_vessel = st.selectbox("Preferred Vessel Class", ["Auto", "Capesize", "Panamax", "Supramax", "Handymax"], index=0)
            demurrage_inr = st.number_input("Demurrage Rate (₹ / day)", value=1800000.0, step=100000.0)
            
            custom_comm = create_custom_commodity(
                cargo_name=custom_cargo_name,
                quantity_tonnes=quantity_tonnes,
                stowage_factor=stowage_factor,
                preferred_vessel_class=pref_vessel,
                demurrage_rate_usd_day=demurrage_inr / 84.0
            )
            cargo_type = custom_comm.display_name
            default_laytime = 72.0
            default_demurrage_usd = custom_comm.default_demurrage_rate_usd_day

        st.markdown("---")
        st.markdown("**VOYAGE ROUTE**")
        origin_ports = list(dict.fromkeys([p.country for p in PORT_MASTER.values() if p.country != "India"]))
        origin = st.selectbox("Origin Region / Port", origin_ports, index=0)

        dest_ports = [p.port_id for p in PORT_MASTER.values() if p.country == "India"]
        destination = st.selectbox("Destination Port (India East Coast)", dest_ports, index=0)

        st.markdown("---")
        st.markdown("**CHARTER TIMING & CONSTRAINTS**")
        earliest_date = st.date_input("Earliest Charter Date", value=today_dt + timedelta(days=1))
        latest_date = st.date_input("Latest Charter Date", value=today_dt + timedelta(days=15))

        vessel_options = ["Auto"] + list(VESSEL_MASTER.keys())
        vessel_class = st.selectbox("Vessel Class Constraint", vessel_options, index=0)
        risk_preference = st.selectbox("Risk Preference", ["Low", "Balanced", "Flexible"], index=1)

        use_custom_dem = st.checkbox("Override Demurrage Rate")
        demurrage_rate_usd = default_demurrage_usd
        if use_custom_dem:
            dem_inr_input = st.number_input("Custom Demurrage Rate (₹ / day)", value=round(default_demurrage_usd * 84.0, 0), step=50000.0)
            demurrage_rate_usd = dem_inr_input / 84.0

        st.markdown("---")
        run_opt = st.button("Evaluate Charter Options", type="primary", use_container_width=True)

        # Sync active shipment context
        update_active_shipment_context(
            cargo_type=cargo_type,
            quantity_tonnes=quantity_tonnes,
            origin=origin,
            destination=destination,
            vessel_class=vessel_class,
            demurrage_rate=demurrage_rate_usd
        )

with col_results:
    st.markdown("#### Optimal Charter Recommendation")

    # Run Forecasting Engine for 30 days
    fc_res = generate_freight_forecast(df, horizon=30, selected_model="Auto")
    
    risk_map = {"Low": "Low", "Balanced": "Medium", "Flexible": "High"}

    opt_res = optimize_charter_timing(
        forecast_df=fc_res["forecast_df"],
        cargo_type=cargo_type,
        quantity_tonnes=quantity_tonnes,
        origin=origin,
        destination=destination,
        earliest_date=earliest_date.strftime("%Y-%m-%d"),
        latest_date=latest_date.strftime("%Y-%m-%d"),
        vessel_class=vessel_class,
        demurrage_rate=demurrage_rate_usd,
        risk_tolerance=risk_map.get(risk_preference, "Medium")
    )

    if opt_res["success"]:
        rec = opt_res["recommendation"]
        
        # Save snapshot & Log Decision Version
        save_shipment(shipment_ctx)
        log_decision_version(shipment_ctx.get("shipment_id", "FIQ-2026-0001"), rec)

        # Render Recommendation Panel
        safe_render_section("Charter Recommendation Panel", lambda: render_charter_recommendation_panel(rec))

        st.markdown("<br>", unsafe_allow_html=True)

        # Render Route Visualization Card
        safe_render_section("Route Visualization", lambda: render_route_visualization_card(origin, destination))

        st.markdown("<br>", unsafe_allow_html=True)

        # Render Scenario Comparison Table
        safe_render_section("Scenario Comparison", lambda: render_scenario_comparison_table(opt_res["scenarios"]))

        st.markdown("<br>", unsafe_allow_html=True)

        # Ranked Candidate Matrix Table
        st.markdown("#### Ranked Feasible Candidate Matrix")
        cand_list = opt_res.get("all_evaluated_candidates", [])
        if cand_list:
            display_limit = st.radio("Show Candidates", ["Top 5 Candidates", "All Feasible Candidates"], index=0, horizontal=True)
            limit_n = 5 if "5" in display_limit else len(cand_list)

            matrix_rows = []
            for idx, c in enumerate(cand_list[:limit_n], start=1):
                c_cost_inr = usd_to_inr(c["total_logistics_cost_usd"])
                c_f_inr = usd_to_inr(c["freight_cost_usd"])
                matrix_rows.append({
                    "Rank": f"#{idx}",
                    "Charter Date": c["charter_date"],
                    "Vessel": c["vessel_class"],
                    "Port": c["destination"],
                    "Unit Freight": f"{format_inr(usd_to_inr(c['unit_freight_usd_per_tonne']))} / t",
                    "Freight Cost": format_inr(c_f_inr),
                    "Demurrage Exposure": format_inr(usd_to_inr(c["demurrage_cost_usd"])),
                    "Expected Logistics Cost": format_inr(c_cost_inr),
                    "Status": "Optimal" if idx == 1 else "Feasible Alternative"
                })

            st.dataframe(pd.DataFrame(matrix_rows), use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # PDF Decision Report Export & Navigation Shortcuts
        c_pdf, c_nav1, c_nav2 = st.columns([0.5, 0.25, 0.25])
        with c_pdf:
            pdf_bytes = generate_charter_decision_pdf(recommendation=rec, data_mode="DEMO")
            st.download_button(
                label="📄 Generate Decision Report (PDF)",
                data=pdf_bytes,
                file_name=f"FreightIQ_Decision_Report_{datetime.now().strftime('%Y-%m-%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with c_nav1:
            if st.button("Open Decision Twin", use_container_width=True):
                navigate_to(DECISION_TWIN_PAGE)
        with c_nav2:
            if st.button("Open Scenario Lab", use_container_width=True):
                navigate_to(SCENARIO_PAGE)

    else:
        st.warning("⚠ Optimization Infeasible: No feasible charter option found for the selected constraints.")
        if "infeasibility_reasons" in opt_res:
            for r in opt_res["infeasibility_reasons"]:
                st.info(f"• {r}")

render_disclaimer()
