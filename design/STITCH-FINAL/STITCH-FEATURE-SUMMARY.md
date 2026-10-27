# FreightIQ — feature summary for Google Stitch

This brief describes the verified application captured on 24 October 2026, not a proposed product. It covers all **11 pages and 13 tabs**. The 15 accompanying images are selected from the existing reference captures.

## Product and shared interactions

FreightIQ is a maritime freight and chartering decision-support prototype for Indian procurement teams. It models shipment costs, vessel/date choices, forecasts and hypothetical disruption impacts. Most market inputs and all freight-performance demonstrations use **synthetic demo data**. INR, crore, lakh, tonnes, dates, USD benchmarks and units must remain explicit.

Preserve navigation to every page, active shipment/route context, light/dark theme switching, data-mode and model-status indicators, PDF/CSV downloads, chart hover/zoom/pan/legend controls, and table scrolling/sorting/fullscreen inspection. Charts and tables must remain usable at normal text size. Inputs and scenario state can propagate between pages; show which context produced a result. Retain explicit run/update buttons and calculation feedback.

## All 11 pages

| # / screenshot | Verified page heading (navigation aliases) | Purpose and functionality to preserve |
|---|---|---|
| 01 | Overview (Home) | Shipment ID, cargo, quantity and route; modeled logistics cost, charter date/vessel and robustness /100; freight history with moving average, forecast interval and illustrative activity. View Recommendation opens Charter Workbench; Run Scenario opens Scenario Lab; PDF download. |
| 02 | Control Tower | Separate reachable entry to the same shared command view as Overview, with its own heading/sidebar selection. Preserve its navigation mapping and the same recommendation, scenario, history/forecast and PDF functionality. Similarity to image 01 is intrinsic to the existing app. |
| 03 | Decision Twin | Cargo, quantity 10,000–250,000 t, origin country/port and destination port inputs; calibrated-route status and active-scenario context. Compare decisions across 1,000 simulated futures using recommended vessel/date, expected cost, composite robustness, regret, decision-surface heatmap, median/10–90% future envelope and heuristic counterfactual tipping points. PDF export. Score is not a probability. |
| 04 | Operations Overview (Operations) | Compact freight rate/7-day comparison, 14-day outlook, vessel availability/supply trend and port waiting-time KPIs. Historical/forecast chart, confidence interval, recommendation and cost drivers. Existing page uses a fixed 75,000 t Coking Coal Australia–Paradip case; it has no local shipment form. |
| 05 | Market Intelligence (Market Overview / Markets) | Active-route spot/trend/congestion/wait/supply snapshot, separate benchmark and commodity KPIs, Date Window control, benchmark freight/moving-average chart, market signal table and illustrative news. Keep route-specific context distinguishable from shared benchmark data. |
| 06 | Forecasts (Forecasting) | Calibrated route, Auto/SARIMA/Naive Baseline model choice (Prophet only when installed), 7/14/30-day horizon and Update Forecast. History/forecast/95% interval, optional expanded comparison of up to three routes, synthetic MAE/RMSE/MAPE and model comparison, contextual signals and narrative. Separate Open-Meteo observed wind hold-out validation with metrics, source, units and date range; this is weather-method validation, not real freight accuracy. |
| 07 | Charter Workbench (Charter Optimizer / Chartering) | Cargo, quantity, origin country/port, destination and laycan controls; Solve Candidates; route feasibility badge and port metadata. Ranked vessel/date candidate matrix, recommendation, component costs, scenario comparison, route text/arrow diagram, explanation, expandable alternatives, four assumption sensitivity sweeps and detailed perturbation results. PDF export; solve persists shipment/decision versions locally. Existing UI uses Auto vessel, Medium risk and fixed demurrage. Selected capture uses a laycan inside the demo forecast period. |
| 08 | Scenario Lab (Scenarios) | Six presets: East Coast Disruption, Freight Rate Spike, Paradip Congestion, Vessel Shortage, Severe Weather Risk, Market Relief; plus Reset Scenario. Freight (-20 to +30%), congestion (-50 to +100%) and availability (-60 to +50%) sliders, weather severity and target discharge port. Run Scenario Simulation produces cost/delta/date/vessel, shifted/unchanged status, explanation and baseline-versus-stressed table. Active scenario is shared with other pages. Current request fixes Coking Coal/75,000 t/Australia. Image 08 shows East Coast Disruption, not the baseline. |
| 09 | Simulation Backtest (Backtesting) | Route, start/end dates, 7/14/30-day horizon, 7/14/21/30-day interval and Run Simulation Backtest. Completion/time, decision-window count, win rate, signed cost difference/percentage and forecast error; benchmark-versus-strategy bars, cumulative difference and per-period outcomes. Synthetic route-history evaluation against immediate charter; preserve negative results and scope disclosures. Panamax is fixed in this page. |
| 10 | Data & Integrations (Data Integration / Data) | Eight tabs described below: connector provenance, data quality, operator notes/audit history, limitations, parameters, model documentation and validation status. Preserve read-only versus editable distinctions. |
| 11 | Data Explorer (Explorer) | Observation/feature/date-range KPIs and five tabs described below: route/processed data, correlation, schema quality and upload preview. Preserve route filtering and both CSV exports. |

