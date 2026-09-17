"""
FreightIQ Helper Utilities & Industrial Design System

Provides Indian currency/number formatting helpers (Cr, Lakh, INR/tonne),
industrial maritime CSS theme, global shell components, and cached dataset loaders.
"""

import os
import sys
import textwrap

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
from backend.data_loader import load_raw_datasets
from backend.features import generate_features
from backend.config import DEMO_BANNER_TEXT, DISCLAIMER_TEXT, DEMO_USD_INR_RATE


def format_inr(val_inr: float, is_per_tonne: bool = False) -> str:
    """
    Formats numerical values using standard Indian numbering system (Crore / Lakh / INR).
    Examples:
        18,580,000 -> ₹18.58 Cr
        4,260,000  -> ₹42.6 lakh
        2,477      -> ₹2,477
    """
    if val_inr is None or pd.isna(val_inr):
        return "₹0"

    abs_val = abs(val_inr)
    sign = "-" if val_inr < 0 else ""

    if is_per_tonne:
        return f"{sign}₹{abs_val:,.0f} / tonne"

    if abs_val >= 10_000_000:  # 1 Crore
        cr_val = abs_val / 10_000_000.0
        return f"{sign}₹{cr_val:.2f} Cr"
    elif abs_val >= 100_000:    # 1 Lakh
        lakh_val = abs_val / 100_000.0
        return f"{sign}₹{lakh_val:.1f} lakh"
    else:
        return f"{sign}₹{abs_val:,.0f}"


def usd_to_inr(usd_val: float) -> float:
    """Converts internal USD freight rates/costs to INR display values."""
    if usd_val is None or pd.isna(usd_val):
        return 0.0
    return float(usd_val) * DEMO_USD_INR_RATE


def format_tonnes(tonnes: float) -> str:
    """Formats cargo tonnage."""
    if tonnes is None or pd.isna(tonnes):
        return "0 t"
    return f"{tonnes:,.0f} t"


def format_hours(hours: float) -> str:
    """Formats waiting hours."""
    if hours is None or pd.isna(hours):
        return "0 h"
    return f"{hours:.0f} h"


def get_active_theme() -> str:
    """Returns current active theme ('light' or 'dark')."""
    if "fiq_theme" not in st.session_state:
        st.session_state["fiq_theme"] = "light"
    return st.session_state["fiq_theme"]


def toggle_theme():
    """Toggles theme state between light and dark."""
    curr = get_active_theme()
    st.session_state["fiq_theme"] = "dark" if curr == "light" else "light"


