# FreightIQ — verified feature inventory

Current source and live-browser inspection, 24 October 2026. Every page has its own section below. Shared shell features apply to all pages. This inventory describes implemented behavior, including known limitations, rather than proposing new features.

## Overview / Home

**Source implementation:** app/Home.py; app/views/control_tower_view.py

**Business purpose:** Review the active procurement shipment and modeled recommended action.

**Existing features:** Shipment hero, modeled logistics cost, date/vessel recommendation, computed Twin score, market history, forecast and illustrative shipment activity.

**Available user actions:** View Recommendation; Run Scenario; Download PDF Report; top/sidebar navigation; switch theme.

**Required inputs:** Existing active shipment and scenario session context; no dedicated shipment editor on this page.

**Displayed outputs:** Shipment ID/cargo/tonnes/route, INR cost, recommended date, vessel class, robustness /100, synthetic market/forecast.

**Charts and tables:** Freight market line chart and 30-day forecast with interval; activity card is static illustrative text.

**Navigation connections:** View Recommendation → Charter Optimizer; Run Scenario → Scenario Lab; all global destinations.

**Backend dependencies:** backend.route_market, forecasting, disruption_engine, decision_twin, reporting; shared helper/session state.

**Screenshot filenames:**

- [01-overview--default--full.png](screenshots/desktop-1920/01-overview--default--full.png) — default
- [01-overview--dark-mode--full.png](screenshots/desktop-1920/01-overview--dark-mode--full.png) — dark-mode

Additional viewport, 1440, component and responsive captures are listed in `SCREENSHOT_INDEX.md`.

## Control Tower

**Source implementation:** app/pages/1_Control_Tower.py; app/views/control_tower_view.py

**Business purpose:** Alternate navigation entry to the same shipment command view.

**Existing features:** Same feature set as Home with Control Tower heading; this is an actual separate reachable page.

**Available user actions:** View Recommendation; Run Scenario; PDF download; global navigation; theme.

**Required inputs:** Active shipment/scenario session context.

**Displayed outputs:** Same modeled summary and supporting content as Home.

**Charts and tables:** Freight history and forecast charts; illustrative shipment activity.

**Navigation connections:** Sidebar Control Tower; Overview remains highlighted in the top shell; charter/scenario actions.

**Backend dependencies:** Same shared view and backend dependencies as Home.

**Screenshot filenames:**

- [02-control-tower--default--full.png](screenshots/desktop-1920/02-control-tower--default--full.png) — default

Additional viewport, 1440, component and responsive captures are listed in `SCREENSHOT_INDEX.md`.

## Decision Twin

**Source implementation:** app/pages/2_Decision_Twin.py

**Business purpose:** Compare a modeled charter decision under simulated future market conditions.

**Existing features:** Shipment inputs in sidebar, calibrated-route badge, active-scenario banner, 1,000-future simulation, composite robustness, regret, heatmap, future envelope, heuristic counterfactuals.

**Available user actions:** Choose cargo/country/ports; edit tonnes; inspect chart hover/zoom; export Decision Twin PDF; change theme.

**Required inputs:** Cargo Type; Quantity 10,000–250,000 t; Origin Country/Port; Destination Port; active scenario if selected elsewhere.

**Displayed outputs:** Recommended vessel/date, mean expected cost in Cr, score /100, regret in lakh, modeled tipping points.

**Charts and tables:** Decision Surface heatmap; Simulated Freight Futures median and 10–90% envelope.

**Navigation connections:** Global navigation; Scenario Lab shares active_scenario; Overview uses the same cached Twin service but can supply a different forecast dataframe.

**Backend dependencies:** backend.decision_twin, forecasting, reporting, domain ports/commodities/routes; original shared processed data explicitly supplied by this page.

**Screenshot filenames:**

- [03-decision-twin--default--full.png](screenshots/desktop-1920/03-decision-twin--default--full.png) — default
- [03-decision-twin--active-east-coast-scenario--full.png](screenshots/desktop-1920/03-decision-twin--active-east-coast-scenario--full.png) — active-east-coast-scenario
- [03-decision-twin--dark-mode--full.png](screenshots/desktop-1920/03-decision-twin--dark-mode--full.png) — dark-mode

Additional viewport, 1440, component and responsive captures are listed in `SCREENSHOT_INDEX.md`.

## Operations Overview

**Source implementation:** app/pages/3_Operations_Overview.py

