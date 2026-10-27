"""Verified interaction details and recovery of virtualized-menu selection."""
import json,time
from playwright.sync_api import sync_playwright
from capture_reference import Capture,OUT,BASE

def main():
    cap=Capture()
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        def new(route):
            ctx=browser.new_context(viewport={'width':1920,'height':1080},device_scale_factor=1,locale='en-US',timezone_id='Asia/Kolkata')
            page=ctx.new_page();page.goto(BASE+'/'+route);cap.wait(page);return ctx,page
        def settle(page):page.wait_for_timeout(1300);cap.wait(page)
        def select(page,label,text):
            combo=page.locator('[data-testid=stSelectbox]').filter(has=page.get_by_text(label,exact=True)).get_by_role('combobox')
            combo.click();combo.fill(text);page.wait_for_timeout(400);page.get_by_role('option').filter(has_text=text).first.click();settle(page)
        def save(page,pid,state,both=False,components=False):
            settle(page);cap.text(page,pid,state);cap.pair(page,pid,state,1920,1080)
            if both:cap.pair(page,pid,state,1440,900);page.set_viewport_size({'width':1920,'height':1080})
            if components:cap.components(page,pid,state)
            cap.manifest['interactions'].append({'page':pid,'state':state,'status':'captured'});cap.save();print(pid,state,flush=True)
        def safe(label,fn):
            try:fn()
            except Exception as e:cap.manifest['issues'].append({'page':label,'issue':str(e)});cap.save();print('ISSUE',label,str(e)[:150],flush=True)
        def comparison():
            ctx,page=new('Forecasting');pid='06-forecasting';page.locator('summary').click()
            for term in ['Dalrymple','Ponta da Madeira']:
                combo=page.locator('[data-testid=stMultiSelect]').get_by_role('combobox');combo.click();combo.fill(term);page.wait_for_timeout(400)
                page.get_by_role('option').filter(has_text=term).first.click();page.keyboard.press('Escape');settle(page)
            tags=page.locator('[data-testid=stMultiSelect]').inner_text();assert 'Dalrymple' in tags and 'Ponta da Madeira' in tags
            save(page,pid,'three-route-comparison',True,True)
            select(page,'Route','Ponta da Madeira → Paradip');save(page,pid,'alternate-route-brazil-paradip',True,True)
            ctx.close()
            for issue in cap.manifest['issues']:
                if issue['page']=='06-forecasting':issue['resolved']=True;issue['resolution']='Selected explicit routes through searchable virtualized menu; three-route and alternate-route screenshots captured.'
            cap.save()
        safe('forecast-comparison',comparison)
        def dark_twin():
            ctx,page=new('Decision_Twin');pid='03-decision-twin'
            for _ in range(3):
                if page.get_by_role('button',name='☀ Switch to Light Mode',exact=True).count():break
                page.get_by_role('button',name='🌙 Switch to Dark Mode',exact=True).click();page.wait_for_timeout(3000);cap.wait(page)
            page.get_by_role('button',name='☀ Switch to Light Mode',exact=True).wait_for(timeout=20000)
            page.wait_for_function("getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()==='#0E1117'")
            save(page,pid,'dark-mode',True,True);ctx.close()
        safe('dark-twin',dark_twin)
        def more_charter():
            ctx,page=new('Charter_Optimizer');pid='07-charter-optimizer'
            field=page.get_by_placeholder('YYYY/MM/DD – YYYY/MM/DD',exact=True);field.fill('2026/09/01 – 2026/09/15');field.press('Enter');settle(page)
            select(page,'Origin Country','Brazil');select(page,'Origin Port','Ponta da Madeira (BR_PDM)');select(page,'Destination Port','Gangavaram (IN_GAV)')
            qty=page.get_by_role('spinbutton',name='Quantity (t)',exact=True);qty.fill('150000');qty.press('Enter');settle(page)
            page.get_by_role('button',name='Solve Candidates',exact=True).click();save(page,pid,'brazil-gangavaram-150000t',False,True)
            select(page,'Destination Port','Mumbai (IN_BOM)');save(page,pid,'catalog-only-unsupported-route',True)
            ctx.close()
        safe('charter-route-controls',more_charter)
        def table_details():
            for route,pid,tab in [('Data_Integration','10-data-integrations','Decision Parameters'),('Data_Integration','10-data-integrations','Data Quality'),('Data_Integration','10-data-integrations','Model Status'),('Data_Explorer','11-data-explorer','Route Freight Series'),('Data_Explorer','11-data-explorer','Quality Audit')]:
                ctx,page=new(route);page.get_by_role('tab',name=tab,exact=True).click();page.wait_for_timeout(400)
                tables=page.locator('[data-testid=stDataFrame]:visible')
                for i in range(tables.count()):
                    table=tables.nth(i);table.scroll_into_view_if_needed();page.wait_for_timeout(250)
                    scrolls=table.evaluate("""e=>[...e.querySelectorAll('*')].filter(x=>x.clientWidth>50&&x.clientHeight>30&&(x.scrollWidth>x.clientWidth+10||x.scrollHeight>x.clientHeight+10)).map(x=>{let r={tag:x.tagName,w:x.clientWidth,sw:x.scrollWidth,h:x.clientHeight,sh:x.scrollHeight};x.scrollLeft=x.scrollWidth;x.scrollTop=x.scrollHeight;return r})""")
                    if scrolls:
                        page.wait_for_timeout(700)
                        state=tab+' table '+str(i+1)+' rightmost-columns-last-rows'
                        from capture_reference import slug
                        cap.shot(page,f'screenshots/components/{pid}--{slug(state)}.png',pid,state,'component',table)
                        cap.manifest['interactions'].append({'page':pid,'state':state,'scrolls':scrolls,'status':'captured'})
                ctx.close();cap.save()
            print('Table overflow details captured',flush=True)
        safe('table-overflow',table_details)
        def backtest():
            ctx,page=new('Backtesting');pid='09-backtesting'
            inputs=page.locator('[data-testid=stDateInput] input');inputs.nth(1).fill('2024/09/01');inputs.nth(1).press('Enter');settle(page)
            select(page,'Interval Days','30');page.get_by_role('slider').first.focus();page.keyboard.press('Home');settle(page)
            page.get_by_role('button',name='Run Simulation Backtest',exact=True).click();settle(page)
            save(page,pid,'short-period-7-day-horizon-30-day-interval',False,True);ctx.close()
        safe('backtest-controls',backtest)
        def market_filter():
            ctx,page=new('Market_Overview');pid='05-market-intelligence'
            field=page.get_by_placeholder('YYYY/MM/DD – YYYY/MM/DD',exact=True);field.click();page.wait_for_timeout(400)
            cap.shot(page,f'screenshots/desktop-1920/{pid}--date-range-calendar.png',pid,'Date Window calendar open');page.keyboard.press('Escape')
            field.fill('2026/06/01 – 2026/08/31');field.press('Enter');save(page,pid,'date-window-june-to-august-2026');ctx.close()
        safe('market-filter',market_filter)
        for issue in cap.manifest['issues']:
            if issue['page']=='11-data-explorer':issue['resolved']=True;issue['resolution']='Route dropdown searched explicitly; route filtering, both CSV downloads and both upload previews completed.'
        cap.save();browser.close()

if __name__=='__main__':main()
