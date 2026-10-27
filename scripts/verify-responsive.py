"""Exercise the current web UI at SIH demonstration viewport sizes.

Screenshots are generated evidence and must not be committed.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE = "http://127.0.0.1:3000"
OUT = Path(__file__).resolve().parents[1] / "design" / "visual-verification" / "implementation"
SIZES = [(1920, 1080), (1440, 900), (1366, 768), (390, 844)]
VIEWS = ["decision-arena", "overview", "scenario-lab", "forecasts"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    issues = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.on("pageerror", lambda error: issues.append(f"JavaScript: {error}"))
        page.on("console", lambda message: issues.append(f"Console: {message.text}") if message.type == "error" else None)
        page.on("response", lambda response: issues.append(f"HTTP {response.status}: {response.url}")
                if response.status >= 400 and ("/api/" in response.url or "/geo/" in response.url or "/maplibre-" in response.url) else None)
        for view in VIEWS:
            page.goto(f"{BASE}/#/{view}", wait_until="domcontentloaded")
            page.locator("h1").wait_for(timeout=90000)
            page.wait_for_function("!document.querySelector('.loading')", timeout=90000)
            if view == "overview":
                page.locator(".voyage-map-surface canvas").wait_for(timeout=90000)
            if view == "decision-arena":
                page.locator("#arena-sample").wait_for(timeout=90000)
                slider = page.locator("#arena-sample")
                slider.evaluate("el => { el.value = '1'; el.dispatchEvent(new Event('input', {bubbles: true})); }")
                assert page.locator("#arena-sample-number").inner_text() == "2"
            for width, height in SIZES:
                page.set_viewport_size({"width": width, "height": height})
                page.wait_for_timeout(250)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"{view} overflow at {width}x{height}"
                assert not page.locator(".error-box").count(), f"{view} error state at {width}x{height}"
                assert page.locator("h1").is_visible(), f"{view} heading hidden at {width}x{height}"
                if width == 390:
                    menu = page.locator('[data-action="menu"]')
                    assert menu.is_visible(), f"mobile menu hidden on {view}"
                    menu.click()
                    assert "open" in page.locator("#sidebar").get_attribute("class")
                    assert page.locator("#sidebar .nav").first.is_visible()
                    menu.click()
                    assert "open" not in page.locator("#sidebar").get_attribute("class")
                    page.wait_for_timeout(250)
                page.screenshot(path=str(OUT / f"responsive-{view}-{width}x{height}.png"))
                if view == "overview":
                    page.locator("#voyage-map-card").screenshot(path=str(OUT / f"responsive-voyage-map-{width}x{height}.png"))
                if view == "decision-arena":
                    page.locator(".arena-replay").screenshot(path=str(OUT / f"responsive-future-replay-{width}x{height}.png"))
                print(f"PASS {view} {width}x{height}")
        assert not issues, "\n".join(issues)
        browser.close()
    print("PASS: replay, map, scenario, forecasts, sidebar, console and API")


if __name__ == "__main__":
    main()
