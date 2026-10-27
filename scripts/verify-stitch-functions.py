"""Browser smoke checks against isolated FastAPI/Node servers on 8001/3001."""
from pathlib import Path
from playwright.sync_api import sync_playwright

PAGES = ['overview','control-tower','operations-overview','market-intelligence',
         'forecasts','decision-twin','charter-workbench','scenario-lab',
         'simulation-backtest','data-integrations','data-explorer']

def ready(page, route):
    page.goto(f'http://localhost:3001/#/{route}', wait_until='domcontentloaded')
    page.locator('#main h1').wait_for(timeout=90000)
    assert not page.locator('.error-box').count(), f'{route}: {page.locator(".error-box").inner_text()}'

def main():
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1440,'height':900})
        page.on('pageerror', lambda err: errors.append(str(err)))
        for route in PAGES:
            ready(page,route)
            print('PAGE',route)
        ready(page,'control-tower')
        chart=page.locator('.plotly-chart').first
        chart.locator('.main-svg').first.wait_for(timeout=90000)
        original=page.evaluate("document.querySelector('.plotly-chart')._fullLayout.xaxis.range.slice()")
        chart.locator('.modebar-btn[data-title="Zoom in"]').click()
        assert page.evaluate("document.querySelector('.plotly-chart')._fullLayout.xaxis.range.slice()")!=original
        chart.locator('.modebar-btn[data-title="Reset axes"]').click()
        ready(page,'forecasts')
        page.locator('#forecast-horizon').select_option('7')
        page.locator('[data-action="update-forecast"]').click()
        page.locator('#main h1').wait_for()
        assert not page.locator('.error-box').count()
        ready(page,'charter-workbench')
        page.locator('[data-action="solve"]').click()
        page.get_by_text('saved.',exact=False).wait_for(timeout=90000)
        assert page.locator('.error-box').count()==0
        page.locator('#candidate-filter').fill('Panamax')
        assert page.locator('#candidate-filter').input_value()=='Panamax'
        with page.expect_download() as download:
            page.locator('[data-action="candidate-csv"]').click()
        assert download.value.suggested_filename.endswith('.csv')
        ready(page,'scenario-lab')
        page.locator('[data-preset="Freight Rate Spike"]').click()
        assert page.locator('#shock-freight').input_value()=='25'
        page.locator('#shock-freight').fill('20')
        assert page.locator('output[for="shock-freight"]').inner_text()=='20'
        page.locator('[data-action="run-scenario"]').click()
        page.locator('#main h1').wait_for(timeout=90000)
        assert not page.locator('.error-box').count()
        assert '— vessel' not in page.locator('.impact-stack').inner_text()
        ready(page,'data-integrations')
        for tab in range(8):
            page.locator('[data-tab]').nth(tab).click()
            page.locator('#main h1').wait_for(timeout=90000)
            assert not page.locator('.error-box').count()
        page.locator('[data-tab]').nth(2).click()
        page.locator('[data-action="record-note"]').click()
        page.get_by_text('recorded',exact=False).wait_for(timeout=30000)
        ready(page,'data-explorer')
        for tab in range(5):
            page.locator('[data-tab]').nth(tab).click()
            page.locator('#main h1').wait_for(timeout=90000)
            assert not page.locator('.error-box').count()
        page.locator('[data-tab]').nth(0).click()
        header=page.locator('.table-outer th[data-sort]').first
        header.click()
        assert header.get_attribute('aria-sort')=='ascending'
        page.locator('[data-table-fullscreen]').first.click()
        page.wait_for_function('Boolean(document.fullscreenElement)', timeout=5000)
        page.evaluate('document.exitFullscreen()')
        page.locator('[data-tab]').nth(4).click()
        sample=Path('design/visual-verification/upload-smoke.csv')
        sample.write_text('route_key,date,freight_rate\nAU_HPT -> IN_PDP,2026-01-01,17.4\n',encoding='utf-8')
        page.locator('#upload-file').set_input_files(str(sample.resolve()))
        page.locator('[data-action="upload"]').click()
        page.locator('#upload-result .notice').wait_for(timeout=30000)
        ready(page,'simulation-backtest')
        page.locator('#backtest-start').fill('2026-06-01')
        page.locator('#backtest-end').fill('2026-07-01')
        page.locator('[data-action="run-backtest"]').click()
        page.get_by_text('Decision Outcomes Matrix').wait_for(timeout=90000)
        assert not errors, errors
        browser.close()
    print('PASS: navigation, 13 tabs, chart, sort, fullscreen, forecast, solve, scenario, note, upload, backtest')

if __name__=='__main__':
    main()
