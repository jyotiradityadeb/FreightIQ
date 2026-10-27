"""Secondary real UI states; no production application edits."""
import json,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from capture_reference import Capture,OUT,BASE,slug

def run():
    cap=Capture()
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        def new(route):
            ctx=browser.new_context(viewport={'width':1920,'height':1080},device_scale_factor=1,locale='en-US',timezone_id='Asia/Kolkata',accept_downloads=True)
            page=ctx.new_page();page.goto(BASE+'/'+route);cap.wait(page)
            return ctx,page
        def settled(page):
            page.wait_for_timeout(900);return cap.wait(page)
        def record(page,pid,state,both=False,components=False):
            settled(page);cap.text(page,pid,state);cap.pair(page,pid,state,1920,1080)
            if both:cap.pair(page,pid,state,1440,900);page.set_viewport_size({'width':1920,'height':1080})
            if components:cap.components(page,pid,state)
            cap.manifest['interactions'].append({'page':pid,'state':state,'status':'captured','url':page.url});cap.save()
            print(pid,state,flush=True)
        def pick(page,label,option):
            combo=page.locator('[data-testid=stSelectbox]').filter(has=page.get_by_text(label,exact=True)).get_by_role('combobox')
            combo.click();combo.fill(option);page.wait_for_timeout(400)
            page.get_by_role('option').filter(has_text=option).first.click()
            settled(page)
        def download(page,label,pid):
            with page.expect_download(timeout=30000) as info:
                page.get_by_role('button',name=label,exact=True).click()
            d=info.value
            path=OUT/'evidence/downloads'/d.suggested_filename;path.parent.mkdir(parents=True,exist_ok=True);d.save_as(path)
            cap.manifest['interactions'].append({'page':pid,'action':'download '+label,'file':str(path.relative_to(OUT)),'bytes':path.stat().st_size,'status':'downloaded'});cap.save()
        def safe(name,fn):
            if len(sys.argv)>1 and name not in sys.argv[1:]:return
            try:fn()
            except Exception as e:
                cap.manifest['issues'].append({'page':name,'issue':str(e)});cap.save();print('INTERACTION ISSUE',name,str(e)[:350],flush=True)

        def charter():
            ctx,page=new('Charter_Optimizer');pid='07-charter-optimizer'
            field=page.get_by_placeholder('YYYY/MM/DD – YYYY/MM/DD',exact=True)
            field.fill('2026/09/01 – 2026/09/15');field.press('Enter');settled(page)
            page.get_by_role('button',name='Solve Candidates',exact=True).click();settled(page)
            page.get_by_text('Feasible Charter Candidate Matrix',exact=True).wait_for(timeout=60000)
            record(page,pid,'demo-laycan-2026-09-01-to-15',both=True,components=True)
            for i in range(page.locator('summary').count()):
                summary=page.locator('summary').nth(i);label=summary.inner_text();summary.click()
                record(page,pid,'expanded-'+label,components=True);summary.click()
            download(page,'Download Procurement Report (PDF)',pid)
            field.click();page.wait_for_timeout(300)
            cap.shot(page,'screenshots/desktop-1920/'+pid+'--laycan-calendar.png',pid,'Laycan calendar open');page.keyboard.press('Escape')
            page.locator('[data-testid=stSelectbox]').filter(has=page.get_by_text('Cargo',exact=True)).get_by_role('combobox').click();page.wait_for_timeout(250)
            cap.shot(page,'screenshots/desktop-1920/'+pid+'--cargo-menu.png',pid,'Cargo choices');page.keyboard.press('Escape')
            page.locator('[data-testid=stSelectbox]').filter(has=page.get_by_text('Origin Country',exact=True)).get_by_role('combobox').click();page.wait_for_timeout(250)
            options=page.get_by_role('option').all_text_contents();page.keyboard.press('Escape')
            cap.manifest['interactions'].append({'page':pid,'control':'Origin Country options','values':options});cap.save()
            page.get_by_role('spinbutton',name='Quantity (t)',exact=True).fill('250000');page.get_by_role('spinbutton',name='Quantity (t)',exact=True).press('Enter')
            record(page,pid,'infeasible-250000-tonnes')
            ctx.close()
        safe('07-charter-optimizer',charter)

        def forecast():
            ctx,page=new('Forecasting');pid='06-forecasting'
            pick(page,'Forecast Model','SARIMA')
            page.get_by_role('slider').first.focus();page.keyboard.press('End');settled(page)
            page.get_by_role('button',name='Update Forecast',exact=True).click()
            record(page,pid,'sarima-30-day',both=True,components=True)
            pick(page,'Forecast Model','Naive Baseline');record(page,pid,'naive-baseline-30-day')
            page.locator('summary').filter(has_text='Compare Route Freight').click()
            combo=page.locator('[data-testid=stMultiSelect]').get_by_role('combobox')
            combo.click();opts=page.get_by_role('option').all_text_contents();page.keyboard.press('Escape')
            for option in [o for o in opts if 'Hay Point' not in o][:2]:
                combo.click();combo.fill(option);page.wait_for_timeout(400);page.get_by_role('option').filter(has_text=option).first.click();page.keyboard.press('Escape');settled(page)
            record(page,pid,'three-route-comparison',both=True,components=True)
            page.locator('[data-testid=stSelectbox]').filter(has=page.get_by_text('Route',exact=True)).get_by_role('combobox').click();opts=page.get_by_role('option').all_text_contents();page.keyboard.press('Escape')
            alternative='Ponta da Madeira → Paradip';pick(page,'Route',alternative)
            record(page,pid,'alternate-route-'+alternative)
            ctx.close()
        safe('06-forecasting',forecast)

        def scenarios():
            ctx,page=new('Scenario_Lab');pid='08-scenario-lab'
            for label in ['East Coast Disruption','Freight Rate Spike','Paradip Congestion','Vessel Shortage','Severe Weather Risk','Market Relief','Reset Scenario']:
                page.get_by_role('button',name=label,exact=True).click()
                record(page,pid,label,both=label=='East Coast Disruption')
            page.get_by_role('button',name='East Coast Disruption',exact=True).click();settled(page)
            page.get_by_role('button',name='Run Scenario Simulation',exact=True).click();settled(page)
            page.get_by_role('button',name='Decision Twin',exact=True).click();settled(page)
            record(page,'03-decision-twin','active-east-coast-scenario',components=True)
            ctx.close()
        safe('08-scenario-lab',scenarios)

        def integrations():
            ctx,page=new('Data_Integration');pid='10-data-integrations'
            page.get_by_role('tab',name='Overrides',exact=True).click()
            page.get_by_role('spinbutton',name='Override Port Congestion (0-100)',exact=True).fill('60')
            page.get_by_role('spinbutton',name='Override Port Congestion (0-100)',exact=True).press('Enter');settled(page)
            page.get_by_role('button',name='Record Manual Override Note',exact=True).click();record(page,pid,'override-note-recorded')
            page.get_by_role('tab',name='Audit Trail',exact=True).click();record(page,pid,'audit-after-demo-note',components=True)
            ctx.close()
        safe('10-data-integrations',integrations)

        def explorer():
            ctx,page=new('Data_Explorer');pid='11-data-explorer'
            pick(page,'Filter Route Key','BR_PDM -> IN_PDP');record(page,pid,'filtered-brazil-paradip',components=True)
            download(page,'Download Route Rates CSV',pid);download(page,'Download Processed CSV',pid)
            page.get_by_role('tab',name='Validate & Preview Dataset',exact=True).click()
            # Upload only public synthetic fixture bytes through the existing preview UI.
            import pandas as pd
            root=OUT.parents[1];from_path=root/'data/processed/modelling_dataset.csv'
            # Build a small all-required-column fixture from existing demo data.
            sys.path.insert(0,str(root))
            from backend.data_loader import load_raw_datasets
            raw=load_raw_datasets().head(12).to_csv(index=False).encode()
            page.locator('input[type=file]').set_input_files({'name':'synthetic-demo-preview.csv','mimeType':'text/csv','buffer':raw})
            record(page,pid,'upload-valid-demo-preview',components=True)
            page.locator('input[type=file]').set_input_files({'name':'incomplete-demo.csv','mimeType':'text/csv','buffer':b'date,freight_rate\n2026-08-01,14.5\n2026-08-02,15.0\n'})
            record(page,pid,'upload-missing-columns-warning',components=True)
            ctx.close()
        safe('11-data-explorer',explorer)

        def navigation():
            ctx,page=new('');pid='01-overview'
            download(page,'Download PDF Report',pid)
            page.get_by_role('button',name='View Recommendation',exact=True).click();settled(page)
            cap.manifest['interactions'].append({'action':'Overview > View Recommendation','url':page.url,'status':'navigated'})
            page.get_by_role('button',name='Overview',exact=True).click();settled(page)
            page.get_by_role('button',name='Run Scenario',exact=True).click();settled(page)
            cap.manifest['interactions'].append({'action':'Overview > Run Scenario','url':page.url,'status':'navigated'})
            page.get_by_role('button',name='Decision Twin',exact=True).click();settled(page)
            download(page,'Download Decision Twin Report (PDF)','03-decision-twin')
            ctx.close();cap.save()
        safe('navigation-and-exports',navigation)

        def themes():
            for route,pid in [('', '01-overview'),('Decision_Twin','03-decision-twin'),('Forecasting','06-forecasting'),('Data_Explorer','11-data-explorer')]:
                ctx,page=new(route)
                page.get_by_role('button',name='🌙 Switch to Dark Mode',exact=True).click()
                record(page,pid,'dark-mode',both=pid=='01-overview',components=True)
                ctx.close()
        safe('themes',themes)

        def responsive():
            for route,pid in [('', '01-overview'),('Forecasting','06-forecasting'),('Charter_Optimizer','07-charter-optimizer'),('Data_Integration','10-data-integrations')]:
                ctx,page=new(route);cap.pair(page,pid,'responsive-768',768,1024);ctx.close()
            print('Responsive captures complete',flush=True)
        safe('responsive',responsive)
        browser.close();cap.save()

if __name__=='__main__':run()