**Business purpose:** Provide a compact market and charter recommendation summary.

**Existing features:** Four KPIs, freight forecast, vessel-supply trend, recommendation and cost drivers.

**Available user actions:** Inspect interactive forecast and recommendation; global navigation; theme.

**Required inputs:** Fixed 75,000 t Coking Coal, Australia → Paradip, Auto vessel; 14-day forecast; no local procurement form.

**Displayed outputs:** Freight price and 7-day comparison, 14-day outlook, vessel count, waiting hours, charter recommendation.

**Charts and tables:** Historical/forecast line chart with confidence interval; native recommendation card.

**Navigation connections:** Operations top button and Operations Overview sidebar entry.

**Backend dependencies:** backend.forecasting, optimizer, vessel_forecast; shared processed dataset and cards/charts.

**Screenshot filenames:**

- [04-operations--default--full.png](screenshots/desktop-1920/04-operations--default--full.png) — default

Additional viewport, 1440, component and responsive captures are listed in `SCREENSHOT_INDEX.md`.

## Market Intelligence

**Source implementation:** app/pages/4_Market_Overview.py

**Business purpose:** Inspect route market context alongside benchmark and commodity signals.

**Existing features:** Active route snapshot, benchmark KPI strip, date filter, freight chart, signal table, illustrative news.

**Available user actions:** Edit sidebar Date Window; interact with chart; navigate to Forecasts; theme.

**Required inputs:** Active shipment route; Date Window range. Source checks list rather than tuple, so filtering behavior should not be assumed correct.

**Displayed outputs:** Route spot rate, 14-day trend, congestion/wait, supply; benchmark BDI/freight/coal/ore; fixed event text.

**Charts and tables:** Freight market benchmark line chart with moving average; Market Signals dataframe.

**Navigation connections:** Markets button; active shipment from other pages feeds route snapshot.

**Backend dependencies:** backend.route_market and domain.routes for route snapshot; shared dataset for benchmark strip/chart; charts helpers.

**Screenshot filenames:**

- [05-market-intelligence--default--full.png](screenshots/desktop-1920/05-market-intelligence--default--full.png) — default
- [05-market-intelligence--date-window-june-to-august-2026--full.png](screenshots/desktop-1920/05-market-intelligence--date-window-june-to-august-2026--full.png) — date-window-june-to-august-2026

Additional viewport, 1440, component and responsive captures are listed in `SCREENSHOT_INDEX.md`.

## Forecasts

**Source implementation:** app/pages/5_Forecasting.py

**Business purpose:** Inspect predictive freight trajectories and the scope of their validation.

**Existing features:** Canonical route selection, model and horizon controls, optional up-to-three-route comparison, synthetic metrics, model comparison, contextual signals, external weather hold-out chart.

**Available user actions:** Select Route/Forecast Model/Horizon; Update Forecast; expand comparison and select routes; chart interactions; theme.

**Required inputs:** Calibrated route; Auto/SARIMA/Naive Baseline (Prophet conditional); 7/14/30-day horizon; up to three comparison routes.

**Displayed outputs:** Forecast and interval, selected model, MAE/RMSE/MAPE, narrative, external wind validation metrics/date range.

**Charts and tables:** Main freight forecast, optional route overlay, synthetic model comparison table, contextual signals table, public-weather validation chart.

**Navigation connections:** Forecasts navigation; updates active route context; external weather is a validation section, not a separate page.

**Backend dependencies:** backend.route_market, domain.routes, forecasting, validation; Plotly and charts helpers.

**Screenshot filenames:**

- [06-forecasting--default--full.png](screenshots/desktop-1920/06-forecasting--default--full.png) — default
- [06-forecasting--expanded-keyboard-arrow-right-compare-route-freight-trajectories-optional--full.png](screenshots/desktop-1920/06-forecasting--expanded-keyboard-arrow-right-compare-route-freight-trajectories-optional--full.png) — expanded-keyboard_arrow_right 📊 Compare Route Freight Trajectories (Optional)
- [06-forecasting--dark-mode--full.png](screenshots/desktop-1920/06-forecasting--dark-mode--full.png) — dark-mode
- [06-forecasting--sarima-30-day--full.png](screenshots/desktop-1920/06-forecasting--sarima-30-day--full.png) — sarima-30-day
- [06-forecasting--naive-baseline-30-day--full.png](screenshots/desktop-1920/06-forecasting--naive-baseline-30-day--full.png) — naive-baseline-30-day
- [06-forecasting--three-route-comparison--full.png](screenshots/desktop-1920/06-forecasting--three-route-comparison--full.png) — three-route-comparison
- [06-forecasting--alternate-route-brazil-paradip--full.png](screenshots/desktop-1920/06-forecasting--alternate-route-brazil-paradip--full.png) — alternate-route-brazil-paradip

