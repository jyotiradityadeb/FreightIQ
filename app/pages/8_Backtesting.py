"""
FreightIQ Streamlit Page 4: Historical-Style Simulation Backtest on Synthetic Demo Data
"""

import os
import sys

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd

from app.components.helpers import (
    inject_custom_css,
    render_top_shell,
    render_sidebar_status,
    render_disclaimer,
    get_cached_processed_data,
    usd_to_inr,
    format_inr,
    get_active_shipment_context
)
from app.components.cards import render_forecast_interpretation_box
from app.components.charts import (
    plot_backtest_cost_comparison,
    plot_cumulative_simulated_savings
)
from backend.domain.routes import get_calibrated_routes, resolve_route
from backend.route_market import get_route_market_history
from backend.backtesting import run_historical_simulation


st.set_page_config(page_title="FreightIQ — Simulation Backtest", page_icon=None, layout="wide")

inject_custom_css()
render_sidebar_status()
render_top_shell(active_page_name="Simulation Backtest")

shipment_ctx = get_active_shipment_context()
calibrated_routes = get_calibrated_routes()
route_display_labels = [r["display_label"] for r in calibrated_routes]

active_o_pid = shipment_ctx.get("origin_port_id", shipment_ctx.get("origin", "AU_HPT"))
active_d_pid = shipment_ctx.get("destination_port_id", shipment_ctx.get("destination", "IN_PDP"))
active_res = resolve_route(active_o_pid, active_d_pid)

default_idx = 0
if active_res.is_calibrated:
    for idx, r_dict in enumerate(calibrated_routes):
        if r_dict["origin_port_id"] == active_res.origin_port_id and r_dict["destination_port_id"] == active_res.destination_port_id:
            default_idx = idx
            break

# Header
st.markdown("<h1 style='margin-bottom: 2px;'>Simulation Backtest</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #6B7280; font-size: 0.95rem; margin-bottom: 20px;'>Historical-style simulation on synthetic route-specific data against an immediate-charter benchmark strategy.</p>", unsafe_allow_html=True)

import time

