"""Build human-readable index/inventory, local gallery, and capture integrity report."""
import hashlib,html,json,math,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageStat
OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[1]

# Business descriptions verified against page implementation, not inferred from names.
SPECS=[
('01-overview','Overview / Home','app/Home.py; app/views/control_tower_view.py',
 'Review the active procurement shipment and modeled recommended action.',
 'Shipment hero, modeled logistics cost, date/vessel recommendation, computed Twin score, market history, forecast and illustrative shipment activity.',
 'View Recommendation; Run Scenario; Download PDF Report; top/sidebar navigation; switch theme.',
 'Existing active shipment and scenario session context; no dedicated shipment editor on this page.',
 'Shipment ID/cargo/tonnes/route, INR cost, recommended date, vessel class, robustness /100, synthetic market/forecast.',
 'Freight market line chart and 30-day forecast with interval; activity card is static illustrative text.',
 'View Recommendation → Charter Optimizer; Run Scenario → Scenario Lab; all global destinations.',
 'backend.route_market, forecasting, disruption_engine, decision_twin, reporting; shared helper/session state.'),
('02-control-tower','Control Tower','app/pages/1_Control_Tower.py; app/views/control_tower_view.py',
 'Alternate navigation entry to the same shipment command view.',
 'Same feature set as Home with Control Tower heading; this is an actual separate reachable page.',
 'View Recommendation; Run Scenario; PDF download; global navigation; theme.',
 'Active shipment/scenario session context.',
 'Same modeled summary and supporting content as Home.',
 'Freight history and forecast charts; illustrative shipment activity.',
 'Sidebar Control Tower; Overview remains highlighted in the top shell; charter/scenario actions.',
 'Same shared view and backend dependencies as Home.'),
('03-decision-twin','Decision Twin','app/pages/2_Decision_Twin.py',
 'Compare a modeled charter decision under simulated future market conditions.',
 'Shipment inputs in sidebar, calibrated-route badge, active-scenario banner, 1,000-future simulation, composite robustness, regret, heatmap, future envelope, heuristic counterfactuals.',
 'Choose cargo/country/ports; edit tonnes; inspect chart hover/zoom; export Decision Twin PDF; change theme.',
 'Cargo Type; Quantity 10,000–250,000 t; Origin Country/Port; Destination Port; active scenario if selected elsewhere.',
 'Recommended vessel/date, mean expected cost in Cr, score /100, regret in lakh, modeled tipping points.',
 'Decision Surface heatmap; Simulated Freight Futures median and 10–90% envelope.',
 'Global navigation; Scenario Lab shares active_scenario; Overview uses the same cached Twin service but can supply a different forecast dataframe.',
 'backend.decision_twin, forecasting, reporting, domain ports/commodities/routes; original shared processed data explicitly supplied by this page.'),
('04-operations','Operations Overview','app/pages/3_Operations_Overview.py',
 'Provide a compact market and charter recommendation summary.',
 'Four KPIs, freight forecast, vessel-supply trend, recommendation and cost drivers.',
 'Inspect interactive forecast and recommendation; global navigation; theme.',
 'Fixed 75,000 t Coking Coal, Australia → Paradip, Auto vessel; 14-day forecast; no local procurement form.',
 'Freight price and 7-day comparison, 14-day outlook, vessel count, waiting hours, charter recommendation.',
 'Historical/forecast line chart with confidence interval; native recommendation card.',
 'Operations top button and Operations Overview sidebar entry.',
 'backend.forecasting, optimizer, vessel_forecast; shared processed dataset and cards/charts.'),
('05-market-intelligence','Market Intelligence','app/pages/4_Market_Overview.py',
 'Inspect route market context alongside benchmark and commodity signals.',
 'Active route snapshot, benchmark KPI strip, date filter, freight chart, signal table, illustrative news.',
 'Edit sidebar Date Window; interact with chart; navigate to Forecasts; theme.',
 'Active shipment route; Date Window range. Source checks list rather than tuple, so filtering behavior should not be assumed correct.',
 'Route spot rate, 14-day trend, congestion/wait, supply; benchmark BDI/freight/coal/ore; fixed event text.',
 'Freight market benchmark line chart with moving average; Market Signals dataframe.',
 'Markets button; active shipment from other pages feeds route snapshot.',
 'backend.route_market and domain.routes for route snapshot; shared dataset for benchmark strip/chart; charts helpers.'),
('06-forecasting','Forecasts','app/pages/5_Forecasting.py',
 'Inspect predictive freight trajectories and the scope of their validation.',
 'Canonical route selection, model and horizon controls, optional up-to-three-route comparison, synthetic metrics, model comparison, contextual signals, external weather hold-out chart.',
 'Select Route/Forecast Model/Horizon; Update Forecast; expand comparison and select routes; chart interactions; theme.',
 'Calibrated route; Auto/SARIMA/Naive Baseline (Prophet conditional); 7/14/30-day horizon; up to three comparison routes.',
 'Forecast and interval, selected model, MAE/RMSE/MAPE, narrative, external wind validation metrics/date range.',
 'Main freight forecast, optional route overlay, synthetic model comparison table, contextual signals table, public-weather validation chart.',
 'Forecasts navigation; updates active route context; external weather is a validation section, not a separate page.',
 'backend.route_market, domain.routes, forecasting, validation; Plotly and charts helpers.'),
('07-charter-optimizer','Charter Workbench','app/pages/6_Charter_Optimizer.py',
 'Compare feasible modeled vessel/date candidates and explain their costs.',
 'Procurement toolbar, route badge/metadata, candidate matrix, recommendation, route text diagram, scenario comparison, cost breakdown, explanation, expandable alternatives, sensitivity.',
 'Choose cargo/country/ports; edit quantity and laycan; Solve Candidates; expand alternative reasons/perturbation results; download PDF.',
 'Cargo, 10,000–250,000 t, origin country/port, destination port, laycan; page uses Auto vessel, Medium risk and USD 22,000/day demurrage.',
 'Ranked candidate date/vessel/cost, selected action, component costs, route specifications, assumption stability.',
 'Candidate table; scenario comparison table; cost breakdown; winner-share table; four assumption sweeps and detailed perturbation tables. Route visualization is text, not a map.',
 'Overview View Recommendation; top Chartering button; active shipment session; local shipment/version persistence on solve.',
 'backend.optimizer, sensitivity, reporting, storage, domain catalogs; forecasting on shared processed dataset.'),
('08-scenario-lab','Scenario Lab','app/pages/7_Scenario_Lab.py',
 'Compare hypothetical market disruption effects with the baseline recommendation.',
 'Six presets, reset, three shock sliders, weather and target-port choices, impact preview, status and comparison.',
 'East Coast Disruption; Freight Rate Spike; Paradip Congestion; Vessel Shortage; Severe Weather Risk; Market Relief; Reset Scenario; Run Scenario Simulation.',
 'Freight -20 to +30%; congestion -50 to +100%; availability -60 to +50%; Low/Moderate/High/Severe weather; target discharge port.',
 'Expected cost, % delta, selected date/vessel, recommendation shifted/unchanged status, explanation and baseline-versus-stressed results.',
 'Native comparison dataframe; impact KPI cards. No standalone scenario chart is currently rendered.',
 'Overview Run Scenario; Scenarios top button; canonical active_scenario session used by other pages.',
 'backend.forecasting, scenario_engine, schemas, domain.ports; request still fixes Coking Coal/75,000 t/Australia.'),
('09-backtesting','Simulation Backtest','app/pages/8_Backtesting.py',
 'Evaluate the decision rule against immediate charter on synthetic historical route data.',
 'Route/date/horizon/interval form, run state and timing, four metrics, interpretation, comparison/cumulative charts and period outcomes.',
 'Select route/dates/horizon/interval; Run Simulation Backtest; inspect charts/table; theme.',
 'Simulation Route; start/end dates; 7/14/30-day horizon; 7/14/21/30-day interval; active cargo; Panamax fixed.',
 'Decision-window count, simulated win rate, signed cost difference and %, forecast MAE, per-period results.',
 'Cost Comparison per Decision Period; Cumulative Cost Difference; Decision Outcomes Matrix.',
 'Backtesting top/sidebar entry; route defaults from active shipment context.',
 'backend.backtesting, route_market, domain.routes; chart helpers and session result cache.'),
('10-data-integrations','Data & Integrations','app/pages/9_Data_Integration.py',
 'Inspect data provenance, assumptions, model limitations and local audit activity.',
 'Eight tabs; five-source connection table; quality matrix; manual note form; audit log; limitations prose; eleven parameters; classification legend; four model cards; trust panel.',
 'Switch all eight tabs; expand legend/model cards; edit manual-note values; Record Manual Override Note. Connection action cells are not functional buttons.',
 'Manual note congestion 0–100, vessel count 1–100, INR/day demurrage; otherwise read-only.',
 'Connection states, signal freshness/mode, note confirmation, local events, parameter values/ranges/provenance and model status.',
 'Connections, quality, audit, parameters and trust dataframes; model cards in two-column expanded panels.',
 'Data top button; Data Integration sidebar; notes write only to audit log.',
 'backend.integrations.integration_manager, data_quality, storage, config_model, validation.'),
('11-data-explorer','Data Explorer','app/pages/10_Data_Explorer.py',
 'Inspect and export synthetic datasets, examine schema/correlation, and preview an upload.',
 'Five tabs; KPI row; route filter; route/processed CSV exports; correlation; missingness/types audit; upload validation preview. Dataset tab currently empty.',
 'Filter Route Key; download route/processed CSV; switch tabs; upload CSV for preview only; inspect table/heatmap.',
 'Route key or All Routes; optional CSV upload. Required columns enforced by data_loader validation, with missing columns defaulted.',
 'Observation/features/date-range KPIs, route and processed rows, correlation coefficients, missingness/schema, preview success/warning/error.',
 'Two data tables under Route Freight Series; Pearson correlation heatmap; quality dataframe; upload preview dataframe.',
 'Explorer button and Data Explorer sidebar; upload does not replace active forecasts.',
 'backend.route_market, data_loader, features; Plotly Express and shared chart theme.'),
]