Additional viewport, 1440, component and responsive captures are listed in `SCREENSHOT_INDEX.md`.

## Charter Workbench

**Source implementation:** app/pages/6_Charter_Optimizer.py

**Business purpose:** Compare feasible modeled vessel/date candidates and explain their costs.

**Existing features:** Procurement toolbar, route badge/metadata, candidate matrix, recommendation, route text diagram, scenario comparison, cost breakdown, explanation, expandable alternatives, sensitivity.

**Available user actions:** Choose cargo/country/ports; edit quantity and laycan; Solve Candidates; expand alternative reasons/perturbation results; download PDF.

**Required inputs:** Cargo, 10,000–250,000 t, origin country/port, destination port, laycan; page uses Auto vessel, Medium risk and USD 22,000/day demurrage.

**Displayed outputs:** Ranked candidate date/vessel/cost, selected action, component costs, route specifications, assumption stability.

**Charts and tables:** Candidate table; scenario comparison table; cost breakdown; winner-share table; four assumption sweeps and detailed perturbation tables. Route visualization is text, not a map.

**Navigation connections:** Overview View Recommendation; top Chartering button; active shipment session; local shipment/version persistence on solve.

**Backend dependencies:** backend.optimizer, sensitivity, reporting, storage, domain catalogs; forecasting on shared processed dataset.

**Screenshot filenames:**

- [07-charter-optimizer--default--full.png](screenshots/desktop-1920/07-charter-optimizer--default--full.png) — default
- [07-charter-optimizer--demo-laycan-2026-09-01-to-15--full.png](screenshots/desktop-1920/07-charter-optimizer--demo-laycan-2026-09-01-to-15--full.png) — demo-laycan-2026-09-01-to-15
- [07-charter-optimizer--expanded-keyboard-arrow-right-panamax-on-2026-09-07-total-2-637-225-0-vs-selected--full.png](screenshots/desktop-1920/07-charter-optimizer--expanded-keyboard-arrow-right-panamax-on-2026-09-07-total-2-637-225-0-vs-selected--full.png) — expanded-keyboard_arrow_right Panamax on 2026-09-07 — total $2,637,225 (+₹0 vs selected)
- [07-charter-optimizer--expanded-keyboard-arrow-right-panamax-on-2026-09-06-total-2-637-975-63-000-vs-selected--full.png](screenshots/desktop-1920/07-charter-optimizer--expanded-keyboard-arrow-right-panamax-on-2026-09-06-total-2-637-975-63-000-vs-selected--full.png) — expanded-keyboard_arrow_right Panamax on 2026-09-06 — total $2,637,975 (+₹63,000 vs selected)
- [07-charter-optimizer--expanded-keyboard-arrow-right-panamax-on-2026-09-08-total-2-637-975-63-000-vs-selected--full.png](screenshots/desktop-1920/07-charter-optimizer--expanded-keyboard-arrow-right-panamax-on-2026-09-08-total-2-637-975-63-000-vs-selected--full.png) — expanded-keyboard_arrow_right Panamax on 2026-09-08 — total $2,637,975 (+₹63,000 vs selected)
- [07-charter-optimizer--expanded-keyboard-arrow-right-detailed-perturbation-results--full.png](screenshots/desktop-1920/07-charter-optimizer--expanded-keyboard-arrow-right-detailed-perturbation-results--full.png) — expanded-keyboard_arrow_right Detailed perturbation results
- [07-charter-optimizer--infeasible-250000-tonnes--full.png](screenshots/desktop-1920/07-charter-optimizer--infeasible-250000-tonnes--full.png) — infeasible-250000-tonnes
- [07-charter-optimizer--brazil-gangavaram-150000t--full.png](screenshots/desktop-1920/07-charter-optimizer--brazil-gangavaram-150000t--full.png) — brazil-gangavaram-150000t
- [07-charter-optimizer--catalog-only-unsupported-route--full.png](screenshots/desktop-1920/07-charter-optimizer--catalog-only-unsupported-route--full.png) — catalog-only-unsupported-route

