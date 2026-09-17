"""
FreightIQ UI Error Boundary Helper
"""

import streamlit as st
import traceback
from typing import Callable, Any, Optional


def safe_render_section(
    section_title: str,
    render_func: Callable[[], Any],
    fallback_message: str = "Component rendering temporarily unavailable. Fallback view enabled."
):
    """
    Safely executes render_func inside an error boundary.
    Exposes clean fallback message instead of raw traceback.
    """
    try:
        render_func()
    except Exception as e:
        st.warning(f"⚠ {section_title} — {fallback_message}")
        with st.expander("Technical Exception Details (Debug Only)"):
            st.code(str(e))
            st.caption(traceback.format_exc())
