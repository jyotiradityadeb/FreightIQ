"""Browser checks for the local Voyage Intelligence map and its fallback."""
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "design" / "visual-verification" / "implementation"
BASE = "http://127.0.0.1:3000"


def wait_for_map(page):
    page.locator(".voyage-map-surface canvas").wait_for(timeout=90000)
    page.get_by_text("ILLUSTRATIVE CORRIDOR · ROUTING NOT VERIFIED").wait_for()


def main():
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"{BASE}/#/overview", wait_until="domcontentloaded")
        wait_for_map(page)
        assert page.get_by_role("heading", name="VOYAGE INTELLIGENCE").is_visible()
        assert page.get_by_text("Hay Point → Paradip", exact=False).count() >= 1
        assert "4,899 NM" in page.locator("[data-voyage-distance]").inner_text()
        page.get_by_role("button", name="Hay Point, Australia. Open port details").click()
        assert page.get_by_text("North Queensland Bulk Ports").is_visible()
        page.get_by_role("tab", name="ALTERNATIVES").click()
        assert page.get_by_text("Navigation alternatives unavailable").is_visible()
        page.get_by_role("tab", name="SELECTED ROUTE").click()
        page.get_by_role("button", name="Reset map view").click()
        page.get_by_role("button", name="Hay Point, Australia. Open port details").click()
        page.locator("#voyage-map-card").screenshot(path=str(OUT / "voyage-map-desktop-1440.png"))
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Desktop horizontal overflow"

        page.goto(f"{BASE}/#/charter-workbench", wait_until="domcontentloaded")
        page.locator("#charter-origin").select_option("AU_GLT")
        page.get_by_role("button", name="Solve Candidates").click()
        page.get_by_text("Route Gladstone → Paradip", exact=False).wait_for(timeout=90000)
        page.goto(f"{BASE}/#/control-tower", wait_until="domcontentloaded")
        wait_for_map(page)
        assert page.get_by_text("Gladstone → Paradip", exact=False).count() >= 1
        assert "5,063 NM" in page.locator("[data-voyage-distance]").inner_text()
        page.get_by_role("button", name="Gladstone, Australia. Open port details").click()
        assert page.get_by_text("Gladstone Ports Corporation").is_visible()

        page.set_viewport_size({"width": 390, "height": 844})
        page.reload(wait_until="domcontentloaded")
        wait_for_map(page)
        page.wait_for_timeout(750)  # allow the WebGL map's first painted frame after reload
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Mobile horizontal overflow"
        page.locator("#voyage-map-card").screenshot(path=str(OUT / "voyage-map-mobile-390.png"))

        fallback = browser.new_page(viewport={"width": 800, "height": 700})
        fallback.route("**/geo/voyages.json", lambda route: route.fulfill(status=503, body="unavailable"))
        fallback.goto(f"{BASE}/#/overview", wait_until="domcontentloaded")
        fallback.get_by_text("Map data unavailable. Select a route again to retry.").wait_for(timeout=90000)
        assert fallback.get_by_role("heading", name="VOYAGE INTELLIGENCE").is_visible()
        assert fallback.get_by_text("NOT EVALUATED").is_visible()
        missing = browser.new_page(viewport={"width": 800, "height": 700})
        missing.route("**/geo/voyages.json", lambda route: route.fulfill(status=200, content_type="application/json", body='{"routes":{}}'))
        missing.goto(f"{BASE}/#/overview", wait_until="domcontentloaded")
        missing.get_by_text("No geographic corridor is available for this shipment.").wait_for(timeout=90000)
        assert missing.get_by_role("heading", name="VOYAGE INTELLIGENCE").is_visible()

        scenario = browser.new_page(viewport={"width": 1100, "height": 800})
        scenario.goto(f"{BASE}/#/scenario-lab", wait_until="domcontentloaded")
        scenario.locator('[data-preset="Paradip Congestion"]').click(timeout=90000)
        scenario.get_by_role("button", name="Run Scenario Simulation").click()
        scenario.get_by_role("heading", name="Impact Preview").wait_for(timeout=90000)
        scenario.goto(f"{BASE}/#/overview", wait_until="domcontentloaded")
        wait_for_map(scenario)
        assert scenario.get_by_text("SCENARIO INPUT · 80% congestion shock", exact=False).is_visible()
        assert scenario.get_by_text("SCENARIO MODEL COST", exact=False).is_visible()
        assert not errors, errors
        browser.close()
    print("PASS: desktop/mobile map, port details, alternative state, route selection, fallback")


if __name__ == "__main__":
    main()