Additional viewport, 1440, component and responsive captures are listed in `SCREENSHOT_INDEX.md`.

## Scenario Lab

**Source implementation:** app/pages/7_Scenario_Lab.py

**Business purpose:** Compare hypothetical market disruption effects with the baseline recommendation.

**Existing features:** Six presets, reset, three shock sliders, weather and target-port choices, impact preview, status and comparison.

**Available user actions:** East Coast Disruption; Freight Rate Spike; Paradip Congestion; Vessel Shortage; Severe Weather Risk; Market Relief; Reset Scenario; Run Scenario Simulation.

**Required inputs:** Freight -20 to +30%; congestion -50 to +100%; availability -60 to +50%; Low/Moderate/High/Severe weather; target discharge port.

**Displayed outputs:** Expected cost, % delta, selected date/vessel, recommendation shifted/unchanged status, explanation and baseline-versus-stressed results.

**Charts and tables:** Native comparison dataframe; impact KPI cards. No standalone scenario chart is currently rendered.

**Navigation connections:** Overview Run Scenario; Scenarios top button; canonical active_scenario session used by other pages.

**Backend dependencies:** backend.forecasting, scenario_engine, schemas, domain.ports; request still fixes Coking Coal/75,000 t/Australia.

**Screenshot filenames:**

- [08-scenario-lab--default--full.png](screenshots/desktop-1920/08-scenario-lab--default--full.png) — default
- [08-scenario-lab--east-coast-disruption--full.png](screenshots/desktop-1920/08-scenario-lab--east-coast-disruption--full.png) — East Coast Disruption
- [08-scenario-lab--freight-rate-spike--full.png](screenshots/desktop-1920/08-scenario-lab--freight-rate-spike--full.png) — Freight Rate Spike
- [08-scenario-lab--paradip-congestion--full.png](screenshots/desktop-1920/08-scenario-lab--paradip-congestion--full.png) — Paradip Congestion
- [08-scenario-lab--vessel-shortage--full.png](screenshots/desktop-1920/08-scenario-lab--vessel-shortage--full.png) — Vessel Shortage
- [08-scenario-lab--severe-weather-risk--full.png](screenshots/desktop-1920/08-scenario-lab--severe-weather-risk--full.png) — Severe Weather Risk
- [08-scenario-lab--market-relief--full.png](screenshots/desktop-1920/08-scenario-lab--market-relief--full.png) — Market Relief
- [08-scenario-lab--reset-scenario--full.png](screenshots/desktop-1920/08-scenario-lab--reset-scenario--full.png) — Reset Scenario

Additional viewport, 1440, component and responsive captures are listed in `SCREENSHOT_INDEX.md`.

## Simulation Backtest

**Source implementation:** app/pages/8_Backtesting.py

**Business purpose:** Evaluate the decision rule against immediate charter on synthetic historical route data.

**Existing features:** Route/date/horizon/interval form, run state and timing, four metrics, interpretation, comparison/cumulative charts and period outcomes.

**Available user actions:** Select route/dates/horizon/interval; Run Simulation Backtest; inspect charts/table; theme.

**Required inputs:** Simulation Route; start/end dates; 7/14/30-day horizon; 7/14/21/30-day interval; active cargo; Panamax fixed.

**Displayed outputs:** Decision-window count, simulated win rate, signed cost difference and %, forecast MAE, per-period results.

**Charts and tables:** Cost Comparison per Decision Period; Cumulative Cost Difference; Decision Outcomes Matrix.

**Navigation connections:** Backtesting top/sidebar entry; route defaults from active shipment context.

**Backend dependencies:** backend.backtesting, route_market, domain.routes; chart helpers and session result cache.

**Screenshot filenames:**

- [09-backtesting--default--full.png](screenshots/desktop-1920/09-backtesting--default--full.png) — default
- [09-backtesting--short-period-7-day-horizon-30-day-interval--full.png](screenshots/desktop-1920/09-backtesting--short-period-7-day-horizon-30-day-interval--full.png) — short-period-7-day-horizon-30-day-interval

Additional viewport, 1440, component and responsive captures are listed in `SCREENSHOT_INDEX.md`.

## Data & Integrations

**Source implementation:** app/pages/9_Data_Integration.py

**Business purpose:** Inspect data provenance, assumptions, model limitations and local audit activity.

**Existing features:** Eight tabs; five-source connection table; quality matrix; manual note form; audit log; limitations prose; eleven parameters; classification legend; four model cards; trust panel.

