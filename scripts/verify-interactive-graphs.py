"""Smoke-check every interactive graph against the running local app."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'design/visual-verification/implementation'
PAGES = ['overview', 'control-tower', 'operations-overview', 'market-intelligence',
         'forecasts', 'decision-twin']

def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900}, accept_downloads=True)
        page.on('pageerror', lambda e: errors.append(str(e)))
        for route in PAGES:
            page.goto(f'http://127.0.0.1:3000/#/{route}', wait_until='domcontentloaded')
            page.locator('.plotly-chart .main-svg').first.wait_for(timeout=90000)
            assert page.locator('.plotly-chart .main-svg').count() >= 1, route
            print(route, page.locator('.plotly-chart').count(), 'interactive graph(s)')
        # Zoom, pan, hover and PNG export use Plotly's own controls.
        page.goto('http://127.0.0.1:3000/#/forecasts', wait_until='domcontentloaded')
        page.locator('.plotly-chart .main-svg').first.wait_for(timeout=90000)
        first = page.locator('.plotly-chart').first
        first.scroll_into_view_if_needed()
        page.evaluate("Plotly.Fx.hover(document.querySelector('.plotly-chart'), [{curveNumber:0, pointNumber:15}])")
        page.locator('.plotly-chart .hoverlayer .hovertext').first.wait_for(timeout=5000)
        before = page.evaluate("document.querySelector('.plotly-chart')._fullLayout.xaxis.range.slice()")
        zoom = first.locator('.modebar-btn[data-title="Zoom in"]')
        zoom.click()
        after = page.evaluate("document.querySelector('.plotly-chart')._fullLayout.xaxis.range.slice()")
        assert before != after, 'Zoom control did not alter the visible date range'
        first.locator('.modebar-btn[data-title="Reset axes"]').click()
        reset = page.evaluate("document.querySelector('.plotly-chart')._fullLayout.xaxis.range.slice()")
        assert reset != after, 'Reset control did not restore the date range'
        first.locator('.modebar-btn[data-title="Pan"]').click()
        assert page.evaluate("document.querySelector('.plotly-chart')._fullLayout.dragmode") == 'pan'
        with page.expect_download(timeout=15000) as download:
            first.locator('.modebar-btn[data-title="Download plot as a PNG"]').click()
        assert download.value.suggested_filename.endswith('.png')
        page.locator('#compare-details summary').click()
        page.locator('[data-action="compare-routes"]').click()
        page.locator('#compare-result .plotly-chart .main-svg').first.wait_for(timeout=90000)
        assert page.locator('#compare-result .plotly-chart').count() == 1
        page.screenshot(path=str(OUT / 'interactive-forecast-1440.png'), full_page=False)
        page.goto('http://127.0.0.1:3000/#/market-intelligence', wait_until='domcontentloaded')
        page.locator('#market-start').fill('2026-05-01')
        page.locator('#market-end').fill('2026-08-31')
        page.locator('[data-action="market-filter"]').click()
        page.locator('#market-chart .plotly-chart .main-svg').first.wait_for(timeout=90000)
        page.goto('http://127.0.0.1:3000/#/data-explorer', wait_until='domcontentloaded')
        page.locator('[data-tab]').nth(2).click()
        page.locator('.plotly-chart .main-svg').first.wait_for(timeout=90000)
        print('correlation matrix: interactive')
        page.goto('http://127.0.0.1:3000/#/simulation-backtest', wait_until='domcontentloaded')
        page.locator('#backtest-start').fill('2026-06-01')
        page.locator('#backtest-end').fill('2026-07-01')
        page.locator('[data-action="run-backtest"]').click()
        page.locator('.plotly-chart .main-svg').first.wait_for(timeout=90000)
        assert page.locator('.plotly-chart').count() == 2
        print('backtest: 2 interactive graphs')
        assert not errors, errors
        browser.close()
    print('PASS: interactive graph rendering and zoom/reset')

if __name__ == '__main__':
    main()
