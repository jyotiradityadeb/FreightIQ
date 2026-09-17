"""
FreightIQ Reusable Industrial Visual Components

Provides industrial UI card components, charter recommendation panels,
scenario comparison tables, and maritime route visualization using 100% native Streamlit components.
Zero raw HTML leakage!
"""

import streamlit as st
import textwrap
from typing import Dict, Any, List, Optional
from app.components.helpers import format_inr, usd_to_inr, format_tonnes, format_hours


def render_compact_kpi_card(
    label: str,
    value_str: str,
    subtext_str: str,
    subtext_color: str = "#A2ADBA"
):
    """Renders a compact industrial KPI card using native Streamlit container."""
    with st.container(border=True):
        st.caption(label)
        st.markdown(f"**{value_str}**")
        st.caption(subtext_str)


def render_charter_recommendation_panel(rec: Dict[str, Any]):
    """
    Renders the Charter Recommendation panel using 100% native Streamlit components.
    Guarantees ZERO raw HTML leakage!
    """
    # Convert USD costs to INR for presentation
    freight_inr = usd_to_inr(rec.get("expected_freight_cost_usd", 0.0))
    demurrage_inr = usd_to_inr(rec.get("expected_demurrage_cost_usd", 0.0))
    congestion_inr = usd_to_inr(rec.get("expected_congestion_cost_usd", 0.0))
    risk_inr = usd_to_inr(rec.get("expected_route_risk_penalty_usd", 0.0))
    total_inr = usd_to_inr(rec.get("expected_total_logistics_cost_usd", 0.0))
    per_tonne_inr = total_inr / max(1.0, rec.get("quantity_tonnes", 1.0))

    with st.container(border=True):
        top_left, top_right = st.columns([2, 1])

        with top_left:
            st.caption("STATUS")
            st.markdown("**RECOMMENDED**")
            st.markdown(f"### {rec.get('decision', 'Charter within selected window')}")

        with top_right:
            st.caption("EXPECTED TOTAL COST")
            st.markdown(f"### {format_inr(total_inr)}")
            st.caption(f"{format_inr(per_tonne_inr, is_per_tonne=True)}")

        st.divider()

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.caption("RECOMMENDED WINDOW")
            st.write(rec.get('recommended_charter_date', 'N/A'))

        with c2:
            st.caption("VESSEL CLASS")
            st.write(rec.get('recommended_vessel', 'N/A'))

        with c3:
            st.caption("CARGO")
            st.write(f"{format_tonnes(rec.get('quantity_tonnes', 0))} {rec.get('cargo_type', '')}")

        with c4:
            st.caption("ROUTE")
            st.write(f"{rec.get('origin', '')} → {rec.get('destination', '')}")

        st.divider()

        k1, k2, k3, k4 = st.columns(4)

        with k1:
            st.caption("Freight Cost")
            st.write(format_inr(freight_inr))

        with k2:
            st.caption("Expected Demurrage")
            st.write(format_inr(demurrage_inr))

        with k3:
            st.caption("Port / Waiting Cost")
            st.write(format_inr(congestion_inr))

        with k4:
            st.caption("Risk Adjustment")
            st.write(format_inr(risk_inr))

        st.divider()

        st.caption("Decision Drivers")
        for driver in rec.get("why", []):
            st.write(f"• {driver}")

        st.caption("Prototype decision-support estimate based on demo inputs.")


def render_scenario_comparison_table(scenarios: Dict[str, Any]):
    """Renders Scenario Comparison Table formatted cleanly in INR."""
    st.markdown("### Scenario Comparison")

    rows = []
    for opt_key, data in scenarios.items():
        label = "Option A (Recommended)" if "A" in opt_key else ("Option B (Alternative)" if "B" in opt_key else "Option C (Earliest Date)")
        tot_inr = usd_to_inr(data.get("total_logistics_cost_usd", 0.0))
        frt_inr = usd_to_inr(data.get("freight_cost_usd", 0.0))
        dem_inr = usd_to_inr(data.get("demurrage_cost_usd", 0.0))
        prt_inr = usd_to_inr(data.get("congestion_cost_usd", 0.0))
        rsk_inr = usd_to_inr(data.get("route_risk_penalty_usd", 0.0))

        rows.append({
            "Scenario": label,
            "Charter Window": data.get("charter_date"),
            "Vessel": data.get("vessel_class"),
            "Freight Cost": format_inr(frt_inr),
            "Demurrage": format_inr(dem_inr),
            "Port Cost": format_inr(prt_inr),
            "Risk Adjustment": format_inr(rsk_inr),
            "Total Logistics Cost": format_inr(tot_inr)
        })

    st.dataframe(
        rows,
        use_container_width=True
    )


def render_route_visualization_card(origin: str, destination: str):
    """Renders simple maritime route visualization card using native Streamlit components."""
    routes_meta = {
        ("Australia", "Visakhapatnam"): {"nm": 4500, "days": 14, "draft": "16.5m (Compatible)"},
        ("Australia", "Paradip"): {"nm": 4300, "days": 13, "draft": "17.5m (Compatible)"},
        ("Australia", "Kolkata/Haldia"): {"nm": 4650, "days": 15, "draft": "12.5m (Draft Constrained)"},
        ("Indonesia", "Visakhapatnam"): {"nm": 2200, "days": 7, "draft": "16.5m (Compatible)"},
        ("Indonesia", "Paradip"): {"nm": 2100, "days": 6.5, "draft": "17.5m (Compatible)"},
        ("Indonesia", "Kolkata/Haldia"): {"nm": 2350, "days": 8, "draft": "12.5m (Draft Constrained)"},
        ("South Africa", "Visakhapatnam"): {"nm": 4900, "days": 16, "draft": "16.5m (Compatible)"},
        ("South Africa", "Paradip"): {"nm": 5100, "days": 17, "draft": "17.5m (Compatible)"},
        ("South Africa", "Kolkata/Haldia"): {"nm": 5300, "days": 18, "draft": "12.5m (Draft Constrained)"}
    }
    meta = routes_meta.get((origin, destination), {"nm": 3500, "days": 12, "draft": "15.0m"})

    with st.container(border=True):
        st.caption("MARITIME ROUTE SPECIFICATIONS")
        r_col1, r_col2, r_col3 = st.columns([1, 2, 1])
        with r_col1:
            st.markdown(f"**{origin}**")
            st.caption("ORIGIN PORT")
        with r_col2:
            st.markdown(f"**{origin} ───────────────→ {destination}**")
            st.caption(f"~{meta['nm']:,} Nautical Miles • ~{meta['days']} Transit Days")
        with r_col3:
            st.markdown(f"**{destination}**")
            st.caption("DESTINATION PORT")

        st.caption(f"Port Draft Check: **{meta['draft']}** • Prototype route assumption")


def render_forecast_interpretation_box(title: str, text: str):
    """Renders a forecast interpretation text box using native Streamlit container."""
    with st.container(border=True):
        st.caption(title)
        st.write(text)