**Available user actions:** Switch all eight tabs; expand legend/model cards; edit manual-note values; Record Manual Override Note. Connection action cells are not functional buttons.

**Required inputs:** Manual note congestion 0–100, vessel count 1–100, INR/day demurrage; otherwise read-only.

**Displayed outputs:** Connection states, signal freshness/mode, note confirmation, local events, parameter values/ranges/provenance and model status.

**Charts and tables:** Connections, quality, audit, parameters and trust dataframes; model cards in two-column expanded panels.

**Navigation connections:** Data top button; Data Integration sidebar; notes write only to audit log.

**Backend dependencies:** backend.integrations.integration_manager, data_quality, storage, config_model, validation.

**Screenshot filenames:**

- [10-data-integrations--default--full.png](screenshots/desktop-1920/10-data-integrations--default--full.png) — default
- [10-data-integrations--tab-connections--full.png](screenshots/desktop-1920/10-data-integrations--tab-connections--full.png) — tab-Connections
- [10-data-integrations--tab-data-quality--full.png](screenshots/desktop-1920/10-data-integrations--tab-data-quality--full.png) — tab-Data Quality
- [10-data-integrations--tab-overrides--full.png](screenshots/desktop-1920/10-data-integrations--tab-overrides--full.png) — tab-Overrides
- [10-data-integrations--tab-audit-trail--full.png](screenshots/desktop-1920/10-data-integrations--tab-audit-trail--full.png) — tab-Audit Trail
- [10-data-integrations--tab-model-data-limitations--full.png](screenshots/desktop-1920/10-data-integrations--tab-model-data-limitations--full.png) — tab-Model & Data Limitations
- [10-data-integrations--tab-decision-parameters--full.png](screenshots/desktop-1920/10-data-integrations--tab-decision-parameters--full.png) — tab-Decision Parameters
- [10-data-integrations--tab-model-cards--full.png](screenshots/desktop-1920/10-data-integrations--tab-model-cards--full.png) — tab-Model Cards
- [10-data-integrations--tab-model-status--full.png](screenshots/desktop-1920/10-data-integrations--tab-model-status--full.png) — tab-Model Status
- [10-data-integrations--expanded-keyboard-arrow-right-classification-legend--full.png](screenshots/desktop-1920/10-data-integrations--expanded-keyboard-arrow-right-classification-legend--full.png) — expanded-keyboard_arrow_right Classification legend
- [10-data-integrations--expanded-keyboard-arrow-right-forecasting-engine--full.png](screenshots/desktop-1920/10-data-integrations--expanded-keyboard-arrow-right-forecasting-engine--full.png) — expanded-keyboard_arrow_right Forecasting Engine
- [10-data-integrations--expanded-keyboard-arrow-right-charter-optimizer--full.png](screenshots/desktop-1920/10-data-integrations--expanded-keyboard-arrow-right-charter-optimizer--full.png) — expanded-keyboard_arrow_right Charter Optimizer
- [10-data-integrations--expanded-keyboard-arrow-right-decision-twin-monte-carlo--full.png](screenshots/desktop-1920/10-data-integrations--expanded-keyboard-arrow-right-decision-twin-monte-carlo--full.png) — expanded-keyboard_arrow_right Decision Twin (Monte Carlo)
- [10-data-integrations--expanded-keyboard-arrow-right-scenario-engine--full.png](screenshots/desktop-1920/10-data-integrations--expanded-keyboard-arrow-right-scenario-engine--full.png) — expanded-keyboard_arrow_right Scenario Engine
- [10-data-integrations--override-note-recorded--full.png](screenshots/desktop-1920/10-data-integrations--override-note-recorded--full.png) — override-note-recorded
- [10-data-integrations--audit-after-demo-note--full.png](screenshots/desktop-1920/10-data-integrations--audit-after-demo-note--full.png) — audit-after-demo-note

Additional viewport, 1440, component and responsive captures are listed in `SCREENSHOT_INDEX.md`.

## Data Explorer

**Source implementation:** app/pages/10_Data_Explorer.py

**Business purpose:** Inspect and export synthetic datasets, examine schema/correlation, and preview an upload.

**Existing features:** Five tabs; KPI row; route filter; route/processed CSV exports; correlation; missingness/types audit; upload validation preview. Dataset tab currently empty.

**Available user actions:** Filter Route Key; download route/processed CSV; switch tabs; upload CSV for preview only; inspect table/heatmap.

