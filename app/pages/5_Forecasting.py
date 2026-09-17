"""
FreightIQ Streamlit Page 2: Freight Rate Forecasting
"""

import os
import sys

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="FreightIQ — Forecasts", page_icon=None, layout="wide")

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
from app.components.charts import plot_forecast_with_ci, apply_industrial_theme
from backend.forecasting import generate_freight_forecast, HAS_PROPHET
from backend.domain.routes import get_calibrated_routes, resolve_route
from backend.route_market import get_route_market_history
from backend.validation import (
    run_real_validation,
    build_validation_chart_data,
    DataMode,
)

inject_custom_css()
render_sidebar_status()
render_top_shell(active_page_name="Forecasts")

shipment_ctx = get_active_shipment_context()

# Retrieve calibrated route options
calibrated_routes = get_calibrated_routes()
route_display_labels = [r["display_label"] for r in calibrated_routes]

# Active shipment synchronization
active_origin = shipment_ctx.get("origin", "Hay Point")
active_dest = shipment_ctx.get("destination", "Paradip")
active_o_pid = shipment_ctx.get("origin_port_id", "AU_HPT")
active_d_pid = shipment_ctx.get("destination_port_id", "IN_PDP")

active_route_res = resolve_route(active_o_pid or active_origin, active_d_pid or active_dest)

default_route_idx = 0
unsupported_active_msg = None

if active_route_res.is_calibrated:
    for idx, r_dict in enumerate(calibrated_routes):
        if r_dict["origin_port_id"] == active_route_res.origin_port_id and r_dict["destination_port_id"] == active_route_res.destination_port_id:
            default_route_idx = idx
            break
else:
    unsupported_active_msg = f"Forecast unavailable for active shipment route ({active_origin} → {active_dest}) — no demo-calibrated route model."

# Header
st.markdown("<h1 style='margin-bottom: 2px;'>Forecasts</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #6B7280; font-size: 0.95rem; margin-bottom: 20px;'>Predictive spot freight rate models and demo-series simulation metrics.</p>", unsafe_allow_html=True)
st.caption("Source: synthetic route-specific demonstration series — not real Baltic Exchange or AIS data")

if unsupported_active_msg:
    st.warning(f"⚠ {unsupported_active_msg}")

# COMPACT TOOLBAR
with st.container(border=True):
    c1, c2, c3, c4 = st.columns([1.8, 1.2, 1.2, 1])
    with c1:
        selected_route_label = st.selectbox("Route", route_display_labels, index=default_route_idx)
        selected_route_dict = calibrated_routes[route_display_labels.index(selected_route_label)]
        origin_port_id = selected_route_dict["origin_port_id"]
        destination_port_id = selected_route_dict["destination_port_id"]
        origin_name = selected_route_dict["origin_name"]
        destination_name = selected_route_dict["destination_name"]
        route_key = selected_route_dict["route_key"]
    with c2:
        model_options = ["Auto", "SARIMA", "Naive Baseline"]
        if HAS_PROPHET:
            model_options.append("Prophet")
        selected_model = st.selectbox("Forecast Model", model_options, index=0)
    with c3:
        horizon = st.select_slider("Forecast Horizon", options=[7, 14, 30], value=14)
    with c4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        run_fc_btn = st.button("Update Forecast", type="primary", use_container_width=True)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    tb_m1, tb_m2 = st.columns([2.5, 1])
    with tb_m1:
        st.caption(f"Demo route context — forecast uses route-specific synthetic history ({route_key})")
    with tb_m2:
        st.markdown("<div style='text-align: right;'><span style='background-color: #DEF7EC; color: #03543F; font-size: 0.75rem; font-weight: 600; padding: 3px 8px; border-radius: 4px;'>🟢 DEMO-CALIBRATED</span></div>", unsafe_allow_html=True)

# Sync active shipment context to selected route
update_active_shipment_context(
    origin=origin_name,
    origin_port_id=origin_port_id,
    destination=destination_name,
    destination_port_id=destination_port_id
)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# Load Route-Specific Synthetic History (No scalar scaling)
route_df = get_route_market_history(route_key)

# Generate Forecast on route_df
fc_res = generate_freight_forecast(route_df, horizon=horizon, selected_model=selected_model)
fc_df = fc_res["forecast_df"].copy()

metrics = fc_res["metrics"]
_metrics_ok = metrics.get("status") == "OK"

