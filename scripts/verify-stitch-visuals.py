"""Capture the exported Stitch HTML and the working UI at matching viewports."""
from pathlib import Path
import sys
import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / 'design/stitch-final-export/stitch_freightiq_command_center_redesign'
OUT = ROOT / 'design/visual-verification'
APP_URL = os.environ.get('FREIGHTIQ_VISUAL_URL', 'http://localhost:3000')
CASES = [
    ('overview', 'freightiq_overview_home', 'overview', None),
    ('control-tower', 'freightiq_control_tower', 'control-tower', None),
    ('forecasts', 'freightiq_freight_forecasts', 'forecasts', None),
    ('charter-workbench', 'freightiq_charter_workbench', 'charter-workbench', None),
    ('decision-twin', 'freightiq_decision_twin', 'decision-twin', None),
    ('scenario-lab', 'freightiq_scenario_lab', 'scenario-lab', None),
    ('data-explorer', 'freightiq_data_explorer', 'data-explorer', None),
    ('integrations-quality', 'freightiq_data_integrations_data_quality', 'data-integrations', 1),
    ('integrations-overrides', 'freightiq_data_integrations_overrides', 'data-integrations', 2),
    ('integrations-audit', 'freightiq_data_integrations_audit_trail', 'data-integrations', 3),
    ('integrations-limits', 'freightiq_data_integrations_model_data_limitations', 'data-integrations', 4),
]

def main():
    for folder in ('references', 'implementation', 'diffs'):
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
        cases = [case for case in CASES if len(sys.argv) == 1 or case[0] in sys.argv[1:]]
        for name, source, route, tab in cases:
            page.goto((EXPORT / source / 'code.html').as_uri(), wait_until='domcontentloaded')
            page.wait_for_timeout(1800)
            ref = OUT / 'references' / f'{name}-1440.png'
            page.screenshot(path=str(ref), full_page=False)
            page.goto(f'{APP_URL}/#/{route}', wait_until='domcontentloaded')
            page.locator('#main h1').wait_for(timeout=60000)
            if tab is not None:
                page.locator('[data-tab]').nth(tab).click()
                page.locator('#main h1').wait_for(timeout=60000)
            page.wait_for_timeout(600)
            impl = OUT / 'implementation' / f'{name}-1440.png'
            page.screenshot(path=str(impl), full_page=False)
            a, b = Image.open(ref).convert('RGB'), Image.open(impl).convert('RGB')
            diff = ImageChops.difference(a, b)
            diff.save(OUT / 'diffs' / f'{name}-1440.png')
            mae = sum(ImageStat.Stat(diff).mean) / 3
            print(f'{name}: RGB mean absolute difference {mae:.1f}/255')
        for width, height in [(768, 1024), (390, 844)]:
            page.set_viewport_size({'width': width, 'height': height})
            page.goto(f'{APP_URL}/#/control-tower', wait_until='domcontentloaded')
            page.locator('#main h1').wait_for(timeout=60000)
            page.screenshot(path=str(OUT / 'implementation' / f'control-tower-{width}.png'))
        browser.close()

if __name__ == '__main__':
    main()