with st.container(border=True):
    r_col1, r_col2 = st.columns([2, 2])
    with r_col1:
        selected_route_label = st.selectbox("Simulation Route", route_display_labels, index=default_idx)
        selected_route_dict = calibrated_routes[route_display_labels.index(selected_route_label)]
        selected_route_key = selected_route_dict["route_key"]
    with r_col2:
        st.caption("ROUTE DATA MODE")
        st.markdown("<span style='background-color: #DEF7EC; color: #03543F; font-size: 0.85rem; font-weight: 600; padding: 4px 10px; border-radius: 4px;'>🟢 SYNTHETIC ROUTE-SPECIFIC DEMO SERIES</span>", unsafe_allow_html=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    b_c1, b_c2, b_c3, b_c4 = st.columns(4)

    route_df = get_route_market_history(selected_route_key)
    min_d = route_df["date"].min().to_pydatetime()
    max_d = route_df["date"].max().to_pydatetime()

    with b_c1:
        sim_start = st.date_input("Simulation Start Date", value=pd.to_datetime("2024-06-01"))
    with b_c2:
        sim_end = st.date_input("Simulation End Date", value=max_d - pd.Timedelta(days=30))
    with b_c3:
        horizon = st.select_slider("Forecast Horizon", options=[7, 14, 30], value=14)
    with b_c4:
        step_days = st.selectbox("Interval Days", [7, 14, 21, 30], index=1)

    run_sim = st.button("Run Simulation Backtest", type="primary", use_container_width=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

cache_key = f"backtest_{selected_route_key}_{sim_start}_{sim_end}_{horizon}_{step_days}"

# Cache / Gate Backtest Execution
if run_sim or cache_key not in st.session_state:
    with st.spinner("Executing walk-forward historical simulation across decision windows..."):
        t0 = time.time()
        sim_res = run_historical_simulation(
            df=route_df,
            start_date=sim_start.strftime("%Y-%m-%d"),
            end_date=sim_end.strftime("%Y-%m-%d"),
            horizon=horizon,
            step_days=step_days,
            cargo_type=shipment_ctx.get("cargo_type", "Coking Coal"),
            origin=selected_route_dict["origin_name"],
            destination=selected_route_dict["destination_name"],
            vessel_class="Panamax"
        )
        sim_res["elapsed_seconds"] = time.time() - t0
        st.session_state[cache_key] = sim_res

sim_res = st.session_state[cache_key]

if sim_res.get("success"):
    sim_diff_inr = usd_to_inr(sim_res["simulated_cost_difference_total"])
    _fam = sim_res["forecast_accuracy_metrics"]
    mae_inr = usd_to_inr(_fam["MAE"]) if _fam.get("MAE") is not None else None
    elapsed_sec = sim_res.get("elapsed_seconds", 0.0)

    st.caption(f"✓ Simulation completed in {elapsed_sec:.2f} seconds")

    with st.container(border=True):
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.caption("DECISION WINDOWS")
            st.markdown(f"### {sim_res['test_periods_count']}")
            st.caption("Simulated decision points on demo data")

        with k2:
            st.caption("SIMULATED WIN RATE (DEMO DATA)")
            st.markdown(f"<h3 style='color: #10B981;'>{sim_res['win_rate_percentage']:.1f}%</h3>", unsafe_allow_html=True)
            st.caption(f"{sim_res['win_count']} of {sim_res['test_periods_count']} simulated windows (synthetic series)")

        with k3:
            st.caption("SIMULATED COST DIFFERENCE")
            st.markdown(f"<h3 style='color: #10B981;'>{format_inr(sim_diff_inr)}</h3>", unsafe_allow_html=True)
            st.caption(f"{sim_res['simulated_savings_percentage']:+.2f}% vs immediate charter (synthetic sim)")

        with k4:
            st.caption("FORECAST MAE (DEMO SERIES)")
            if mae_inr is not None:
                st.markdown(f"### {format_inr(mae_inr)} / t")
            else:
                _av = _fam.get("available_observations", "?")
                _rq = _fam.get("minimum_required_observations", "?")
                st.markdown(f"Validation unavailable — insufficient historical observations (available: {_av}, required: {_rq})")
            st.caption("Demo-series walk-forward error")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    render_forecast_interpretation_box(
        title="Simulation Backtest Interpretation",
        text=f"On synthetic demo data, FreightIQ recommendations matched or outperformed the immediate-charter benchmark in {sim_res['win_count']} of {sim_res['test_periods_count']} simulated decision windows ({sim_res['win_rate_percentage']}% simulated win rate), resulting in a simulated cost difference of {format_inr(sim_diff_inr)}. These results are on synthetic data and do not reflect real-market performance."
    )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Charts
    res_df = pd.DataFrame(sim_res["period_results_table"])

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("### Cost Comparison per Decision Period")
            fig_bar = plot_backtest_cost_comparison(res_df)
            st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        with st.container(border=True):
            st.markdown("### Cumulative Cost Difference")
            fig_cum = plot_cumulative_simulated_savings(res_df)
            st.plotly_chart(fig_cum, use_container_width=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Table
    with st.container(border=True):
        st.markdown("### Decision Outcomes Matrix")
        table_rows = []
        for r in sim_res["period_results_table"]:
            b_inr = usd_to_inr(r["benchmark_simulated_cost"])
            f_inr = usd_to_inr(r["freightiq_simulated_cost"])
            d_inr = usd_to_inr(r["simulated_cost_difference"])
            table_rows.append({
                "Decision Date": r["decision_date"],
                "Recommended Date": r["recommended_charter_date"],
                "Benchmark Cost": format_inr(b_inr),
                "FreightIQ Cost": format_inr(f_inr),
                "Simulated Difference": format_inr(d_inr),
                "Status": r["simulated_savings_status"]
            })

        st.dataframe(table_rows, use_container_width=True, hide_index=True)

else:
    st.error(f"Simulation Error: {sim_res.get('error')}")


render_disclaimer()

