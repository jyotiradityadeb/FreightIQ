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

        /* Navigation Top Bar */
        .fiq-nav-bar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 24px;
        }}
        .fiq-brand {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .fiq-nav-links {{
            display: flex;
            align-items: center;
            gap: 20px;
            font-size: 0.875rem;
            font-weight: 500;
        }}
        .fiq-nav-item {{
            color: var(--text-secondary);
            text-decoration: none;
            padding: 4px 0;
        }}
        .fiq-nav-item.active {{
            color: var(--primary);
            font-weight: 600;
            border-bottom: 2px solid var(--primary);
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
    """Renders real app shell top navigation bar matching commercial SaaS standard."""
    nav_items = [
        ("Overview", "Overview"),
        ("Markets", "Market Intelligence"),
        ("Forecasts", "Forecasts"),
        ("Scenarios", "Scenario Lab"),
        ("Chartering", "Charter Workbench"),
        ("Decision Twin", "Decision Twin"),
        ("Data", "Data Integration")
    ]

    links_html = ""
    for label, full_name in nav_items:
        is_active = "active" if (active_page_name.lower() in label.lower() or active_page_name.lower() in full_name.lower()) else ""
        links_html += f'<span class="fiq-nav-item {is_active}">{label}</span>'

    logo_svg = get_freightiq_logo_svg(150, 34)

    html = textwrap.dedent(f"""
        <div class="fiq-nav-bar">
            <div class="fiq-brand">
                {logo_svg}
            </div>
            <div class="fiq-nav-links">
                {links_html}
            </div>
            <div class="fiq-right-nav">
                <span class="badge-demo">DEMO MODE</span>
                <span class="badge-online">LIVE API</span>
                <div class="fiq-avatar" title="SteelProcure India Org">SP</div>
            </div>
        </div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


def render_sidebar_status():
    """Renders compact clean sidebar status module and theme switch button."""
    theme = get_active_theme()
    theme_label = "☀ Switch to Light Mode" if theme == "dark" else "🌙 Switch to Dark Mode"

    if st.sidebar.button(theme_label, key="sidebar_theme_switch_btn", use_container_width=True):
        toggle_theme()
        st.rerun()

    html = textwrap.dedent(f"""
        <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border); font-size: 0.78rem;">
            <div style="color: var(--text-secondary); font-weight: 600; text-transform: uppercase; margin-bottom: 8px; font-size: 0.7rem; letter-spacing: 0.05em;">SYSTEM STATUS</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span>Active Theme</span>
                <span style="font-weight: 600; text-transform: capitalize;">{theme} Mode</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span>Data Mode</span>
                <span style="color: #92400E; font-weight: 600;">Demo Dataset</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span>Forecast Engine</span>
                <span style="font-weight: 500;">Ensemble v2.4</span>
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
            "quantity_tonnes": 75000.0,
            "origin": "Australia",
            "destination": "Paradip",
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

