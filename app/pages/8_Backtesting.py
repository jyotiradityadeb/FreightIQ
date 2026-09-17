"""
FreightIQ Streamlit Page 4: Historical Validation
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
    format_inr
)
from app.components.cards import render_forecast_interpretation_box
from app.components.charts import (
    plot_backtest_cost_comparison,
    plot_cumulative_simulated_savings
)
from backend.backtesting import run_historical_simulation


st.set_page_config(page_title="FreightIQ — Historical Validation", page_icon=None, layout="wide")

inject_custom_css()
render_sidebar_status()
render_top_shell(active_page_name="Historical Validation")


df = get_cached_processed_data()

# Header
st.markdown("<h1 style='margin-bottom: 2px;'>Historical Validation</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #6B7280; font-size: 0.95rem; margin-bottom: 20px;'>Walk-forward simulation against immediate-charter benchmark strategy.</p>", unsafe_allow_html=True)

with st.expander("⚙ Simulation Window & Model Parameters", expanded=False):
    b_c1, b_c2, b_c3, b_c4 = st.columns(4)

    min_d = df["date"].min().to_pydatetime()
    max_d = df["date"].max().to_pydatetime()

    with b_c1:
        sim_start = st.date_input("Simulation Start Date", value=pd.to_datetime("2024-06-01"))
    with b_c2:
        sim_end = st.date_input("Simulation End Date", value=max_d - pd.Timedelta(days=30))
    with b_c3:
        horizon = st.select_slider("Forecast Horizon", options=[7, 14, 30], value=14)
    with b_c4:
        step_days = st.selectbox("Interval Days", [7, 14, 21, 30], index=1)

    run_sim = st.button("Re-run Historical Simulation", type="primary", use_container_width=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# Run Simulation
sim_res = run_historical_simulation(
    df=df,
    start_date=sim_start.strftime("%Y-%m-%d"),
    end_date=sim_end.strftime("%Y-%m-%d"),
    horizon=horizon,
    step_days=step_days,
    cargo_type="Coking Coal",
    vessel_class="Panamax"
)

if sim_res["success"]:
    sim_diff_inr = usd_to_inr(sim_res["simulated_cost_difference_total"])
    mae_inr = usd_to_inr(sim_res["forecast_accuracy_metrics"]["MAE"])

    with st.container(border=True):
        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.caption("DECISION WINDOWS")
            st.markdown(f"### {sim_res['test_periods_count']}")
            st.caption("Historical decision points")

        with k2:
            st.caption("WIN RATE")
            st.markdown(f"<h3 style='color: #10B981;'>{sim_res['win_rate_percentage']:.1f}%</h3>", unsafe_allow_html=True)
            st.caption(f"{sim_res['win_count']} of {sim_res['test_periods_count']} windows")

        with k3:
            st.caption("SIMULATED COST DIFFERENCE")
            st.markdown(f"<h3 style='color: #10B981;'>{format_inr(sim_diff_inr)}</h3>", unsafe_allow_html=True)
            st.caption(f"{sim_res['simulated_savings_percentage']:+.2f}% vs Immediate Charter")

        with k4:
            st.caption("FORECAST MAE")
            st.markdown(f"### {format_inr(mae_inr)} / t")
            st.caption("Walk-forward forecast error")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    render_forecast_interpretation_box(
        title="Historical Validation Interpretation",
        text=f"FreightIQ outperformed the immediate-charter benchmark in {sim_res['win_count']} of {sim_res['test_periods_count']} simulated decision windows ({sim_res['win_rate_percentage']}% win rate), resulting in a simulated cost difference of {format_inr(sim_diff_inr)}."
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

