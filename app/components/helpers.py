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


def inject_custom_css():
    """Injects industrial maritime enterprise CSS design system."""
    css = textwrap.dedent("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'IBM Plex Sans', -apple-system, sans-serif;
            color: #E9EEF4;
        }

        .stApp {
            background-color: #0B1118;
        }

        /* Hide default Streamlit header and footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] {background: transparent;}

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #101720 !important;
            border-right: 1px solid #293541 !important;
        }

        /* Inputs & Selectboxes */
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
            background-color: #1A2531 !important;
            border: 1px solid #293541 !important;
            color: #E9EEF4 !important;
            border-radius: 5px !important;
        }

        /* Status Badges */
        .badge-demo {
            background-color: rgba(201, 130, 38, 0.15);
            color: #D9822B;
            border: 1px solid rgba(201, 130, 38, 0.3);
            font-size: 0.72rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            display: inline-block;
        }

        .badge-online {
            background-color: rgba(46, 139, 104, 0.15);
            color: #2E8B68;
            border: 1px solid rgba(46, 139, 104, 0.3);
            font-size: 0.72rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            display: inline-block;
        }

        /* Disclaimer Footer Bar */
        .disclaimer-footer {
            background-color: #151E28;
            border: 1px solid #293541;
            border-radius: 5px;
            padding: 10px 14px;
            color: #71808F;
            font-size: 0.75rem;
            margin-top: 28px;
        }
        </style>
    """).strip()
    st.markdown(css, unsafe_allow_html=True)


def render_top_shell(active_page_name: str = "Overview"):
    """Renders clean top header shell with page breadcrumbs and status indicators."""
    html = textwrap.dedent(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; margin-bottom: 20px; border-bottom: 1px solid #293541;">
            <div>
                <div style="font-size: 1.15rem; font-weight: 700; color: #E9EEF4; letter-spacing: -0.3px;">FreightIQ <span style="color: #A2ADBA; font-size: 0.85rem; font-weight: 400;">/ {active_page_name}</span></div>
                <div style="color: #71808F; font-size: 0.78rem;">Ministry of Steel & Industrial Bulk Import Decision Support • India East Coast Network</div>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <span class="badge-online">API ONLINE</span>
                <span class="badge-demo">DEMO DATA</span>
            </div>
        </div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


def render_sidebar_status():
    """Renders compact sidebar status module."""
    html = textwrap.dedent("""
        <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #293541; font-size: 0.75rem;">
            <div style="color: #71808F; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">SYSTEM STATUS</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="color: #71808F;">Data Mode</span>
                <span style="color: #D9822B; font-weight: 500;">Demo</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="color: #71808F;">Forecast Model</span>
                <span style="color: #E9EEF4; font-weight: 500;">Auto</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="color: #71808F;">Optimizer</span>
                <span style="color: #2E8B68; font-weight: 500;">Active</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #71808F;">API</span>
                <span style="color: #2E8B68; font-weight: 500;">Online</span>
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

