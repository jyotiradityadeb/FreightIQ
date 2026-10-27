"""Browser regression: a Workbench PDF must match the active shipment and vessel constraint.

Run against the local Python API and web server on ports 8000 and 3000.
"""

from io import BytesIO

from playwright.sync_api import sync_playwright
from pypdf import PdfReader


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900}, accept_downloads=True)
        page.goto("http://localhost:3000/#/charter-workbench", wait_until="domcontentloaded")
        page.locator("#quantity").wait_for(timeout=90000)
        assert "Gladstone" in page.locator(".shipment-chip").inner_text()

        # At 60,000 tonnes Auto selects Supramax on this route. A Panamax-only
        # solve therefore exposes any report request that silently reverts to Auto.
        page.locator("#quantity").fill("60000")
        page.locator(".constraint-disclosure summary").click()
        page.locator("#vessel-class").select_option("Panamax")
        page.locator('[data-action="solve"]').click()
        page.wait_for_function(
            "document.querySelector('#main h1') && "
            "document.querySelector('#main')?.textContent.includes('60,000')",
            timeout=90000,
        )
        recommendation = page.locator(".section").filter(has_text="Selected Recommendation").first
        assert "Panamax" in recommendation.inner_text()

        requests = []
        page.on(
            "request",
            lambda request: requests.append(request.post_data_json)
            if request.url.endswith("/api/web/report") else None,
        )
        with page.expect_download(timeout=90000) as download:
            page.locator('[data-action="report"]').first.click()
        pdf = PdfReader(BytesIO(download.value.path().read_bytes()))
        content = "\n".join(sheet.extract_text() for sheet in pdf.pages)
        assert requests[0]["route_key"] == "AU_GLT -> IN_PDP"
        assert requests[0]["vessel_class"] == "Panamax"
        assert requests[0]["quantity_tonnes"] == 60000
        assert "Gladstone" in content
        assert "60,000 tonnes" in content
        assert "Recommended Vessel:\nPanamax" in content
        assert "Not evaluated for this report" not in content
        assert not page.locator(".error-box").count()

        page.evaluate("location.hash = '#/operations-overview'")
        page.wait_for_function(
            "document.querySelector('#main h1') && !document.querySelector('#main .loading')",
            timeout=90000,
        )
        operations = page.locator("#main").inner_text()
        assert "Gladstone" in operations
        assert "60,000 t Coking Coal" in operations
        assert "FIXED CASE" not in operations
        assert not page.locator(".error-box").count()
        browser.close()
    print("PASS: PDF and Operations Overview match route, cargo quantity and vessel constraint")


if __name__ == "__main__":
    main()
