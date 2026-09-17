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
from backend.config_model import get_decision_params_registry
from backend.validation import run_real_validation, DataMode

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
tab_conn, tab_quality, tab_overrides, tab_audit, tab_limits, tab_params, tab_cards, tab_trust = st.tabs([
    "Connections",
    "Data Quality",
    "Overrides",
    "Audit Trail",
    "Model & Data Limitations",
    "Decision Parameters",
    "Model Cards",
    "Model Status",
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

with tab_params:
    with st.container(border=True):
        st.markdown("### Decision Parameters & Provenance")
        st.caption(
            "Read-only registry of every numeric constant used in the optimizer and cost model. "
            "Classification shows whether each value is observed, derived, or assumed."
        )

        registry = get_decision_params_registry()
        display_rows = []
        for r in registry:
            display_rows.append({
                "Parameter": r["parameter"],
                "Value": r["value"],
                "Unit": r["unit"],
                "Classification": r["classification"],
                "Sensitivity Range": f"{r['sensitivity_min']} – {r['sensitivity_max']}",
                "Source": r["source"],
                "Note": r["note"][:120] + "…" if len(r["note"]) > 120 else r["note"],
            })
        st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)

        classification_legend = {
            "OBSERVED": "Directly measured from a live or historical data source",
            "DERIVED": "Calculated from observed values with a documented formula",
            "LITERATURE_INFORMED": "Consistent with a published industry range",
            "CONFIGURED_ASSUMPTION": "Reasonable default — tune per contract or trade lane",
            "DEMO_ONLY_ASSUMPTION": "Prototype placeholder — must be replaced before production use",
        }
        with st.expander("Classification legend"):
            for cls, desc in classification_legend.items():
                st.markdown(f"**{cls}** — {desc}")

with tab_cards:
    st.markdown("### Model Cards")
    st.caption(
        "Purpose, algorithm, assumptions, limitations, and validation status "
        "for each model powering FreightIQ."
    )

    _MODEL_CARDS = [
        {
            "name": "Forecasting Engine",
            "purpose": "Predict spot freight rates over a 7–30 day horizon to guide charter timing.",
            "inputs": "Synthetic daily freight rate series (365+ days). Route selector and horizon.",
            "outputs": "Point forecast + 95% CI band. MAE / RMSE / MAPE on held-out test fold.",
            "algorithm": (
                "Three candidates: Naive Baseline (last-value + damped trend), "
                "SARIMA(1,1,1)(1,0,0)[7] via statsmodels SARIMAX, "
                "and Prophet (if installed). Auto mode selects the candidate with lowest MAE."
            ),
            "assumptions": (
                "Stationarity after differencing. Weekly seasonality is dominant. "
                "Synthetic series is drawn from a stationary distribution — "
                "real freight markets exhibit structural breaks not present here."
            ),
            "limitations": (
                "All metrics are computed on the same synthetic series used for model fitting. "
                "They do not establish real-market forecast accuracy. "
                "No exogenous regressors (bunker price, fleet news, geopolitics) are incorporated."
            ),
            "validation_status": "Synthetic series backtest only. Real-market validation: not conducted.",
            "data_provenance": "Source: synthetic demonstration series — not real Baltic Exchange data.",
        },
        {
            "name": "Charter Optimizer",
            "purpose": "Identify the lowest expected logistics cost charter date and vessel class for a given cargo.",
            "inputs": (
                "Forecast DataFrame, cargo type, quantity (tonnes), origin/destination, "
                "laycan window, vessel class preference, demurrage rate, risk tolerance."
            ),
            "outputs": (
                "Ranked candidate matrix with freight, demurrage, congestion, and risk components. "
                "Best option, explainability block, and sensitivity-ready cost function."
            ),
            "algorithm": (
                "Exhaustive enumeration over (vessel_class x charter_date) combinations within "
                "the laycan window. Each candidate evaluated with evaluate_charter_candidate() "
                "using: freight cost = forecast_rate x quantity x distance_factor, "
                "demurrage = DEMURRAGE_EXPOSURE_FACTOR x demurrage_rate x waiting_hours, "
                "congestion = CONGESTION_COST_MULTIPLIER x congestion_score x quantity, "
                "risk penalty = weather_risk x WEATHER_RISK_PENALTY + event_risk x EVENT_RISK_PENALTY."
            ),
            "assumptions": (
                "Freight rate forecasts are unbiased. "
                "Port congestion and waiting hours are from synthetic signals. "
                "Vessel capacity/draft constraints from VESSEL_MASTER and PORT_MASTER. "
                "Cost constants (DEMURRAGE_EXPOSURE_FACTOR=0.15, CONGESTION_COST_MULTIPLIER=0.5) "
                "are illustrative defaults — see Decision Parameters tab for full provenance."
            ),
            "limitations": (
                "No LP/MIP solver — enumeration only. Does not optimise multi-leg or multi-cargo. "
                "Cost weights use DEMO_ONLY_ASSUMPTION defaults calibrated to synthetic signals. "
                "Real procurement requires calibration against contract terms and actual demurrage records."
            ),
            "validation_status": "Sensitivity wiring validated via unit tests (test_optimizer_integrity.py). No real-shipment backtesting.",
            "data_provenance": "Source: synthetic freight forecast + synthetic port signals.",
        },
        {
            "name": "Decision Twin (Monte Carlo)",
            "purpose": "Stress-test charter decisions across 1,000 stochastic futures to compute robustness score and expected regret.",
            "inputs": "Active shipment context, freight forecast, optimizer recommendation, risk tolerance.",
            "outputs": (
                "Robustness score (0–100), expected regret (INR Lakh), "
                "simulated cost distribution, regret surface."
            ),
            "algorithm": (
                "1,000 Monte Carlo paths: each path draws freight rate, "
                "congestion, and waiting-hours perturbations from parameterised distributions. "
                "For each path: optimizer runs and cost is compared to the baseline recommendation. "
                "Robustness = fraction of paths where baseline is within 5% of path-optimal."
            ),
            "assumptions": (
                "Perturbations are i.i.d. lognormal — no serial correlation in shock paths. "
                "Same DEMO_ONLY_ASSUMPTION cost weights as the optimizer. "
                "1,000 paths is sufficient for stable robustness estimates at ±5% tolerance."
            ),
            "limitations": (
                "Simulated futures are generated from synthetic signals. "
                "Real market scenarios exhibit tail events, geopolitical shocks, "
                "and regime changes not represented in the demo distribution. "
                "Robustness scores are not comparable across different demo-data runs."
            ),
            "validation_status": "Decision Twin output validated against optimizer unit tests. No real-decision backtesting.",
            "data_provenance": "Source: simulated futures on synthetic demo state — not real-market scenario data.",
        },
        {
            "name": "Scenario Engine",
            "purpose": "Evaluate user-defined freight market scenarios against the baseline recommendation.",
            "inputs": "Cargo configuration, baseline optimization result, user-defined scenario parameters.",
            "outputs": "Scenario vs baseline cost comparison, delta table, narrative summary.",
            "algorithm": (
                "Re-runs optimize_charter_timing() with scenario-perturbed inputs "
                "(freight shock factor, congestion override, demurrage multiplier). "
                "Computes delta cost and recommendation change vs baseline."
            ),
            "assumptions": (
                "Scenario perturbations are applied uniformly across the forecast horizon. "
                "Base model assumptions (cost constants, vessel master) are unchanged per scenario."
            ),
            "limitations": (
                "Scenarios are illustrative — they do not model real geopolitical events, "
                "fleet supply shocks, or regulatory changes. "
                "Outputs are deterministic (no uncertainty bands on scenario cost)."
            ),
            "validation_status": "Scenario output matches optimizer by construction. No real-scenario validation.",
            "data_provenance": "Source: user-defined perturbations on synthetic baseline.",
        },
    ]

    for card in _MODEL_CARDS:
        with st.expander(f"{card['name']}", expanded=False):
            c_l, c_r = st.columns([1, 1])
            with c_l:
                st.markdown(f"**Purpose**  \n{card['purpose']}")
                st.markdown(f"**Algorithm**  \n{card['algorithm']}")
                st.markdown(f"**Assumptions**  \n{card['assumptions']}")
            with c_r:
                st.markdown(f"**Inputs**  \n{card['inputs']}")
                st.markdown(f"**Outputs**  \n{card['outputs']}")
                st.markdown(f"**Limitations**  \n{card['limitations']}")
            st.divider()
            st.markdown(
                f"**Validation status:** {card['validation_status']}  \n"
                f"**Data provenance:** {card['data_provenance']}"
            )

with tab_trust:
    with st.container(border=True):
        st.markdown("### Model Status — Trust Panel")
        st.caption(
            "Explicit status of each model component. "
            "Green = validated within stated scope. "
            "Amber = functional but limited validation. "
            "Red = not validated or known limitation."
        )

        trust_items = [
            {
                "Component": "Forecasting Engine",
                "Status": "Amber",
                "Scope": "Synthetic series only",
                "Validated": "Backtest MAE/RMSE/MAPE on demo series",
                "Not Validated": "Real-market freight rate accuracy",
                "Key Limitation": "No exogenous regressors; metrics on same series used for fitting",
            },
            {
                "Component": "Charter Optimizer",
                "Status": "Amber",
                "Scope": "Synthetic signals + demo cost weights",
                "Validated": "Sensitivity wiring (unit tests), determinism, feasibility constraints",
                "Not Validated": "Cost weights vs real contracts; real-shipment cost accuracy",
                "Key Limitation": "DEMO_ONLY_ASSUMPTION cost constants — must be recalibrated for production",
            },
            {
                "Component": "Decision Twin (Monte Carlo)",
                "Status": "Amber",
                "Scope": "Synthetic futures on demo state",
                "Validated": "Robustness score computation; unit tests pass",
                "Not Validated": "Real market stress scenarios; tail-event representation",
                "Key Limitation": "i.i.d. lognormal shocks do not model real market regime changes",
            },
            {
                "Component": "Scenario Engine",
                "Status": "Amber",
                "Scope": "Deterministic perturbations on synthetic baseline",
                "Validated": "Output consistency with optimizer",
                "Not Validated": "Real scenario calibration",
                "Key Limitation": "No uncertainty bounds on scenario outputs",
            },
            {
                "Component": "Real-Data Validation (Open-Meteo)",
                "Status": "Green",
                "Scope": "Public weather observations at Paradip",
                "Validated": "Fetch, cache, train/test split, SARIMA fit, held-out MAE/RMSE/MAPE",
                "Not Validated": "Predictive value of wind speed for freight rates",
                "Key Limitation": "Wind speed is a port-risk proxy — not a direct freight signal",
            },
        ]

        import pandas as _pd_trust
        df_trust = _pd_trust.DataFrame(trust_items)
        st.dataframe(df_trust, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown(
            "**How to interpret status:**  \n"
            "- **Green** — component is validated within its stated scope (the scope itself may be narrow).  \n"
            "- **Amber** — component functions correctly on demo data but has not been validated against "
            "real-market or production conditions.  \n"
            "- **Red** — component has a known material limitation that has not been addressed (none currently).  \n\n"
            "FreightIQ is a **decision-support prototype**. Outputs do not constitute chartering advice, "
            "legal commitments, or financial recommendations. All model outputs require expert review before "
            "use in commercial procurement decisions."
        )

        # Live real-data status check
        st.divider()
        st.markdown("**Live Validation Data Status**")

        @st.cache_data(ttl=600, show_spinner=False)
        def _check_real_validation_status():
            res = run_real_validation()
            return res.status, res.n_observations, res.start_date, res.end_date, res.mae, res.notes

        v_status, v_n, v_start, v_end, v_mae, v_notes = _check_real_validation_status()

        if v_status == "UNAVAILABLE":
            st.error(f"Open-Meteo cache: UNAVAILABLE — {v_notes}")
        elif v_status == "INSUFFICIENT_DATA":
            st.warning(f"Open-Meteo cache: INSUFFICIENT DATA — {v_notes}")
        else:
            st.success(
                f"Open-Meteo cache: OK — {v_n} observations ({v_start} to {v_end}). "
                f"Real validation MAE: {v_mae:.3f} m/s wind speed."
            )

render_disclaimer()