# MAIN FORECAST CHART (DOMINATES PAGE)
with st.container(border=True):
    st.markdown(f"### Spot Freight Rate Forecast — {selected_route_label} ({horizon}-Day Horizon)")
    st.caption(f"Model: {fc_res['selected_model']} • 95% Confidence Interval Band • Data: SYNTHETIC ROUTE-SPECIFIC DEMO HISTORY")
    fig_fc = plot_forecast_with_ci(
        route_df,
        fc_df,
        title="",
        lookback_days=90
    )
    st.plotly_chart(fig_fc, use_container_width=True)

    # Optional Route Comparison Feature
    with st.expander("📊 Compare Route Freight Trajectories (Optional)"):
        st.caption("Overlay up to 3 calibrated routes to inspect route-specific historical freight variations.")
        compare_selected = st.multiselect(
            "Select routes to compare",
            options=route_display_labels,
            default=[selected_route_label] if selected_route_label in route_display_labels else route_display_labels[:2],
            max_selections=3
        )
        if compare_selected:
            fig_cmp = go.Figure()
            colors = ["#1667D9", "#D97706", "#059669"]
            for c_idx, label in enumerate(compare_selected):
                r_info = calibrated_routes[route_display_labels.index(label)]
                r_hist = get_route_market_history(r_info["route_key"]).tail(120)
                fig_cmp.add_trace(go.Scatter(
                    x=r_hist["date"],
                    y=r_hist["freight_rate"].apply(usd_to_inr),
                    mode="lines",
                    name=label,
                    line=dict(color=colors[c_idx % len(colors)], width=2.0)
                ))
            apply_industrial_theme(fig_cmp, title="", height=320)
            st.plotly_chart(fig_cmp, use_container_width=True)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# BELOW: VALIDATION METRICS & FORECAST EXPLANATION
col_met, col_exp = st.columns([1, 1])

with col_met:
    with st.container(border=True):
        st.markdown("### Demo-Series Model Metrics")
        st.caption("Out-of-sample error on synthetic demo series — not a real-market accuracy claim")
        st.caption("Validation source: synthetic demonstration series")

        if not _metrics_ok:
            _avail = metrics.get("available_observations", "?")
            _req = metrics.get("minimum_required_observations", "?")
            st.warning(f"Validation unavailable — insufficient historical observations (available: {_avail}, required: {_req})")
        else:
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.caption("MAE")
                st.markdown(f"**{format_inr(usd_to_inr(metrics['MAE']))} / t**")
                st.caption("Mean Absolute Error")
            with m_col2:
                st.caption("RMSE")
                st.markdown(f"**{format_inr(usd_to_inr(metrics['RMSE']))} / t**")
                st.caption("Root Mean Squared Error")
            with m_col3:
                st.caption("MAPE")
                st.markdown(f"**{metrics['MAPE']:.2f}%**")
                st.caption("Mean Absolute Pct Error")

        st.divider()
        st.markdown("#### Model Comparison Benchmark")
        comp_rows = []
        for m in fc_res["comparison_table"]:
            comp_rows.append({
                "Model": m["Model"],
                "MAE (₹/t)": f"₹{usd_to_inr(m['MAE']):.0f}" if m.get("MAE") is not None else "—",
                "RMSE (₹/t)": f"₹{usd_to_inr(m['RMSE']):.0f}" if m.get("RMSE") is not None else "—",
                "MAPE": f"{m['MAPE (%)']:.2f}%" if m.get("MAPE (%)") is not None else "—",
                "Status": "Selected" if m["Selected"] == "Yes" else "Evaluated"
            })
        st.dataframe(comp_rows, use_container_width=True, hide_index=True)