def main():
    m=json.loads((OUT/'evidence/capture-manifest.json').read_text(encoding='utf-8'))
    names={s[0]:s[1] for s in SPECS}
    lines=['# FreightIQ — screenshot index','',
        'Captured 24 October 2026, actual local DEMO UI. PNGs are unretouched browser captures. Device scale factor: 1.',
        '', '**Viewport** files are exactly 1920×1080, 1440×900 or 768×1024. **Full-page** files retain the same width with a larger natural content height; Streamlit\'s inner scrolling requires temporarily increasing browser height. **Component** files are actual chart/table element captures at natural dimensions. No chart labels, errors, values or colors were edited.',
        '', 'Use [gallery.html](gallery.html) for a visual browser. The Dataset-tab empty screen and existing rendering defects are intentionally retained. Capture names identify selected tabs/presets/expanded content. Defaults use clean browser sessions; scenario/interaction names identify deliberate changes.','']
    for pid,title,*_ in SPECS:
        lines.extend([f'## {title}','', '| Screenshot | State | Type | Pixels |','|---|---|---|---|'])
        for c in m['captures']:
            if c['page']==pid:
                file=c['file'];state=' '.join(c['state'].split()).replace('|','/').replace('keyboard_arrow_right ','').replace('keyboard_arrow_down ','')
                lines.append(f"| [{Path(file).name}]({file}) | {state} | {c['kind']} | {c['size'][0]}×{c['size'][1]} |")
        lines.append('')
    (OUT/'SCREENSHOT_INDEX.md').write_text('\n'.join(lines),encoding='utf-8')
    inv=['# FreightIQ — verified feature inventory','',
         'Current source and live-browser inspection, 24 October 2026. Every page has its own section below. Shared shell features apply to all pages. This inventory describes implemented behavior, including known limitations, rather than proposing new features.','']
    labels=['Source implementation','Business purpose','Existing features','Available user actions','Required inputs','Displayed outputs','Charts and tables','Navigation connections','Backend dependencies']
    for spec in SPECS:
        pid,title,*values=spec
        inv.extend([f'## {title}',''])
        for label,value in zip(labels,values):inv.extend([f'**{label}:** {value}',''])
        files=[c for c in m['captures'] if c['page']==pid]
        inv.extend(['**Screenshot filenames:**',''])
        for c in files:
            if c['kind']=='full-page' and 'desktop-1920' in c['file']:
                inv.append(f"- [{Path(c['file']).name}]({c['file']}) — {' '.join(c['state'].split())}")
        inv.extend(['','Additional viewport, 1440, component and responsive captures are listed in `SCREENSHOT_INDEX.md`.',''])
    inv.extend(['## Tab and expandable-section coverage',''])
    for page in m['pages']:
        if page['tabs'] or page['expanders']:
            inv.append(f"### {names.get(page['id'],page['id'])}\n")
            if page['tabs']:inv.append('Tabs: '+ '; '.join(page['tabs'])+'.\n')
            if page['expanders']:inv.append('Expanders discovered in the rendered page: '+ '; '.join(page['expanders']).replace('\n',' ')+'.\n')
    inv.extend(['## Features absent from this frontend','',
        'No interactive map, live vessel-position map, separate weather dashboard, standalone report library, editable parameter settings page, user/role management, charter execution/booking, payment, notification inbox or authenticated connector setup form. PDF/CSV exports, weather validation, route text metadata and vessel comparisons exist only in the locations documented above.',
        '', '## Interaction and display caveats','',
        'The UI includes native Plotly zoom/pan/hover/legend controls and dataframe scroll/sort/fullscreen affordances. These are inspection interactions, not additional business workflows. The captures cover representative selections and meaningful states, not every possible numeric input or every combination of route × model × horizon. Intrinsically scrollable tables cannot show all dataset rows in one screenshot; component and horizontal-scroll states preserve representative readable content.'])
    (OUT/'FEATURE_INVENTORY.md').write_text('\n'.join(inv),encoding='utf-8')

    # Standalone local index; no external libraries or network required.
    cards=[]
    for c in m['captures']:
        f=html.escape(c['file'],quote=True);title=html.escape(names.get(c['page'],c['page'])+' / '+c['state'])
        cards.append(f'<a class="card" href="{f}" data-search="{title.lower()}"><img loading="lazy" src="{f}" alt="{title}"><strong>{title}</strong><small>{c["kind"]} · {c["size"][0]} × {c["size"][1]}</small></a>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FreightIQ — Stitch references</title><style>body{font:15px system-ui;margin:0;background:#f4f6fa;color:#14233a}header{padding:28px 4vw;background:#fff;border-bottom:1px solid #ccd4df}h1{margin:0 0 8px}p{max-width:1000px}input{padding:12px;width:min(600px,85%);border:1px solid #aab6c7;border-radius:8px}.grid{padding:24px 4vw;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px}.card{color:inherit;text-decoration:none;background:white;border:1px solid #d6deea;border-radius:8px;overflow:hidden}.card img{width:100%;height:225px;object-fit:contain;background:#e7edf5}.card strong,.card small{display:block;padding:8px 12px}.card small{color:#52617a}nav a{margin-right:20px;color:#145bbc}</style><header><h1>FreightIQ · UI reference library</h1><p>Actual current-state screenshots, 24 October 2026. Synthetic demo data; existing defects retained. Open an image for full-resolution detail. Full-page images are taller than the stated desktop viewport.</p><nav><a href="STITCH_CONTEXT.md">Stitch context</a><a href="FEATURE_INVENTORY.md">Feature inventory</a><a href="DESIGN_AUDIT.md">Design audit</a><a href="SCREENSHOT_INDEX.md">Full index</a><a href="VERIFICATION.md">Verification</a></nav><p><input id="search" aria-label="Filter screenshots" placeholder="Filter by page or state, e.g. dark, scenario, forecast"></p></header><main class="grid">'''+''.join(cards)+'''</main><script>document.getElementById('search').addEventListener('input',e=>{const q=e.target.value.toLowerCase();document.querySelectorAll('.card').forEach(c=>c.hidden=!c.dataset.search.includes(q))})</script></html>'''
    (OUT/'gallery.html').write_text(page,encoding='utf-8')

    # Decode every delivered image and validate named resolution classes.
    checks=[]
    for c in m['captures']:
        f=OUT/c['file']
        with Image.open(f) as im:
            im.load();actual=list(im.size)
            assert actual==c['size'],f
            assert im.format=='PNG',f
            assert sum(ImageStat.Stat(im.convert('RGB')).stddev)>1,'Blank image '+str(f)
            if c['kind']=='viewport' and '--viewport.png' in c['file']:
                expected=[1920,1080] if '/desktop-1920/' in c['file'] else [1440,900] if '/desktop-1440/' in c['file'] else [768,1024]
                assert actual==expected,(f,actual)
        checks.append({'file':c['file'],'pixels':actual,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'decoded':True})
    baseline=json.loads((OUT/'evidence/source-baseline.json').read_text(encoding='utf-8'))
    changed=[f for f,h in baseline['hashes'].items() if not (ROOT/f).exists() or hashlib.sha256((ROOT/f).read_bytes()).hexdigest()!=h]
    results={'screenshot_count':len(checks),'all_images_decoded':True,'source_files_changed':changed,'source_head':baseline['head'],'current_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'screenshots':checks}
    (OUT/'evidence/integrity-check.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print('Built index, inventory, gallery. PNGs verified:',len(checks),'Changed tracked files:',changed)

if __name__=='__main__':main()
