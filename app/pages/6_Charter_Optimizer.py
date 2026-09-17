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
from backend.sensitivity import run_sensitivity_analysis
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
        destination = st.selectbox("Destination Port", ["Paradip", "Visakhapatnam", "Kolkata/Haldia"], index=0)
    with t5:
        laycan_input = st.date_input("Laycan Window", value=[today_dt + timedelta(days=1), today_dt + timedelta(days=15)])
        if isinstance(laycan_input, (list, tuple)) and len(laycan_input) == 2:
            e_dt, l_dt = laycan_input[0], laycan_input[1]
        elif isinstance(laycan_input, (list, tuple)) and len(laycan_input) == 1:
            e_dt = laycan_input[0]
            l_dt = e_dt + timedelta(days=14)
        else:
            e_dt = laycan_input if hasattr(laycan_input, "strftime") else today_dt + timedelta(days=1)
            l_dt = e_dt + timedelta(days=14)
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

# Input hash for caching candidate solutions
current_inputs_key = f"{cargo_type}_{quantity_tonnes}_{origin}_{destination}_{e_dt}_{l_dt}"

# Check active scenario in session state
active_scenario = st.session_state.get("active_scenario", {})
scenario_cost_overrides = None
if active_scenario.get("is_active"):
    scenario_cost_overrides = {
        "demurrage_factor": 0.15 * (1.0 + active_scenario.get("demurrage_pct", 0.0) / 100.0),
        "congestion_multiplier": 0.5 * (1.0 + active_scenario.get("congestion_pct", 0.0) / 100.0),
    }

if run_opt or "optimizer_result" not in st.session_state or st.session_state.get("opt_inputs_key") != current_inputs_key:
    fc_res = generate_freight_forecast(df, horizon=30, selected_model="Auto")
    st.session_state["opt_forecast_df"] = fc_res["forecast_df"]
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
        risk_tolerance="Medium",
        cost_factor_overrides=scenario_cost_overrides,
    )
    st.session_state["optimizer_result"] = opt_res
    st.session_state["opt_inputs_key"] = current_inputs_key

    if opt_res["success"]:
        rec = opt_res["recommendation"]
        save_shipment(shipment_ctx)
        log_decision_version(shipment_ctx.get("shipment_id", "FIQ-2026-0001"), rec, reason="Solver Execution")
else:
    opt_res = st.session_state["optimizer_result"]

