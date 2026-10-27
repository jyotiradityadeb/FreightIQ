# FreightIQ — Google Stitch redesign context

Reference date: **24 October 2026 (Asia/Kolkata)**. Source commit: `0e1d2e87f6fa43c3c47e34d651323e9fd013860d`.

This package records the existing application. Screenshots are actual browser captures, not mockups. Design recommendations describe future work; none have been implemented. Read `SCREENSHOT_INDEX.md` for individual states and `VERIFICATION.md` for capture coverage and limitations.

## Product identity and purpose

**FreightIQ** is a **Maritime Freight Rate Forecasting and Vessel Chartering Decision Support Platform**, currently implemented as a demonstration prototype. Its intended users include Indian steel manufacturers, procurement professionals, shipping analysts, chartering teams, and logistics decision-makers.

It presents freight histories and forecasts, ranks modeled charter options, compares hypothetical disruptions, simulates decision robustness, and evaluates historical decision rules. Most market data is synthetic. Preserve that distinction throughout the redesign: this is not an operational vessel tracking, booking, or charter execution system.

## Architecture

- Python Streamlit multipage frontend; startup: `python -m streamlit run app/Home.py`.
- Eleven reachable page URLs: Home plus ten numbered scripts under `app/pages/`.
- Native Streamlit sidebar navigation and a custom horizontal navigation row coexist. The horizontal row contains real Streamlit buttons that call `st.switch_page` through `app/navigation.py`.
- `app/components/helpers.py` provides the shell, session theme, shipment context, formatting, and procurement toolbar. `cards.py` and `charts.py` provide reusable UI components. `app/views/control_tower_view.py` renders both Home and Control Tower.
- Plotly charts, Streamlit canvas-backed dataframes, native inputs, tabs and expanders. Custom CSS and an inline SVG logo; no separate React application or dedicated map frontend.
- Pages call Python backend functions directly. `backend/main.py` also exposes a FastAPI interface, but launching that server is unnecessary for these screenshots.
- SQLite stores local shipment/decision records and audit notes; ReportLab creates PDF downloads. Session state holds selected shipment, scenario, theme, and cached calculations.

## Actual navigation

| Sidebar / URL | Page heading / business purpose | Top navigation label |
|---|---|---|
| Home `/` | Overview: shipment summary, modeled recommendation, market and forecast charts | Overview |
| Control Tower `/Control_Tower` | Control Tower: same renderer as Overview, separate reachable entry | Overview highlighted |
| Decision Twin `/Decision_Twin` | Stress-test a shipment over simulated futures; cost surface and regret | Decision Twin |
| Operations Overview `/Operations_Overview` | Compact freight, supply and waiting KPIs with forecast/recommendation | Operations |
| Market Overview `/Market_Overview` | Market Intelligence: route snapshot, benchmark history, signals and illustrative news | Markets |
| Forecasting `/Forecasting` | Forecasts: route/model/horizon controls, model metrics and external weather validation | Forecasts |
| Charter Optimizer `/Charter_Optimizer` | Charter Workbench: procurement inputs, ranked candidates, cost/explanation/sensitivity | Chartering |
| Scenario Lab `/Scenario_Lab` | Presets and custom market shocks with baseline/stressed comparison | Scenarios |
| Backtesting `/Backtesting` | Simulation Backtest: walk-forward cost comparison against immediate charter | Backtesting |
| Data Integration `/Data_Integration` | Data & Integrations: sources, quality, notes, logs, assumptions, model documentation | Data |
| Data Explorer `/Data_Explorer` | Data inspection, route filtering, correlation, schema audit and CSV preview | Explorer |

There is **no dedicated Settings, Reports, Weather, Route Intelligence, Vessel Comparison, or Analytics page**. Related capabilities live inside the pages above. The route card is text with an arrow and route metadata, **not an interactive geographic map**. There is no implemented live AIS map, real-time vessel position display, booking flow, authentication screen, or notification inbox.

## Features to preserve

### Overview and operations

Keep shipment ID, cargo, tonnes, origin/destination, total cost, charter date/window, vessel class, robustness score, units and provenance together. Overview actions navigate to chartering and scenarios and download a PDF. Market history and freight forecast are distinct charts. The activity panel contains illustrative fixed text; it must not become a live operational feed in the redesign. Operations is a separate, simpler summary using the original shared dataset.

### Forecasting

Route selection uses the calibrated route catalog. Available model choices are Auto, SARIMA and Naive Baseline; Prophet is conditional on installation. Horizon choices are 7, 14 and 30 days. Preserve the point forecast, interval band, historical observations, synthetic hold-out metrics, comparison table, contextual signals, interpretation, and optional comparison of up to three routes. The lower weather-validation section uses cached public external data and is separate from freight validation.

### Charter workbench

Preserve cargo, quantity, origin country, origin port, destination port and laycan controls; route calibration and draft metadata; Solve Candidates; candidate ranks; vessel/date/route/rate/cost columns; selected recommendation; cost breakdown; alternatives; PDF export; and one-at-a-time assumption sensitivity with expandable detail. Costs are model estimates. “DEMO-CALIBRATED” means configured prototype assumptions, not empirical operational validation.

### Decision Twin

Preserve sidebar shipment inputs, expected cost, recommended vessel/date, 0–100 composite robustness score, expected regret, decision surface heatmap, simulated freight envelope and heuristic tipping-point cards. It simulates 1,000 futures in the current UI. A robustness score is not a probability of commercial success. Retain the PDF export and active-scenario banner when present.

### Scenario Lab and backtesting

