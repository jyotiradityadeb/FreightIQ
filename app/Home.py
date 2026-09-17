"""
FreightIQ Primary Landing Page — Overview / Control Tower Command Centre
"""

import os
import sys

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st

st.set_page_config(
    page_title="FreightIQ — Overview",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

from app.views.control_tower_view import render_control_tower_page

render_control_tower_page(active_page_name="Overview")