if opt_res["success"]:
    rec = opt_res["recommendation"]

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

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ── COST MODEL TRANSPARENCY ──────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("### Cost Model Breakdown — Top Candidates")
        st.caption(
            "Exact cost components computed by the optimizer for each candidate. "
            "Formula: Total = Freight + Demurrage + Congestion + Route Risk Penalty"
        )
        breakdown_rows = []
        for idx, c in enumerate(cand_list[:6], start=1):
            breakdown_rows.append({
                "Rank": f"#{idx}",
                "Vessel / Date": f"{c['vessel_class']} · {c['charter_date']}",
                "Freight (₹)": format_inr(usd_to_inr(c["freight_cost_usd"])),
                "Demurrage (₹)": format_inr(usd_to_inr(c["demurrage_cost_usd"])),
                "Congestion (₹)": format_inr(usd_to_inr(c["congestion_cost_usd"])),
                "Risk Adj. (₹)": format_inr(usd_to_inr(c["route_risk_penalty_usd"])),
                "Total (₹)": format_inr(usd_to_inr(c["total_logistics_cost_usd"])),
                "₹/t": f"₹{usd_to_inr(c['effective_cost_per_tonne']):,.0f}",
            })
        st.dataframe(pd.DataFrame(breakdown_rows), use_container_width=True, hide_index=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ── OPTIMIZER EXPLAINABILITY ─────────────────────────────────────────────
    expl = opt_res.get("explainability", {})
    if expl:
        with st.container(border=True):
            st.markdown("### Why This Recommendation Was Selected")
            st.caption("Derived from computed candidate costs — not generic boilerplate")

            winner = expl.get("winner", {})
            if winner:
                ex_c1, ex_c2 = st.columns(2)
                with ex_c1:
                    st.markdown(f"**Selected:** {winner['candidate']}")
                    for reason in winner.get("why_won", []):
                        st.markdown(f"- {reason}")
                with ex_c2:
                    bd = winner.get("cost_breakdown_usd", {})
                    total = winner.get("total_cost_usd", 1)
                    breakdown_items = [
                        {"Component": "Freight", "USD": f"${bd.get('freight', 0):,.0f}", "Share": f"{bd.get('freight', 0)/total*100:.1f}%"},
                        {"Component": "Demurrage", "USD": f"${bd.get('demurrage', 0):,.0f}", "Share": f"{bd.get('demurrage', 0)/total*100:.1f}%"},
                        {"Component": "Congestion", "USD": f"${bd.get('congestion', 0):,.0f}", "Share": f"{bd.get('congestion', 0)/total*100:.1f}%"},
                        {"Component": "Risk Penalty", "USD": f"${bd.get('risk_penalty', 0):,.0f}", "Share": f"{bd.get('risk_penalty', 0)/total*100:.1f}%"},
                    ]
                    st.dataframe(pd.DataFrame(breakdown_items), use_container_width=True, hide_index=True)

            alts = expl.get("alternatives", [])
            if alts:
                st.markdown("**Why alternatives were ranked lower:**")
                for alt in alts:
                    delta_inr = format_inr(usd_to_inr(alt["delta_vs_winner_usd"]))
                    with st.expander(
                        f"{alt['candidate']} — total ${alt['total_cost_usd']:,.0f} "
                        f"(+{delta_inr} vs selected)"
                    ):
                        for r in alt["loss_reasons"]:
                            st.markdown(f"- {r}")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # ── ASSUMPTION SENSITIVITY / ROBUSTNESS PANEL ────────────────────────────
    with st.container(border=True):
        st.markdown("### Assumption Sensitivity — Robustness Panel")
        st.caption(
            "Each key cost assumption is perturbed ±15% and ±30% (one at a time) and "
            "the optimizer re-run. 'Held' = same vessel and charter date as baseline. "
            "Computed on synthetic demo series — not real-market robustness."
        )

        sens_res = run_sensitivity_analysis(
            forecast_df=st.session_state.get("opt_forecast_df", df),
            cargo_type=cargo_type,
            quantity_tonnes=quantity_tonnes,
            origin=origin,
            destination=destination,
            risk_tolerance="Medium",
            demurrage_rate=22000.0,
            earliest_date=e_dt.strftime("%Y-%m-%d"),
            latest_date=l_dt.strftime("%Y-%m-%d"),
        )

        if sens_res["success"]:
            st.markdown(
                f"**Overall stability:** {sens_res['stability_summary']} "
                f"(demo data)"
            )

            sens_rows = []
            for pr in sens_res["param_results"]:
                sens_rows.append({
                    "Assumption": pr["parameter_label"],
                    "Baseline Value": pr["baseline_value"],
                    "Range Tested": f"{pr['baseline_value']*0.7:.4g} – {pr['baseline_value']*1.3:.4g}",
                    "Held / Tested": f"{pr['stable_count']} / {pr['tested_count']}",
                    "Stable Across ±30%": "Yes" if pr["holds_across_range"] else "No",
                    "First Flip At": pr["first_flip_at"] if pr["first_flip_at"] else "—",
                })
            st.dataframe(pd.DataFrame(sens_rows), use_container_width=True, hide_index=True)

            # Per-assumption drill-down
            with st.expander("Detailed perturbation results"):
                for pr in sens_res["param_results"]:
                    st.markdown(f"**{pr['parameter_label']}** ({pr['unit']})")
                    detail_rows = []
                    for lv in pr["levels"]:
                        detail_rows.append({
                            "Perturbation": f"{lv['perturbation_pct']:+.0f}%",
                            "Value": f"{lv['perturbed_value']:.4g}",
                            "Vessel": lv["recommended_vessel"] or "—",
                            "Date": lv["recommended_date"] or "—",
                            "Total Cost (₹)": format_inr(usd_to_inr(lv["total_cost_usd"])) if lv["total_cost_usd"] else "—",
                            "Held": "Yes" if lv["recommendation_held"] else ("—" if lv["perturbation_pct"] == 0 else "No"),
                        })
                    st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)
                    st.markdown("")
        else:
            st.warning("Sensitivity analysis could not be computed for this configuration.")

else:
    st.warning("⚠ Optimization Infeasible: No feasible charter option found for the selected constraints.")
    if "infeasibility_reasons" in opt_res:
        for r in opt_res["infeasibility_reasons"]:
            st.info(f"• {r}")

render_disclaimer()