def inject_custom_css():
    """Injects modern SaaS design system with light/dark theme CSS variables."""
    theme = get_active_theme()
    is_dark = (theme == "dark")

    bg = "#0E1117" if is_dark else "#F6F8FB"
    surface = "#151A22" if is_dark else "#FFFFFF"
    surface_sec = "#1B212B" if is_dark else "#F8FAFC"
    text = "#F5F7FA" if is_dark else "#101828"
    text_sec = "#98A2B3" if is_dark else "#667085"
    border = "#2A3240" if is_dark else "#E4E7EC"
    primary = "#4D8DFF" if is_dark else "#1667D9"
    primary_hover = "#6BA1FF" if is_dark else "#1256B8"

    css = textwrap.dedent(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

        :root {{
            --bg: {bg};
            --surface: {surface};
            --surface-secondary: {surface_sec};
            --text: {text};
            --text-secondary: {text_sec};
            --border: {border};
            --primary: {primary};
            --primary-hover: {primary_hover};
        }}

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            color: var(--text) !important;
            -webkit-font-smoothing: antialiased;
        }}

        .stApp {{
            background-color: var(--bg) !important;
        }}

        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header[data-testid="stHeader"] {{
            background-color: transparent !important;
            height: 0px !important;
            min-height: 0px !important;
        }}
        div[data-testid="stHeader"] {{
            display: none !important;
        }}

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {{
            background-color: var(--surface) !important;
            border-right: 1px solid var(--border) !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
            color: var(--text-secondary) !important;
            font-size: 0.875rem !important;
        }}

        /* Native Containers & Card Styling */
        div[data-testid="stVerticalBlock"] > div[data-testid="stNativeContainer"],
        div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stBorderWrapper"] {{
            border: 1px solid var(--border) !important;
            background-color: var(--surface) !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
        }}

        /* Inputs, Selectboxes & Control Elements */
        div[data-baseweb="select"] > div, 
        div[data-baseweb="input"] > div,
        div[data-baseweb="base-input"] > div {{
            background-color: var(--surface-secondary) !important;
            border: 1px solid var(--border) !important;
            color: var(--text) !important;
            border-radius: 6px !important;
            font-size: 0.875rem !important;
        }}

        /* Typography Hierarchy Overrides */
        h1, h2, h3, h4, h5, h6 {{
            color: var(--text) !important;
            font-weight: 600 !important;
            letter-spacing: -0.02em !important;
        }}
        p, span, label, div {{
            color: var(--text);
        }}
        h1 {{ font-size: 1.75rem !important; margin-bottom: 0.5rem !important; }}
        h2 {{ font-size: 1.25rem !important; margin-top: 1rem !important; margin-bottom: 0.5rem !important; }}
        h3 {{ font-size: 1.05rem !important; margin-top: 0.75rem !important; margin-bottom: 0.25rem !important; }}

        /* Buttons */
        div.stButton > button {{
            border-radius: 6px !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
            padding: 0.45rem 1rem !important;
            transition: all 0.15s ease-in-out !important;
        }}
        div.stButton > button[kind="primary"] {{
            background-color: var(--primary) !important;
            color: #FFFFFF !important;
            border: 1px solid var(--primary) !important;
        }}
        div.stButton > button[kind="secondary"] {{
            background-color: var(--surface) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
        }}

        /* Metric & Badges */
        div[data-testid="stMetricValue"] {{
            font-size: 1.625rem !important;
            font-weight: 600 !important;
            color: var(--text) !important;
        }}
        div[data-testid="stMetricLabel"] {{
            font-size: 0.8125rem !important;
            font-weight: 500 !important;
            color: var(--text-secondary) !important;
            text-transform: uppercase !important;
        }}

        /* Top Navigation Bar Styling */
        div[data-testid="stHorizontalBlock"]:has(button[key*="topnav_"]) {{
            align-items: center !important;
            gap: 6px !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
        }}

        button[key*="topnav_"] {{
            white-space: nowrap !important;
            word-break: keep-all !important;
            overflow-wrap: normal !important;
            height: 42px !important;
            min-height: 42px !important;
            max-height: 42px !important;
            padding: 0px 16px !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
        }}

        button[key*="topnav_"] p,
        button[key*="topnav_"] span,
        button[key*="topnav_"] div,
        button[key*="topnav_"] [data-testid="stMarkdownContainer"] p {{
            white-space: nowrap !important;
            word-break: keep-all !important;
            overflow-wrap: normal !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            line-height: 1 !important;
            margin: 0 !important;
        }}

        /* Footer */
        .disclaimer-footer {{
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 10px 14px;
            color: var(--text-secondary);
            font-size: 0.75rem;
            margin-top: 32px;
        }}
        </style>
    """).strip()

    st.markdown(css, unsafe_allow_html=True)


def get_freightiq_logo_svg(width: int = 140, height: int = 32) -> str:
    """Returns SVG markup for the FreightIQ geometric vessel/route logo & wordmark."""
    theme = get_active_theme()
    text_col = "#F5F7FA" if theme == "dark" else "#111827"
    return textwrap.dedent(f"""
        <svg width="{width}" height="{height}" viewBox="0 0 175 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- Geometric Icon: Keel + Vector Arrow + Letter F -->
            <rect x="2" y="6" width="28" height="28" rx="6" fill="#1667D9"/>
            <path d="M10 13H22M10 20H19M10 13V27" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>
            <path d="M19 20L22 17M22 17L19 14" stroke="#66E6FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <!-- Wordmark -->
            <text x="38" y="26" font-family="'Inter', sans-serif" font-weight="700" font-size="20" fill="{text_col}" letter-spacing="-0.5">Freight<tspan fill="#1667D9">IQ</tspan></text>
        </svg>
    """).strip()


def render_top_shell(active_page_name: str = "Overview"):
    """Renders functional app shell top navigation bar matching commercial SaaS standard."""
    from app.navigation import (
        DECISION_TWIN_PAGE,
        OPERATIONS_PAGE,
        MARKET_PAGE,
        FORECAST_PAGE,
        CHARTER_PAGE,
        SCENARIO_PAGE,
        VALIDATION_PAGE,
        DATA_INTEGRATION_PAGE,
        DATA_EXPLORER_PAGE,
        navigate_to
    )

    nav_items = [
        ("Overview", "Home.py"),
        ("Decision Twin", DECISION_TWIN_PAGE),
        ("Operations", OPERATIONS_PAGE),
        ("Markets", MARKET_PAGE),
        ("Forecasts", FORECAST_PAGE),
        ("Chartering", CHARTER_PAGE),
        ("Scenarios", SCENARIO_PAGE),
        ("Backtesting", VALIDATION_PAGE),
        ("Data", DATA_INTEGRATION_PAGE),
        ("Explorer", DATA_EXPLORER_PAGE),
    ]

    col_widths = [1.8, 1.05, 1.25, 1.15, 1.0, 1.1, 1.2, 1.1, 1.25, 0.9, 1.0]

    def _is_active(lbl: str, p: str) -> bool:
        lbl_l = lbl.lower()
        p_l = p.lower()
        if lbl_l == p_l:
            return True
        if lbl_l == "overview" and p_l in ("overview", "control tower", "home"):
            return True
        if lbl_l == "decision twin" and "decision twin" in p_l:
            return True
        if lbl_l == "operations" and "operations" in p_l:
            return True
        if lbl_l == "markets" and "market" in p_l:
            return True
        if lbl_l == "forecasts" and "forecast" in p_l:
            return True
        if lbl_l == "chartering" and ("charter" in p_l or "optimizer" in p_l):
            return True
        if lbl_l == "scenarios" and ("scenario" in p_l or "lab" in p_l):
            return True
        if lbl_l == "backtesting" and ("backtest" in p_l or "simulation" in p_l or "validation" in p_l):
            return True
        if lbl_l == "data" and ("data integration" in p_l or p_l == "data"):
            return True
        if lbl_l == "explorer" and ("data explorer" in p_l or p_l == "explorer"):
            return True
        return False

    with st.container():
        cols = st.columns(col_widths)
        with cols[0]:
            st.markdown(get_freightiq_logo_svg(175, 36), unsafe_allow_html=True)

        for idx, (label, target_page) in enumerate(nav_items, start=1):
            with cols[idx]:
                is_active = _is_active(label, active_page_name)
                btn_kind = "primary" if is_active else "secondary"
                if st.button(label, key=f"topnav_{label}", type=btn_kind, use_container_width=True):
                    if target_page == "Home.py":
                        try:
                            st.switch_page("Home.py")
                        except Exception:
                            st.switch_page("pages/1_Control_Tower.py")
                    else:
                        navigate_to(target_page)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)



def render_sidebar_status():
    """Renders compact clean sidebar status module and theme switch button."""
    theme = get_active_theme()
    theme_label = "☀ Switch to Light Mode" if theme == "dark" else "🌙 Switch to Dark Mode"

    if st.sidebar.button(theme_label, key="sidebar_theme_switch_btn", use_container_width=True):
        toggle_theme()
        st.rerun()

    data_mode = st.session_state.get("data_mode", "DEMO")

    html = textwrap.dedent(f"""
        <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border); font-size: 0.78rem;">
            <div style="color: var(--text-secondary); font-weight: 600; text-transform: uppercase; margin-bottom: 8px; font-size: 0.7rem; letter-spacing: 0.05em;">SYSTEM STATUS</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span>Active Theme</span>
                <span style="font-weight: 600; text-transform: capitalize;">{theme} Mode</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span>Data Mode</span>
                <span style="color: #92400E; font-weight: 600;">{data_mode}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span>Forecast Engine</span>
                <span style="font-weight: 500;">Auto Model Selection</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span>Optimizer</span>
                <span style="color: #10B981; font-weight: 600;">Active</span>
            </div>
        </div>
    """).strip()
    st.sidebar.markdown(html, unsafe_allow_html=True)




def render_disclaimer():
    """Renders footer disclaimer."""
    html = textwrap.dedent(f"""
        <div class="disclaimer-footer">
            <strong>Prototype Disclaimer:</strong> {DISCLAIMER_TEXT}
        </div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


