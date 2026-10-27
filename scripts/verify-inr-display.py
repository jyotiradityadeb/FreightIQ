"""Check that browser-facing FreightIQ pages show money in INR only."""

from pathlib import Path

from playwright.sync_api import sync_playwright


BASE = "http://127.0.0.1:3000"
VIEWS = [
    "overview", "control-tower", "operations-overview", "market-intelligence",
    "forecasts", "decision-twin", "charter-workbench", "decision-arena",
    "scenario-lab", "simulation-backtest", "data-integrations", "data-explorer",
]


def check(page, name):
    page.locator("h1").wait_for(timeout=90000)
    page.wait_for_function("!document.querySelector('.loading')", timeout=90000)
    assert not page.locator(".error-box").count(), f"{name}: error state"
    content = page.locator("#main").inner_text()
    assert "$" not in content, f"{name}: dollar symbol visible"
    assert "USD" not in content, f"{name}: dollar currency label visible"
    print(f"PASS {name}")


def main():
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900}, accept_downloads=True)
        page.on("pageerror", lambda error: errors.append(str(error)))
        for view in VIEWS:
            page.goto(f"{BASE}/#/{view}", wait_until="domcontentloaded")
            check(page, view)
            if view == "charter-workbench":
                page.get_by_text("Why alternatives ranked lower").click()
                check(page, "charter-workbench alternatives")
                with page.expect_download() as download_info:
                    page.locator("[data-action='candidate-csv']").click()
                csv = Path(download_info.value.path()).read_text(encoding="utf-8")
                assert "_inr" in csv.splitlines()[0]
                assert "_usd" not in csv.splitlines()[0]
            if view == "data-explorer":
                page.locator("[data-tab='1']").click()
                check(page, "data-explorer processed dataset")
                page.locator("[data-tab='2']").click()
                check(page, "data-explorer correlation chart")
                assert page.locator(".plotly-chart").count()
        assert not errors, errors
        browser.close()
    print("PASS: browser-facing values and explanations use INR")


if __name__ == "__main__":
    main()