## All 13 tabs

Tab counts exclude navigation buttons and expandable sections. Images 12–15 are additional tab references, not new pages.

| # | Parent page | Exact tab label | Existing content and interactions | Image |
|---|---|---|---|---|
| 1 | Data & Integrations | Connections | Five-source table: source, type, status, freshness and action text. Distinguish cached public weather, synthetic feeds and unconfigured commercial AIS. Action cells are informational strings, not working connection buttons. | 10 |
| 2 | Data & Integrations | Data Quality | Signal quality/freshness and source-mode matrix. Preserve missing/stale/unavailable distinctions. | Documented only |
| 3 | Data & Integrations | Overrides | Manual operator-note form: congestion 0–100, vessel count 1–100 and INR/day demurrage. Record Manual Override Note stores an audit note and confirmation; it does not change calculation inputs. | Documented only |
| 4 | Data & Integrations | Audit Trail | Local event history, timestamps, actions and details, including recorded notes; support populated and empty states. | Documented only |
| 5 | Data & Integrations | Model & Data Limitations | Read-only explanation of synthetic inputs, modeling assumptions, validation scope and limitations. Keep prominent provenance/disclosures. | Documented only |
| 6 | Data & Integrations | Decision Parameters | Eleven-entry read-only parameter registry with values, units, classification, sensitivity range, source and notes; expandable Classification legend. Table scroll exposes off-screen rows/columns. | 12 |
| 7 | Data & Integrations | Model Cards | Four expanders: Forecasting Engine, Charter Optimizer, Decision Twin (Monte Carlo), Scenario Engine. Each documents purpose, inputs, outputs, assumptions and validation scope. Existing prose needs technical verification before reuse as claims. | Documented only |
| 8 | Data & Integrations | Model Status | Trust panel per component: status, scope, validated/not-validated areas, key limitations; green/amber/red interpretation and public-weather cache/validation status. Green applies only within the stated scope. | 13 |
| 9 | Data Explorer | Route Freight Series | Canonical route history table and All Routes/specific route filter; Download Route Rates CSV. Current implementation also places the processed modeling dataset and Download Processed CSV in this tab. | 11 |
| 10 | Data Explorer | Dataset | Currently renders an empty body because the processed dataset table/export appear under Route Freight Series. Documented rather than wasting a screenshot on an empty state. Retain the dataset/export capability in any redesign; do not assume this tab is populated today. | Documented only |
| 11 | Data Explorer | Correlation Matrix | Pearson feature correlation heatmap with numeric coefficients, axes and color scale. Preserve hover/inspection and readable labels. | 14 |
| 12 | Data Explorer | Quality Audit | Column-level missingness, data types/schema and integrity table. | Documented only |
| 13 | Data Explorer | Validate & Preview Dataset | CSV upload, required-column validation, success/missing-column warnings/parse errors and preview table. Missing numeric columns may be defaulted. Upload is preview-only and does not replace the active forecast dataset. Image shows a valid 12-row demo upload. | 15 |

## Design guidance and boundaries

Improve hierarchy, compact spacing, consistent forms and navigation, readable charts/tables and semantic status contrast. Preserve all analytical controls and evidence; use drawers/sections if needed to shorten long pages. Support dark mode with consistent chart, table and button colors. The source dark captures were less legible, so this curated set uses light references.

There is **no interactive maritime map or live vessel-position screen**. The route visual is the text/arrow card in Charter Workbench. There is no charter booking/execution, payment, user/role administration, notification inbox, standalone weather dashboard or report library. Do not invent these as existing features.

Existing defects are evidence, not target design: literal “undefined” chart titles, cramped heatmap labels, mixed theme styling, horizontal table overflow, duplicated Home/Control Tower views, legacy route metadata and inconsistent cross-page baselines. The current optimizer can return out-of-laycan dates if the requested window misses the demo forecast; represent invalid/out-of-period states explicitly in a redesign. Market date filtering also needs behavior verification. Captures faithfully preserve existing rendering; no screenshot values or UI elements were retouched.
