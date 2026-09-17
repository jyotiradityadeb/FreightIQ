"""
FreightIQ Streamlit Page 1 — Control Tower
Real-Time-Style Disruption Intelligence & Charter Decision Monitoring
"""

import os
import sys

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Delegate rendering to app/Home.py
from app.Home import *