with col_exp:
    with st.container(border=True):
        st.markdown("### Contextual Market Signals")
        st.caption("Qualitative market indicators — not used as explicit model regressors in univariate forecast")

        drivers = [
            {"Signal": "Bunker Fuel Spot Prices", "Indicator": "Softening", "Context": "Macro cost driver", "Relevance": "High"},
            {"Signal": "East Coast Port Congestion", "Indicator": "Elevated", "Context": "Logistics queue delay", "Relevance": "High"},
            {"Signal": "Panamax Fleet Availability", "Indicator": "Tight", "Context": "Spot vessel liquidity", "Relevance": "Medium"},
            {"Signal": "Queensland Rail Throughput", "Indicator": "Stable", "Context": "Supply rail bottleneck", "Relevance": "Medium"}
        ]
        st.dataframe(pd.DataFrame(drivers), use_container_width=True, hide_index=True)

        st.divider()
        st.caption("FORECAST INTERPRETATION")
        if not fc_df.empty:
            start_val = float(fc_df["predicted_freight_rate"].iloc[0])
            end_val = float(fc_df["predicted_freight_rate"].iloc[-1])
            diff_val = end_val - start_val
            if diff_val > 0.5:
                trend_desc = f"projected to rise by ₹{usd_to_inr(diff_val):.0f}/t"
            elif diff_val < -0.5:
                trend_desc = f"projected to soften by ₹{usd_to_inr(abs(diff_val)):.0f}/t"
            else:
                trend_desc = "projected to remain relatively stable"
        else:
            trend_desc = "projected to remain stable"

        if _metrics_ok:
            st.write(f"Freight rates are {trend_desc} over the next {horizon} days based on {fc_res['selected_model']} model analysis. The model achieves an out-of-sample MAPE of {metrics['MAPE']:.2f}% on the synthetic demo series.")
        else:
            st.write(f"Freight rates are {trend_desc} over the next {horizon} days based on {fc_res['selected_model']} model analysis. Demo-series metrics unavailable — insufficient data for error estimation.")

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# ── REAL-DATA VALIDATION (Open-Meteo) ────────────────────────────────────────
with st.container(border=True):
    st.markdown("### Real-Data Validation — Open-Meteo Observed Series")
    st.caption(
        "Source: Open-Meteo Archive API — public daily weather observations (CC BY 4.0). "
        "Max daily wind speed at Paradip port. Train/test split: last 30 days held out. "
        "Metrics computed on real observed values only — not on synthetic data."
    )

    @st.cache_data(ttl=3600, show_spinner=False)
    def _load_real_validation():
        return build_validation_chart_data(model_name="SARIMA", horizon=30)

    chart_data = _load_real_validation()

    if chart_data is None:
        st.warning(
            "Real-data validation unavailable — no cached series and network unreachable. "
            "Connect to the internet once to populate the local cache."
        )
    else:
        result = chart_data["result"]

        if result.status == "UNAVAILABLE":
            st.warning(result.notes)
        elif result.status == "INSUFFICIENT_DATA":
            st.info(f"Insufficient data for hold-out evaluation: {result.notes}")
        else:
            # Metrics row
            rv_c1, rv_c2, rv_c3, rv_c4 = st.columns(4)
            with rv_c1:
                st.caption("MAE (real)")
                st.markdown(f"**{result.mae:.3f} m/s**" if result.mae is not None else "—")
            with rv_c2:
                st.caption("RMSE (real)")
                st.markdown(f"**{result.rmse:.3f} m/s**" if result.rmse is not None else "—")
            with rv_c3:
                st.caption("MAPE (real)")
                st.markdown(f"**{result.mape:.2f}%**" if result.mape is not None else "—")
            with rv_c4:
                st.caption("Observations")
                st.markdown(f"**{result.n_observations}** ({result.start_date} → {result.end_date})")

            # Plotly chart: observed vs predicted on test split
            fig_rv = go.Figure()

            # Training series (last 90 days for readability)
            lookback = 90
            train_dates = chart_data["dates_train"][-lookback:]
            train_vals = chart_data["values_train"][-lookback:]

            fig_rv.add_trace(go.Scatter(
                x=train_dates, y=train_vals,
                mode="lines",
                name="Observed (train)",
                line=dict(color="#6B7280", width=1.5),
            ))

            # CI band
            fig_rv.add_trace(go.Scatter(
                x=list(chart_data["dates_pred"]) + list(chart_data["dates_pred"])[::-1],
                y=list(chart_data["upper_ci"]) + list(chart_data["lower_ci"])[::-1],
                fill="toself",
                fillcolor="rgba(22, 103, 217, 0.10)",
                line=dict(width=0),
                name="±1σ interval",
                showlegend=True,
            ))

            # Predicted on test window
            fig_rv.add_trace(go.Scatter(
                x=chart_data["dates_pred"], y=chart_data["values_pred"],
                mode="lines",
                name=f"{result.model_name} forecast",
                line=dict(color="#1667D9", width=2, dash="dash"),
            ))

            # Actual test values
            fig_rv.add_trace(go.Scatter(
                x=chart_data["dates_test"], y=chart_data["values_test"],
                mode="lines+markers",
                name="Observed (test, held-out)",
                line=dict(color="#059669", width=2),
                marker=dict(size=4),
            ))

            # Train/test split line
            split_x_str = str(pd.Timestamp(chart_data["split_date"]).date())
            fig_rv.add_shape(
                type="line",
                x0=split_x_str,
                x1=split_x_str,
                y0=0,
                y1=1,
                yref="paper",
                line=dict(color="#D97706", width=1.5, dash="dot")
            )
            fig_rv.add_annotation(
                x=split_x_str,
                y=1.0,
                yref="paper",
                text="Train / Test split",
                showarrow=False,
                xanchor="right",
                yanchor="bottom",
                font=dict(size=10, color="#D97706")
            )


            # Metric annotation box
            if result.mae is not None:
                ann_text = (
                    f"MAE={result.mae:.3f}  RMSE={result.rmse:.3f}  MAPE={result.mape:.2f}%"
                )
                fig_rv.add_annotation(
                    xref="paper", yref="paper", x=0.01, y=0.97,
                    text=ann_text, showarrow=False,
                    font=dict(size=10, color="#374151"),
                    bgcolor="#F9FAFB", bordercolor="#D1D5DB", borderwidth=1,
                    align="left",
                )

            fig_rv.update_layout(
                title="Validation on Real Observed Data (Open-Meteo) — Paradip Max Daily Wind Speed",
                xaxis_title="Date",
                yaxis_title="Wind Speed (m/s)",
                height=380,
                margin=dict(l=20, r=20, t=50, b=20),
                legend=dict(orientation="h", y=-0.2),
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                font=dict(family="Inter, sans-serif", size=11, color="#374151"),
            )
            fig_rv.update_xaxes(showgrid=True, gridcolor="#F3F4F6")
            fig_rv.update_yaxes(showgrid=True, gridcolor="#F3F4F6")

            st.plotly_chart(fig_rv, use_container_width=True)
            st.caption(
                f"Note: {result.notes} "
                "Wind speed is not a freight rate signal — this chart validates that the "
                "model pipeline correctly fits and evaluates real external data."
            )

render_disclaimer()