Scenario Lab has six preset buttons and Reset Scenario. The editable controls are freight shock, congestion shock, vessel availability change, weather risk and target discharge port. Preserve baseline/stressed costs, date/vessel, recommendation status, explanatory text and comparison table. The current scenario request uses fixed cargo/quantity/origin; do not imply that every active shipment field is already wired through it.

Backtesting has route, date range, horizon and interval controls, a run button, simulated win rate, cost difference, forecast error, period comparison chart, cumulative difference chart and outcomes table. Keep negative outcomes visible. “Simulated cost difference” must not become “realized savings.”

### Data tools

Data & Integrations has eight tabs: Connections, Data Quality, Overrides, Audit Trail, Model & Data Limitations, Decision Parameters, Model Cards, Model Status. Model Cards contains four expanders. Decision Parameters contains a classification legend expander.

Data Explorer has five tabs: Route Freight Series, Dataset, Correlation Matrix, Quality Audit, Validate & Preview Dataset. **The current Dataset tab is empty:** the processed dataset table/download are actually rendered under Route Freight Series because of the source indentation. Preserve the capability, not this placement error. Uploads validate/preview a CSV and do not replace the active modeling dataset. Override notes are logged and do not modify model inputs. Connection-table “Refresh,” “Configure” and “Add Key” entries are display strings, not working buttons.

## User workflows

1. **Review a shipment:** Overview → View Recommendation → Charter Workbench → adjust input controls → Solve Candidates → inspect candidate costs, alternatives and sensitivity → download procurement PDF.
2. **Inspect the market:** Markets → Forecasts → choose a route/model/horizon → Update Forecast → expand route comparison → inspect synthetic validation separately from external weather validation.
3. **Stress-test:** Scenarios → choose a preset or edit shocks → Run Scenario Simulation → compare baseline/stressed outputs → Decision Twin → inspect active-scenario context, cost surface and simulated downside.
4. **Evaluate the decision rule:** Backtesting → select route/date interval → Run Simulation Backtest → compare modeled outcomes against immediate charter. Historical periods are synthetic demonstration records.
5. **Inspect trust and inputs:** Data → Connections/Data Quality → Parameters/Model Cards/Model Status → record a manual note → Audit Trail. Explorer → filter route series → download CSV, inspect correlation/quality, or preview an uploaded CSV.

These are implemented navigation/control paths, not a guarantee that every backend data source is synchronized. In this snapshot, Forecasts and Overview use route-specific histories while Charter Workbench and the Decision Twin page explicitly load the older shared dataset. Preserve clear data identity and flag reconciliation as separate engineering work.

## Data and integrations

| Category | Actual source / behavior | Appropriate presentation |
|---|---|---|
| Operational live data | No verified commercial operational feed used in this capture | Do not claim live fleet, prices, queues or bookings |
| Historical demonstration data | Five bundled synthetic daily CSV series, 974 days, 2024-01-01 to 2026-08-31 | SYNTHETIC / DEMO; show covered period |
| Route histories | Bundled `data/route_freight_rates.csv`, generated by `backend/route_market.py` | Route-specific SYNTHETIC histories, assumed route profiles |
| Forecasts | Naive/SARIMA outputs; optional Prophet; interval estimates | Forecast/model output with horizon and training-data identity |
| Decision simulations | Enumerated costs, hypothetical shocks and Monte Carlo samples | Modeled / simulated; explain assumptions |
| Public weather validation | Existing Open-Meteo archive cache, passed through validation module | Cached public external weather series; not real freight validation or a live maritime weather feed |
| Commercial connectors | Freight/AIS/port/commodity adapter interfaces currently return bundled data; credentials/configuration checks are not proof of retrieval | Demo / not configured, according to implementation |
| Uploads / overrides | CSV preview only; operator note logging only | Label their limited effect explicitly |

The capture run used `DATA_MODE=DEMO`, existing synthetic files and the existing public weather cache in an isolated copy. It did not configure commercial credentials, log into production services or copy the original workspace database.

## UI requirements and constraints for Stitch

- Design a premium enterprise decision-support interface with strong hierarchy, restrained color, readable dense tables and clear selected states.
- Keep INR, ₹/tonne, Cr/lakh, USD where explicitly used, tonnes, days/hours, dates, risk scores and percentage changes unambiguous.
- Place active shipment, route, data mode and data period near decision outputs. Preserve baseline-versus-scenario context and distinguish a recommendation change from a cost-only change.
- Keep source disclosures near metrics rather than only in a footer. Provide explicit unavailable, unsupported-route, infeasible, empty-table and upload-validation states.
- Keep essential chart legends, axes, confidence/simulation intervals, comparison labels, and table column meanings. Use the component screenshots to inspect fine detail.
- Preserve all actual inputs, exports, tab content and expandable explanations. A more compact information architecture is welcome; removing capability is not.
- Use the existing FreightIQ wordmark/blue brand as reference. Current light and dark themes are captured; ensure future tables, charts and controls use a consistent theme.
- Do not copy known rendering defects, placeholder market narratives, “undefined” chart labels, or conflicting dates as intended product behavior.
- Do not invent live integrations, calibrated probabilities, a global optimization solver, booking/execution, permission management, notifications, editable parameter administration or maps.
- No redesign, algorithm changes, business-rule changes or backend refactoring were performed for this package.

## Suggested upload sequence

Start with the 1920-wide default viewport images for all eleven pages, then the full-page versions for context. Add the charter detail/sensitivity, Forecasts route comparison and weather-validation component, Decision Twin charts, Scenario presets, integration tabs/model cards and Explorer tabs. Use 1440 captures to judge density, and the optional 768 captures to understand current responsive failures. `gallery.html` and `SCREENSHOT_INDEX.md` link every captured image.
