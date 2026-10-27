"""Check that synthetic forecast bands do not steal hover from the center line.

Run while the local API and web server are available on ports 8000 and 3000.
"""

from playwright.sync_api import sync_playwright


def check_chart(page, route, chart_index, center_label):
    page.goto(f"http://localhost:3000/#/{route}", wait_until="domcontentloaded")
    chart = page.locator(".plotly-chart").nth(chart_index)
    page.wait_for_function(
        "index => document.querySelectorAll('.plotly-chart')[index]?._fullData?.length >= 6",
        arg=chart_index,
        timeout=90000,
    )
    chart.scroll_into_view_if_needed()
    position = chart.evaluate(
        """element => {
            const layout = element._fullLayout;
            const center = element._fullData.at(-1);
            const point = Math.min(4, center.x.length - 1);
            const box = element.getBoundingClientRect();
            return {
                x: box.left + layout.margin.l + layout.xaxis.d2p(center.x[point]),
                y: box.top + layout.margin.t + layout.yaxis.d2p(center.y[point]),
            };
        }"""
    )
    page.mouse.move(position["x"], position["y"])
    page.wait_for_function(
        "index => document.querySelectorAll('.plotly-chart')[index]"
        "?.querySelector('.hoverlayer')?.textContent.includes('Upper bound')",
        arg=chart_index,
        timeout=5000,
    )
    hover = chart.locator(".hoverlayer").text_content()
    assert center_label in hover, hover
    assert "Upper bound" in hover, hover
    assert "Lower bound" in hover, hover
    assert hover.index(center_label) < hover.index("Upper bound"), hover
    assert not chart.evaluate("element => element._fullLayout.yaxis.showspikes")


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        check_chart(page, "forecasts", 0, "Forecast")
        check_chart(page, "decision-twin", 1, "Simulated median")
        assert not errors, errors
        browser.close()
    print("PASS: Forecasts and Decision Twin hover show center, upper and lower values")


if __name__ == "__main__":
    main()
