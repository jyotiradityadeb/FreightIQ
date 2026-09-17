"""
FreightIQ Central Navigation Registry

Defines authoritative relative page paths to prevent stale st.switch_page links.
"""

import os
import streamlit as st

# Centralized Streamlit Page Constants
CONTROL_TOWER_PAGE = "pages/1_Control_Tower.py"
DECISION_TWIN_PAGE = "pages/2_Decision_Twin.py"
OPERATIONS_PAGE = "pages/3_Operations_Overview.py"
MARKET_PAGE = "pages/4_Market_Overview.py"
FORECAST_PAGE = "pages/5_Forecasting.py"
CHARTER_PAGE = "pages/6_Charter_Optimizer.py"
SCENARIO_PAGE = "pages/7_Scenario_Lab.py"
VALIDATION_PAGE = "pages/8_Backtesting.py"
DATA_INTEGRATION_PAGE = "pages/9_Data_Integration.py"
DATA_EXPLORER_PAGE = "pages/10_Data_Explorer.py"


def navigate_to(page_constant: str):
    """Safely switches to target Streamlit page constant."""
    try:
        st.switch_page(page_constant)
    except Exception as e:
        # Fallback to Home if page missing
        st.error(f"Navigation error: Page '{page_constant}' not found ({e})")


def get_all_pages():
    """Returns list of all registered Streamlit page path constants."""
    return [
        CONTROL_TOWER_PAGE,
        DECISION_TWIN_PAGE,
        OPERATIONS_PAGE,
        MARKET_PAGE,
        FORECAST_PAGE,
        CHARTER_PAGE,
        SCENARIO_PAGE,
        VALIDATION_PAGE,
        DATA_INTEGRATION_PAGE,
        DATA_EXPLORER_PAGE
    ]

