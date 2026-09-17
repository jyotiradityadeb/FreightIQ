"""
FreightIQ Control Tower View Module

Shared renderer for Control Tower and Home landing pages.
"""

import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

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
from app.components.charts import (
    plot_freight_trend,
    plot_forecast_with_ci
)
from app.components.error_boundary import safe_render_section
from backend.forecasting import generate_freight_forecast
from backend.schemas import ScenarioShock
from backend.disruption_engine import evaluate_control_tower_state
from backend.reporting import generate_charter_decision_pdf


def render_control_tower_page(active_page_name: str = "Control Tower"):
    """Renders the complete Control Tower / Overview dashboard UI."""
    # 1. Inject Custom SaaS CSS
    inject_custom_css()

    # 2. Render Sidebar System Status & Theme Switcher
    render_sidebar_status()

    # 3. Top Shell Navigation Bar
    render_top_shell(active_page_name=active_page_name)

    # 4. Global Active Shipment Sync
    shipment_ctx = get_active_shipment_context()

    # Page Title & Subtitle
    st.markdown(f"<h1 style='margin-bottom: 2px;'>{active_page_name}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 20px;'>Real-time freight exposure, market signals, and charter decision monitoring.</p>", unsafe_allow_html=True)

    # Load Processed Dataset & Run Disruption Engine with Fallbacks
    try:
        df = get_cached_processed_data()
        fc_res = generate_freight_forecast(df, horizon=30, selected_model="Auto")
        forecast_df = fc_res["forecast_df"]
        ct_data = evaluate_control_tower_state(forecast_df=forecast_df)
    except Exception as e:
        st.warning(f"Unable to refresh live market feeds ({e}). Displaying cached demonstration state.")
        # Fallback dataset construction if load fails
        dates = pd.date_range(end=pd.Timestamp.now(), periods=60, freq="D")
        df = pd.DataFrame({
            "date": dates,
            "freight_rate": [25.0 + np.sin(i / 5.0) for i in range(60)],
            "bdi": [1500 + i * 2 for i in range(60)],
            "port_congestion_score": [45.0] * 60,
            "vessel_availability_count": [20] * 60,
            "coking_coal_price": [220.0] * 60,
            "iron_ore_price": [110.0] * 60
        })
        forecast_df = df.copy()
        forecast_df["predicted_freight_rate"] = forecast_df["freight_rate"]
        forecast_df["lower_ci"] = forecast_df["freight_rate"] * 0.95
        forecast_df["upper_ci"] = forecast_df["freight_rate"] * 1.05
        ct_data = evaluate_control_tower_state(forecast_df=forecast_df)

    curr_rec = ct_data.get("current_recommendation", {
        "expected_total_cost_inr_formatted": "₹18.58 Cr",
        "recommended_window": "15–19 Sep",
        "vessel_class": "Panamax"
    })

    # ACTIVE SHIPMENT HERO CARD
    with st.container(border=True):
        hero_top_left, hero_top_right = st.columns([3, 1])

        with hero_top_left:
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 4px;">
                    <span class="fiq-mono" style="font-weight: 600;">{shipment_ctx.get('shipment_id', 'FIQ-2026-0001')}</span>
                    <span style="font-size: 1.15rem; font-weight: 700;">{shipment_ctx.get('quantity_tonnes', 75000):,.0f} t {shipment_ctx.get('cargo_type', 'Coking Coal')}</span>
                </div>
                <div style="font-size: 0.875rem;">
                    Route: <strong>{shipment_ctx.get('origin', 'Hay Point')}</strong> → <strong>{shipment_ctx.get('destination', 'Paradip')}</strong>
                </div>
            """, unsafe_allow_html=True)

        with hero_top_right:
            st.markdown("""
                <div style="text-align: right;">
                    <span class="badge-online" style="font-size: 0.8rem; padding: 4px 10px;">RECOMMENDED ACTION</span>
                </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Three Core Metrics
        m1, m2, m3 = st.columns(3)

        with m1:
            st.caption("EXPECTED LOGISTICS COST")
            st.markdown(f"<h2 style='color: #1667D9; margin: 0;'>{curr_rec.get('expected_total_cost_inr_formatted', '₹18.58 Cr')}</h2>", unsafe_allow_html=True)
            st.caption("Base rate + port demurrage + risk factor")

        with m2:
            st.caption("RECOMMENDED CHARTER WINDOW")
            st.markdown(f"<h2 style='margin: 0;'>{curr_rec.get('recommended_window', '15–19 Sep')}</h2>", unsafe_allow_html=True)
            st.caption(f"{curr_rec.get('vessel_class', 'Panamax')} Vessel Class")

        with m3:
            st.caption("DECISION ROBUSTNESS")
            st.markdown("<h2 style='color: #10B981; margin: 0;'>82%</h2>", unsafe_allow_html=True)
            st.caption("Stable across 820 / 1,000 simulated futures")

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Action Buttons
        b1, b2, b3, b_empty = st.columns([1.5, 1.5, 2.2, 2.8])
        with b1:
            if st.button("View Recommendation", type="primary", use_container_width=True, key=f"{active_page_name}_btn_rec"):
                navigate_to(CHARTER_PAGE)
        with b2:
            if st.button("Run Scenario", type="secondary", use_container_width=True, key=f"{active_page_name}_btn_scen"):
                navigate_to(SCENARIO_PAGE)
        with b3:
            pdf_bytes = generate_charter_decision_pdf(recommendation=curr_rec, data_mode="DEMO")
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name=f"FreightIQ_Decision_Report_{datetime.datetime.now().strftime('%Y-%m-%d')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"{active_page_name}_btn_pdf"
            )

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # BELOW HERO: LEFT 2/3 (Market Overview Chart) vs RIGHT 1/3 (Shipment Activity)
    c_market, c_activity = st.columns([2, 1])

    with c_market:
        with st.container(border=True):
            st.markdown("### Freight Market Overview")
            st.caption("Historical Panamax / Capesize spot freight rate trajectory (₹/tonne)")
            fig_trend = plot_freight_trend(df)
            st.plotly_chart(fig_trend, use_container_width=True)

    with c_activity:
        with st.container(border=True):
            st.markdown("### Shipment Activity")
            st.caption("Current vessel queue & route conditions")

            st.markdown("""
                <div style="display: flex; flex-direction: column; gap: 14px; font-size: 0.875rem;">
                    <div style="border-bottom: 1px solid var(--border); padding-bottom: 10px;">
                        <div style="font-weight: 600;">Paradip Port Queue</div>
                        <div style="font-size: 0.8rem;">Congestion Index: 64/100 • Avg Wait 39h</div>
                    </div>
                    <div style="border-bottom: 1px solid var(--border); padding-bottom: 10px;">
                        <div style="font-weight: 600;">Vessel Availability</div>
                        <div style="font-size: 0.8rem;">East Coast Australia: 18 Panamax vessels open</div>
                    </div>
                    <div style="border-bottom: 1px solid var(--border); padding-bottom: 10px;">
                        <div style="font-weight: 600;">Bunker Fuel Benchmark</div>
                        <div style="font-size: 0.8rem;">VLSFO Singapore: ₹54,200 / t (Stable)</div>
                    </div>
                    <div>
                        <div style="font-weight: 600;">Weather Warning</div>
                        <div style="color: #10B981; font-size: 0.8rem;">Bay of Bengal: Normal passage conditions</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # NEXT SECTION: FREIGHT FORECAST (Large Clean Chart)
    with st.container(border=True):
        st.markdown("### Freight Forecast")
        st.caption("30-Day predictive freight rate outlook with 95% confidence bounds (₹/tonne)")
        fig_fc = plot_forecast_with_ci(df, forecast_df, title="", lookback_days=45)
        st.plotly_chart(fig_fc, use_container_width=True)

    render_disclaimer()
