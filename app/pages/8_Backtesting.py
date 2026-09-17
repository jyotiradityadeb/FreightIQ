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

st.set_page_config(page_title="Historical Validation — FreightIQ", page_icon=None, layout="wide")

from app.components.helpers import (
    inject_custom_css,
    render_top_shell,
    render_sidebar_status,
    render_disclaimer,
    get_cached_processed_data,
    format_inr,
    usd_to_inr
)
from app.components.cards import render_compact_kpi_card, render_forecast_interpretation_box
from app.components.charts import (
    plot_backtest_cost_comparison,
    plot_cumulative_simulated_savings
)
from backend.backtesting import run_historical_simulation

inject_custom_css()
render_sidebar_status()
render_top_shell(active_page_name="Historical Validation")

df = get_cached_processed_data()

# Header
st.markdown("### Historical Validation")
st.caption("Walk-forward simulation against immediate-charter benchmark [D] Demo Data")

with st.expander("⚙ Configure Historical Simulation Window & Model Parameters", expanded=False):
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

    run_sim = st.button("Re-run Historical Simulation", use_container_width=True)

st.markdown("---")

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
    # 4 Top Metrics
    k1, k2, k3, k4 = st.columns(4)

    sim_diff_inr = usd_to_inr(sim_res["simulated_cost_difference_total"])
    mae_inr = usd_to_inr(sim_res["forecast_accuracy_metrics"]["MAE"])

    with k1:
        render_compact_kpi_card(
            label="DECISION WINDOWS",
            value_str=f"{sim_res['test_periods_count']}",
            subtext_str="Historical decision points"
        )

    with k2:
        render_compact_kpi_card(
            label="WIN RATE",
            value_str=f"{sim_res['win_rate_percentage']:.1f}%",
            subtext_str=f"{sim_res['win_count']} of {sim_res['test_periods_count']} windows",
            subtext_color="#2E8B68"
        )

    with k3:
        render_compact_kpi_card(
            label="SIMULATED COST DIFFERENCE",
            value_str=format_inr(sim_diff_inr),
            subtext_str=f"{sim_res['simulated_savings_percentage']:+.2f}% vs Immediate Charter",
            subtext_color="#2E8B68" if sim_diff_inr >= 0 else "#C98226"
        )

    with k4:
        render_compact_kpi_card(
            label="FORECAST MAE",
            value_str=f"{format_inr(mae_inr)} / t",
            subtext_str="Walk-forward forecast error"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    render_forecast_interpretation_box(
        title="Historical Validation Interpretation",
        text=f"FreightIQ outperformed the immediate-charter benchmark in {sim_res['win_count']} of {sim_res['test_periods_count']} simulated decision windows ({sim_res['win_rate_percentage']}% win rate), resulting in a simulated cost difference of {format_inr(sim_diff_inr)}."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    res_df = pd.DataFrame(sim_res["period_results_table"])

    c1, c2 = st.columns(2)
    with c1:
        fig_bar = plot_backtest_cost_comparison(res_df)
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        fig_cum = plot_cumulative_simulated_savings(res_df)
        st.plotly_chart(fig_cum, use_container_width=True)

    st.markdown("---")

    # Table
    st.markdown("### Decision Outcomes")
    
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
            "Simulated Cost Difference": format_inr(d_inr),
            "Status": r["simulated_savings_status"]
        })

    st.dataframe(table_rows, use_container_width=True)

else:
    st.error(f"Simulation Error: {sim_res.get('error')}")

st.markdown("""
    <div style="background-color: #151E28; border-left: 3px solid #C98226; border-radius: 4px; padding: 10px 14px; margin-top: 24px; color: #C98226; font-size: 0.78rem;">
        <strong>Validation Disclaimer:</strong> Historical simulation results are for prototype evaluation only and do not represent realized commercial savings or future performance.
    </div>
""", unsafe_allow_html=True)

render_disclaimer()