@st.cache_data
def get_cached_processed_data():
    """Loads and caches raw dataset with feature engineering."""
    raw_df = load_raw_datasets()
    feat_df = generate_features(raw_df)
    return feat_df


def get_active_shipment_context() -> dict:
    """Returns the global active shipment workspace context from st.session_state."""
    if "shipment_workspace" not in st.session_state:
        st.session_state["shipment_workspace"] = {
            "shipment_id": "FIQ-2026-0001",
            "cargo_type": "Coking Coal",
            "cargo_id": "coking_coal",
            "quantity_tonnes": 75000.0,
            "origin_country": "Australia",
            "origin": "Hay Point",
            "origin_port_id": "AU_HPT",
            "destination_country": "India",
            "destination": "Paradip",
            "destination_port_id": "IN_PDP",
            "vessel_class": "Auto",
            "laytime_hours": 72.0,
            "demurrage_rate": 22000.0,
            "risk_tolerance": "Medium",
            "earliest_date": None,
            "latest_date": None
        }
    return st.session_state["shipment_workspace"]


def update_active_shipment_context(**kwargs):
    """Updates the global active shipment workspace context across all pages."""
    ctx = get_active_shipment_context()
    for k, v in kwargs.items():
        if v is not None:
            ctx[k] = v
    st.session_state["shipment_workspace"] = ctx


