"""Capture real FreightIQ UI; run against the isolated DEMO server on port 8518."""
import json, re, sys, time
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8518"
PAGES = [
    ("01-overview", ""), ("02-control-tower", "Control_Tower"),
    ("03-decision-twin", "Decision_Twin"), ("04-operations", "Operations_Overview"),
    ("05-market-intelligence", "Market_Overview"), ("06-forecasting", "Forecasting"),
    ("07-charter-optimizer", "Charter_Optimizer"), ("08-scenario-lab", "Scenario_Lab"),
    ("09-backtesting", "Backtesting"), ("10-data-integrations", "Data_Integration"),
    ("11-data-explorer", "Data_Explorer"),
]

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:100]

class Capture:
    def __init__(self):
        path = OUT / "evidence/capture-manifest.json"
        self.manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"captures": [], "pages": [], "issues": [], "interactions": []}

    def save(self):
        (OUT / "evidence/capture-manifest.json").write_text(json.dumps(self.manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    def wait(self, page, timeout=180):
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if page.locator('[data-testid="stException"]').count():
                page.wait_for_timeout(500)
                return "EXCEPTION"
            if page.locator('.disclaimer-footer').count():
                busy = page.locator('[data-testid="stStatusWidget"]:visible, [data-testid="stSpinner"]:visible').count()
                if not busy:
                    page.wait_for_timeout(1000)
                    if not page.locator('[data-testid="stStatusWidget"]:visible, [data-testid="stSpinner"]:visible').count():
                        page.evaluate("document.fonts.ready")
                        return "RENDERED"
            page.wait_for_timeout(300)
        return "TIMEOUT"

    def shot(self, page, file, page_id, state, kind="viewport", locator=None):
        path = OUT / file
        path.parent.mkdir(parents=True, exist_ok=True)
        page.mouse.move(0, 0)
        page.wait_for_timeout(250)
        if locator is not None:
            locator.screenshot(path=str(path), animations="disabled")
        else:
            page.screenshot(path=str(path), animations="disabled", full_page=False)
        with Image.open(path) as im:
            size = list(im.size)
        entry = {"file":file, "page":page_id, "state":state, "kind":kind, "size":size, "url":page.url}
        self.manifest["captures"] = [x for x in self.manifest["captures"] if x["file"] != file] + [entry]
        self.save()

    def pair(self, page, page_id, state, width, height):
        folder = f"screenshots/desktop-{width}" if width in (1920,1440) else "screenshots/responsive"
        page.set_viewport_size({"width":width,"height":height})
        page.locator('[data-testid="stMain"]').evaluate("e=>e.scrollTop=0")
        page.wait_for_timeout(400)
        self.shot(page,f"{folder}/{page_id}--{slug(state)}--viewport.png",page_id,state)
        # Streamlit scrolls stMain, not document.body. Increase viewport height to
        # its actual content height to capture a complete, unstiched real page.
        full_height = height
        for _ in range(3):
            needed = page.locator('[data-testid="stMain"]').evaluate("e=>e.scrollHeight")
            if needed <= full_height + 2:
                break
            full_height = min(20000, int(needed)+10)
            page.set_viewport_size({"width":width,"height":full_height})
            page.wait_for_timeout(350)
        self.shot(page,f"{folder}/{page_id}--{slug(state)}--full.png",page_id,state,"full-page")
        page.set_viewport_size({"width":width,"height":height})
        page.wait_for_timeout(300)

    def components(self, page, page_id, state):
        for selector, kind in [('[data-testid="stPlotlyChart"]','chart'),('[data-testid="stDataFrame"]','table')]:
            els = page.locator(selector)
            for i in range(els.count()):
                el=els.nth(i)
                if el.is_visible():
                    try:
                        el.scroll_into_view_if_needed()
                        page.wait_for_timeout(350)
                        self.shot(page,f"screenshots/components/{page_id}--{slug(state)}--{kind}-{i+1:02}.png",page_id,state,"component",el)
                    except Exception as e:
                        self.manifest['issues'].append({'page':page_id,'state':state,'issue':f'Component {kind} {i+1}: {e}'})
        self.save()

    def text(self,page,page_id,state):
        (OUT/f"evidence/{page_id}--{slug(state)}.txt").write_text(page.locator('body').inner_text(),encoding='utf-8')

def main():
    cap=Capture()
    with sync_playwright() as p:
        b=p.chromium.launch(channel='msedge',headless=True)
        for page_id, route in PAGES:
            ctx=b.new_context(viewport={'width':1920,'height':1080},device_scale_factor=1,locale='en-US',timezone_id='Asia/Kolkata')
            page=ctx.new_page(); start=time.monotonic()
            page.goto(BASE+'/'+route,wait_until='domcontentloaded')
            status=cap.wait(page)
            tabs=page.get_by_role('tab').all_text_contents()
            headings=page.locator('h1,h2,h3,h4').all_text_contents()
            cap.manifest['pages'].append({'id':page_id,'route':route,'status':status,'seconds':round(time.monotonic()-start,2),'tabs':tabs,'headings':headings,'expanders':page.locator('summary').all_text_contents()})
            cap.text(page,page_id,'default')
            for width,height in [(1920,1080),(1440,900)]:
                cap.pair(page,page_id,'default',width,height)
                if tabs:
                    for label in tabs:
                        page.get_by_role('tab',name=label,exact=True).click()
                        page.wait_for_timeout(500)
                        cap.pair(page,page_id,'tab-'+label,width,height)
                    page.get_by_role('tab',name=tabs[0],exact=True).click()
            page.set_viewport_size({'width':1920,'height':1080})
            if tabs:
                for label in tabs:
                    page.get_by_role('tab',name=label,exact=True).click()
                    page.wait_for_timeout(300)
                    cap.text(page,page_id,'tab-'+label)
                    cap.components(page,page_id,'tab-'+label)
                    summaries=page.locator('summary:visible')
                    for i in range(summaries.count()):
                        summary=summaries.nth(i); label_exp=summary.inner_text()
                        summary.click(); page.wait_for_timeout(350)
                        cap.pair(page,page_id,'expanded-'+label_exp,1920,1080)
                        cap.text(page,page_id,'expanded-'+label_exp)
                        summary.click()
            else:
                cap.components(page,page_id,'default')
                summaries=page.locator('summary:visible')
                for i in range(summaries.count()):
                    summary=summaries.nth(i); label=summary.inner_text()
                    summary.click(); page.wait_for_timeout(350)
                    cap.pair(page,page_id,'expanded-'+label,1920,1080)
                    cap.components(page,page_id,'expanded-'+label)
                    summary.click()
            cap.save()
            print(page_id,status,'tabs',len(tabs),'captures',len(cap.manifest['captures']),flush=True)
            ctx.close()
        b.close()

if __name__=='__main__':main()