**Required inputs:** Route key or All Routes; optional CSV upload. Required columns enforced by data_loader validation, with missing columns defaulted.

**Displayed outputs:** Observation/features/date-range KPIs, route and processed rows, correlation coefficients, missingness/schema, preview success/warning/error.

**Charts and tables:** Two data tables under Route Freight Series; Pearson correlation heatmap; quality dataframe; upload preview dataframe.

**Navigation connections:** Explorer button and Data Explorer sidebar; upload does not replace active forecasts.

**Backend dependencies:** backend.route_market, data_loader, features; Plotly Express and shared chart theme.

**Screenshot filenames:**

- [11-data-explorer--default--full.png](screenshots/desktop-1920/11-data-explorer--default--full.png) — default
- [11-data-explorer--tab-route-freight-series--full.png](screenshots/desktop-1920/11-data-explorer--tab-route-freight-series--full.png) — tab-Route Freight Series
- [11-data-explorer--tab-dataset--full.png](screenshots/desktop-1920/11-data-explorer--tab-dataset--full.png) — tab-Dataset
- [11-data-explorer--tab-correlation-matrix--full.png](screenshots/desktop-1920/11-data-explorer--tab-correlation-matrix--full.png) — tab-Correlation Matrix
- [11-data-explorer--tab-quality-audit--full.png](screenshots/desktop-1920/11-data-explorer--tab-quality-audit--full.png) — tab-Quality Audit
- [11-data-explorer--tab-validate-preview-dataset--full.png](screenshots/desktop-1920/11-data-explorer--tab-validate-preview-dataset--full.png) — tab-Validate & Preview Dataset
- [11-data-explorer--dark-mode--full.png](screenshots/desktop-1920/11-data-explorer--dark-mode--full.png) — dark-mode
- [11-data-explorer--filtered-brazil-paradip--full.png](screenshots/desktop-1920/11-data-explorer--filtered-brazil-paradip--full.png) — filtered-brazil-paradip
- [11-data-explorer--upload-valid-demo-preview--full.png](screenshots/desktop-1920/11-data-explorer--upload-valid-demo-preview--full.png) — upload-valid-demo-preview
- [11-data-explorer--upload-missing-columns-warning--full.png](screenshots/desktop-1920/11-data-explorer--upload-missing-columns-warning--full.png) — upload-missing-columns-warning

Additional viewport, 1440, component and responsive captures are listed in `SCREENSHOT_INDEX.md`.

## Tab and expandable-section coverage

### Forecasts

Expanders discovered in the rendered page: keyboard_arrow_right📊 Compare Route Freight Trajectories (Optional).

### Charter Workbench

Expanders discovered in the rendered page: keyboard_arrow_rightPanamax on 2026-09-07 — total $2,637,225 (+₹0 vs selected); keyboard_arrow_rightPanamax on 2026-09-06 — total $2,637,975 (+₹63,000 vs selected); keyboard_arrow_rightPanamax on 2026-09-08 — total $2,637,975 (+₹63,000 vs selected); keyboard_arrow_rightDetailed perturbation results.

### Data & Integrations

Tabs: Connections; Data Quality; Overrides; Audit Trail; Model & Data Limitations; Decision Parameters; Model Cards; Model Status.

Expanders discovered in the rendered page: keyboard_arrow_rightClassification legend; keyboard_arrow_rightForecasting Engine; keyboard_arrow_rightCharter Optimizer; keyboard_arrow_rightDecision Twin (Monte Carlo); keyboard_arrow_rightScenario Engine.

### Data Explorer

Tabs: Route Freight Series; Dataset; Correlation Matrix; Quality Audit; Validate & Preview Dataset.

## Features absent from this frontend

No interactive map, live vessel-position map, separate weather dashboard, standalone report library, editable parameter settings page, user/role management, charter execution/booking, payment, notification inbox or authenticated connector setup form. PDF/CSV exports, weather validation, route text metadata and vessel comparisons exist only in the locations documented above.

## Interaction and display caveats

The UI includes native Plotly zoom/pan/hover/legend controls and dataframe scroll/sort/fullscreen affordances. These are inspection interactions, not additional business workflows. The captures cover representative selections and meaningful states, not every possible numeric input or every combination of route × model × horizon. Intrinsically scrollable tables cannot show all dataset rows in one screenshot; component and horizontal-scroll states preserve representative readable content.