def render_procurement_input_toolbar(key_prefix: str = "toolbar", show_laycan: bool = True, laycan_default_days: int = 14) -> dict:
    """
    Renders standardized SaaS procurement toolbar with Country -> Port cascading selectboxes,
    canonical domain data dropdowns, route calibration status badge, and subtle port metadata.
    """
    from backend.domain.commodities import get_all_commodities, get_commodity
    from backend.domain.ports import (
        get_origin_countries,
        get_destination_countries,
        get_ports_for_country,
        get_port_by_id
    )
    from backend.domain.routes import resolve_route
    from datetime import datetime, timedelta

    shipment_ctx = get_active_shipment_context()
    commodities = list(get_all_commodities().values())
    cargo_names = [c.display_name for c in commodities]

    # Preselect current context
    curr_cargo = shipment_ctx.get("cargo_type", "Coking Coal")
    cargo_idx = cargo_names.index(curr_cargo) if curr_cargo in cargo_names else 0

    origin_countries = get_origin_countries()
    curr_o_country = shipment_ctx.get("origin_country", "Australia")
    if curr_o_country not in origin_countries:
        curr_o_country = "Australia"
    o_country_idx = origin_countries.index(curr_o_country)

    dest_countries = get_destination_countries()
    curr_d_country = shipment_ctx.get("destination_country", "India")
    if curr_d_country not in dest_countries:
        curr_d_country = "India"
    d_country_idx = dest_countries.index(curr_d_country)

    if show_laycan:
        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.1, 1.1, 1.2, 1.2, 1.5])
    else:
        c1, c2, c3, c4, c5 = st.columns([1.5, 1.1, 1.2, 1.3, 1.3])

    with c1:
        sel_cargo_name = st.selectbox("Cargo", cargo_names, index=cargo_idx, key=f"{key_prefix}_cargo")
        selected_commodity = get_commodity(sel_cargo_name)
        sel_cargo_id = selected_commodity.commodity_id if selected_commodity else "coking_coal"

    with c2:
        sel_qty = st.number_input("Quantity (t)", min_value=10000.0, max_value=250000.0, value=float(shipment_ctx.get("quantity_tonnes", 75000.0)), step=5000.0, key=f"{key_prefix}_qty")

    with c3:
        sel_o_country = st.selectbox("Origin Country", origin_countries, index=o_country_idx, key=f"{key_prefix}_o_country")

    with c4:
        o_ports = get_ports_for_country(sel_o_country, is_origin=True)
        o_port_labels = [f"{p.port_name} ({p.port_id})" for p in o_ports]
        curr_o_port_id = shipment_ctx.get("origin_port_id", "AU_HPT")
        o_port_idx = 0
        for i, p in enumerate(o_ports):
            if p.port_id == curr_o_port_id or p.port_name == shipment_ctx.get("origin"):
                o_port_idx = i
                break
        sel_o_port_lbl = st.selectbox("Origin Port", o_port_labels, index=o_port_idx, key=f"{key_prefix}_o_port")
        sel_o_port = o_ports[o_port_labels.index(sel_o_port_lbl)]

    with c5:
        d_ports = get_ports_for_country(curr_d_country, is_origin=False)
        d_port_labels = [f"{p.port_name} ({p.port_id})" for p in d_ports]
        curr_d_port_id = shipment_ctx.get("destination_port_id", "IN_PDP")
        d_port_idx = 0
        for i, p in enumerate(d_ports):
            if p.port_id == curr_d_port_id or p.port_name == shipment_ctx.get("destination"):
                d_port_idx = i
                break
        sel_d_port_lbl = st.selectbox("Destination Port", d_port_labels, index=d_port_idx, key=f"{key_prefix}_d_port")
        sel_d_port = d_ports[d_port_labels.index(sel_d_port_lbl)]

    laycan_dates = None
    if show_laycan:
        with c6:
            today_dt = datetime.now()
            laycan_dates = st.date_input("Laycan Window", value=[today_dt + timedelta(days=1), today_dt + timedelta(days=laycan_default_days)], key=f"{key_prefix}_laycan")

    # Route resolution check
    route_res = resolve_route(sel_o_port.port_id, sel_d_port.port_id)

    # Status badge & subtle metadata
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    m_col1, m_col2 = st.columns([2.5, 1])

    with m_col1:
        vessel_str = ", ".join(sel_d_port.supported_vessel_classes)
        meta_html = f"""
        <div style="font-size: 0.8rem; color: var(--text-secondary);">
            Origin: <strong>{sel_o_port.port_name}</strong> ({sel_o_port.region}, {sel_o_port.country} | Draft: {sel_o_port.max_draft_m}m)
            &nbsp;→&nbsp;
            Destination: <strong>{sel_d_port.port_name}</strong> ({sel_d_port.region}, {sel_d_port.country} | Max Draft: {sel_d_port.max_draft_m}m)
        </div>
        """
        st.markdown(meta_html, unsafe_allow_html=True)

    with m_col2:
        if route_res.is_calibrated:
            badge_html = "<div style='text-align: right;'><span style='background-color: #DEF7EC; color: #03543F; font-size: 0.75rem; font-weight: 600; padding: 3px 8px; border-radius: 4px;'>🟢 DEMO-CALIBRATED ROUTE</span></div>"
        else:
            badge_html = "<div style='text-align: right;'><span style='background-color: #FEF3C7; color: #92400E; font-size: 0.75rem; font-weight: 600; padding: 3px 8px; border-radius: 4px;'>⚠️ CATALOG ONLY — optimization unavailable</span></div>"
        st.markdown(badge_html, unsafe_allow_html=True)

    # Sync to global active shipment workspace context
    update_active_shipment_context(
        cargo_type=sel_cargo_name,
        cargo_id=sel_cargo_id,
        quantity_tonnes=sel_qty,
        origin_country=sel_o_country,
        origin=sel_o_port.port_name,
        origin_port_id=sel_o_port.port_id,
        destination_country=curr_d_country,
        destination=sel_d_port.port_name,
        destination_port_id=sel_d_port.port_id
    )

    return {
        "cargo_type": sel_cargo_name,
        "cargo_id": sel_cargo_id,
        "quantity_tonnes": sel_qty,
        "origin_country": sel_o_country,
        "origin": sel_o_port.port_name,
        "origin_port_id": sel_o_port.port_id,
        "destination_country": curr_d_country,
        "destination": sel_d_port.port_name,
        "destination_port_id": sel_d_port.port_id,
        "laycan_dates": laycan_dates,
        "route_resolution": route_res
    }

