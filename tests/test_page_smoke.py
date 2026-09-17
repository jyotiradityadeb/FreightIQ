"""
Page-render smoke test suite using Streamlit AppTest.
Verifies all 10 pages execute cleanly without runtime exceptions.
"""

import pytest
from streamlit.testing.v1 import AppTest


@pytest.mark.parametrize("page_file", [
    "app/Home.py",
    "app/pages/1_Control_Tower.py",
    "app/pages/2_Decision_Twin.py",
    "app/pages/3_Operations_Overview.py",
    "app/pages/4_Market_Overview.py",
    "app/pages/5_Forecasting.py",
    "app/pages/6_Charter_Optimizer.py",
    "app/pages/7_Scenario_Lab.py",
    "app/pages/8_Backtesting.py",
    "app/pages/9_Data_Integration.py",
    "app/pages/10_Data_Explorer.py",
])
def test_page_renders_without_exceptions(page_file):
    at = AppTest.from_file(page_file, default_timeout=30)
    at.run(timeout=30)
    assert len(at.exception) == 0, f"Exception rendered on {page_file}: {[e.value for e in at.exception]}"


