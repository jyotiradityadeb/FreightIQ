> Historical audit snapshot: inspected commit edb25dd1beca6e3e4e1bdec3547dfbfbe2ff5122 on 2026-09-17. Later commits and working-tree changes are not covered. Findings and test counts below describe that snapshot, not the current repository. Local evidence paths refer to the original audit machine.

# FreightIQ current-state repository audit

Audit date: 17 September 2026. Scope: source inspection, fresh local execution, browser rendering, test execution, and a generated PDF. No application source, configuration, documentation, or tests were edited. No fixes, commits, or pushes were made.

All repository inspection and execution commands ran with working directory `C:\Users\jyoti\OneDrive\Desktop\FreightIQ`. Audit scripts and evidence were written outside it, under `C:\Users\jyoti\.codex\FreightIQ-audit-20260917`.

**Main finding:** this is a functioning SYNTHETIC decision-support prototype with useful calculation modules, but its UI, documentation, and PDF do not consistently reflect those calculations. Ten of eleven default pages rendered; Forecasts failed in the external-validation chart. All 144 automated tests passed. Neither result establishes commercial readiness or real freight forecast accuracy.

Status vocabulary: WORKING means the stated, bounded behavior was verified; PARTIAL means functioning elements coexist with material limitations; BROKEN means a specific failure was reproduced or directly established; NOT IMPLEMENTED means the requested behavior is absent; UNVERIFIED means evidence is insufficient. A page-render PASS does not mean all controls or claims are correct.

## 1. Repository identity and inspection boundary

| Item | Verified value |
|---|---|
| Absolute working directory | `C:\Users\jyoti\OneDrive\Desktop\FreightIQ` |
| Branch | `main` |
| HEAD | `edb25dd1beca6e3e4e1bdec3547dfbfbe2ff5122` |
| Remote | `https://github.com/jyotiradityadeb/FreightIQ.git` |
| Tracked working-tree changes | None at start and at final recheck |
| Initial untracked paths | `.claude/`, `data/validation/`, `screenshots/` |
| Later untracked path | `test_report.pdf` additionally appeared during the audit interval; its creating process is UNVERIFIED. It was not deleted or treated as audit evidence. |
| Python | 3.11.9, Windows 64-bit |
| Streamlit | 1.56.0 |
| pandas / Plotly | 2.3.0 / 6.6.0 |
| Entrypoint | `app/Home.py`, launched by `python -m streamlit run app/Home.py` |
| Imported storage module | `C:\Users\jyoti\OneDrive\Desktop\FreightIQ\backend\storage.py` |
| Imported app package | `C:\Users\jyoti\OneDrive\Desktop\FreightIQ\app\__init__.py` |

One fresh Streamlit server was started from this root at `http://127.0.0.1:8517`, bound to loopback, headless, with usage telemetry disabled. All browser pages in this audit used that server. No old screenshots were used as runtime proof.

Runtime side effects are distinct from source changes: importing storage initializes SQLite; opening Charter Workbench automatically saves the shipment and logs a decision. Thus the requested runtime inspection can write the ignored workspace database through existing application behavior. Compileall/pytest also create ordinary cache files. The database was not reset.

Latest ten commits, newest first; all dated 17 September 2026, local timezone +05:30:

| Commit | Time | Subject |
|---|---|---|
| `edb25dd` | 17:55:39 | Batch E: remove synthetic target leakage via shared latent-factor generator |
| `510f149` | 15:28:32 | Batch D: real-data validation path, model cards, and trust panel |
| `3acb9fb` | 15:14:19 | Batch C2: computed sensitivity analysis, robustness panel, optimizer explainability |
| `0bb9564` | 14:36:11 | Batch C1: extract decision constants to config with provenance; correct optimizer terminology |
| `039a306` | 14:26:03 | Batch B: replace fake fallback metrics with honest INSUFFICIENT_DATA status |
| `6c30e9c` | 14:06:04 | Batch A: honest labeling of synthetic metrics and claims |
| `2cf6ebf` | 13:49:03 | Silence Pydantic protected_namespaces UserWarning on ForecastRequest |
| `7f4226e` | 13:48:06 | Fix PDF header/footer non-ASCII glyphs by registering Bitstream Vera Sans |
| `6620fa7` | 13:45:27 | Fix audit trail always returning [] due to log_id/id schema mismatch |
| `c901a85` | 13:13:43 | Update dashboard themes, control tower views, and reporting |

## 2. Current architecture and important modules

The Streamlit UI imports backend Python functions directly. It does not depend on the FastAPI server for ordinary page execution. FastAPI is a second interface to overlapping backend functions.

| Area / module | Actual role |
|---|---|
| `app/Home.py`, `app/pages/1_Control_Tower.py` | Thin entrypoints into the same shared view, with different titles. |
| `app/views/control_tower_view.py` | Overview/Control Tower dashboard: forecast, disruption summary, market charts, shipment summary, PDF button; contains hardcoded activity and robustness displays. |
| `app/pages/` | Ten standalone Streamlit pages; page-specific controls often use local defaults rather than a fully shared shipment/scenario model. |
| `app/navigation.py` | Central relative page-path constants and `st.switch_page` wrapper. On failure it displays an error; despite its comment, it does not actually navigate Home. |
| `app/components/helpers.py` | Currency conversion at 84 INR/USD; lakh/crore formatting; CSS theme; SVG logo; decorative top shell; sidebar; cached CSV/feature loading; shipment session-state defaults. |
| `app/components/charts.py` | Plotly freight, forecast, commodity, congestion, backtest and cumulative-difference charts. Shared theme follows `fiq_theme`. |
| `app/components/cards.py` | KPI, recommendation, comparison and route presentation helpers. |
| `app/components/error_boundary.py` | Catches selected component errors and exposes a warning plus expandable technical details. Not a global page error boundary. |
| `backend/data_loader.py` | Outer-merges five CSVs by date, sorts/deduplicates, forward/backward fills missing values; validates uploaded CSV schema and inserts defaults for missing fields. |
| `backend/features.py` | Calendar, freight lags, rolling averages/volatility, momentum, commodity returns/correlation and congestion/supply changes. Produces 35 columns including date. These extra features are not exogenous regressors in the current freight models. |
| `backend/forecasting.py` | Naive damped-trend, SARIMA and optional Prophet forecasts; error metrics, comparison, model selection and insufficient-metric statuses. See section 12 for unequal evaluation protocols. |
| `backend/forecasts.py` | Compatibility re-export of `backend.forecasting`; no separate engine. |
| `backend/vessel_forecast.py` | Seven-day moving-average/trend projection of synthetic vessel counts; qualitative variance-based confidence. |
| `backend/optimizer.py` | Feasibility filtering and exhaustive date × vessel enumeration for a fixed origin/destination; costs, sorting, recommendation and alternatives. |
| `backend/config.py` | Legacy operational dictionaries for three vessel classes, nine origin/destination pairs, three destination ports, two cargo types, demo FX and disclosures. These drive the optimizer. |
| `backend/config_model.py` | Loads YAML once on import; exposes eleven constants and a provenance registry. |
| `config/decision_model.yaml` | Eleven annotated assumption parameters, editable metadata and sensitivity ranges; not a complete inventory of decision-driving constants. |
| `backend/sensitivity.py` | Four one-at-a-time assumption sweeps around a baseline, with recomputed costs and vessel/date stability. |
| `backend/decision_twin.py` | Seeded Monte Carlo paths, candidate cost distributions, hindsight regret, composite robustness, waiting-cost comparison, Pareto classification and heuristic counterfactual outputs. |
| `backend/scenario_engine.py` | Copies/perturbs forecast inputs, reoptimizes, compares costs, computes assumption-based confidence, sensitivity, threshold sweeps and alternate-port rankings. |
| `backend/disruption_engine.py` | Rule-based signal severity, alerts, market stress, decision stability, port/route status and action summaries. These are heuristic composites, not learned risk models. |
| `backend/data_quality.py` | Freshness helpers and Pydantic metadata structures; the system summary populates hardcoded freshness/coverage/source statuses rather than probing connectors. |
| `backend/validation.py` | Open-Meteo archive fetch/cache, separate PUBLIC_REAL validation result, hold-out metrics and chart inputs; also wraps SYNTHETIC metrics. |
| `backend/reporting.py` | ReportLab PDF bytes, currency strings, numbered pages, optional scenario/Twin/validation arguments; substantial narrative and fallback figures remain hardcoded. |
| `backend/storage.py` | SQLite shipment upserts, JSON payloads, audit appends, explicitly numbered decision versions, migrations and compatibility aliases. |
| `backend/main.py`, `backend/schemas.py` | FastAPI routes and Pydantic request/response definitions. |
| `backend/domain/commodities.py` | Fifteen commodity catalogue entries and custom commodity creation, including density/stowage/handling metadata. |
| `backend/domain/vessels.py` | Nine vessel specifications, capacities, draft, compatible cargo/ports, speed and fuel assumptions. |
| `backend/domain/ports.py` | Fourteen port records, coordinates, draft limits and source/assumption metadata. |
| `backend/domain/routes.py` | Thirteen route records and route/transit helpers. These richer masters are not the optimizer's authoritative dictionaries. |
| `backend/integrations/` | Adapter contract, five adapters and manager; four adapters always read local CSVs; weather has an explicit public HTTP branch. |
| `data/` | Five SYNTHETIC CSVs plus deterministic generator. `data/validation/` contains an untracked external weather cache. |
| `tests/` | Seventeen test modules, 144 collected cases. No committed browser page-render suite was found. |
| Root deployment files | Dockerfile runs Streamlit; Compose adds a separate FastAPI service. Fresh container execution was UNVERIFIED. |

## 3. Current product capabilities

| Capability | Status | What it actually does / limitation |
|---|---|---|
| Overview / Control Tower | PARTIAL | Renders forecast and default disruption recommendation; duplicated views; hardcoded robustness/activity; active shipment heading can diverge from backend default calculation. |
| Market Intelligence | PARTIAL | Displays synthetic rates/indices and a chart. Trends, bunker quote and news are hardcoded; date-range type check is incompatible with the installed range return type. |
| Forecasting | PARTIAL; external chart BROKEN | Forecast/metrics render, then a Plotly Timestamp annotation raises TypeError. Route selector changes wording, not input data/model. |
| Scenario Lab | PARTIAL | Presets and shocks recompute cost comparisons. No full cross-page scenario propagation, no Reset control, and cost-only changes are described as a changed charter decision. |
| Charter Optimizer | PARTIAL | Computes feasible date/vessel rankings and sensitivity. Laycan control handling, unsupported port fallbacks and narrative issues undermine correctness outside the default display. |
| Decision Twin | PARTIAL | Real computed synthetic Monte Carlo cost/regret outputs; hardcoded UI tipping points and 82% caption; vessel-supply paths do not constrain candidate costs. |
| Backtesting | WORKING within SYNTHETIC scope | Default walk-forward calculation and charts render; current result is negative, not the documented ~83% win rate. |
| Data Explorer | PARTIAL | Inspection, correlations, processed CSV download and upload validation/preview work. Upload does not replace the forecasting dataset despite UI wording. |
| Data Integration | PARTIAL | Tabs, registry, audit reads and weather-cache metrics render. Connection/freshness displays are not actual connection checks; manual override only logs. |
| PDF reporting | PARTIAL | Generates readable PDF bytes and page numbering. Contains fabricated/default analysis when results are omitted; current page calls omit important inputs. |
| Audit trail | WORKING for implemented writes | Shipment saves, decision saves and manual override actions can be logged and read. It does not record every model execution. |
| Shipment persistence | PARTIAL | Save/load APIs work; UI defaults are not automatically restored from SQLite; default decision version is overwritten on rerenders. |
| External integrations | PARTIAL | Public weather HTTP path and weather archive cache exist. Commercial freight/AIS/commodity/port retrieval is NOT IMPLEMENTED. |
| FastAPI | PARTIAL | Nine defined application routes and five API tests pass; validation/error-handling and production controls are limited. |

## 4–5. Streamlit page map and fresh browser runtime

Visible sidebar names come from filenames, while headings often use different product names. Routes below were read from rendered navigation links, then opened individually using Playwright in headless Microsoft Edge. Timing is one end-to-end navigation-to-footer/exception measurement, including browser/Streamlit overhead, on the same fresh server; it is not a cold-start benchmark or CPU profile.

| File under `app/` | Sidebar → visible heading | Route | Major dependencies / purpose | Render | Seconds | Duplication |
|---|---|---|---|---|---:|---|
| `Home.py` | Home → Overview | `/` | Shared view, forecast, disruption, charts, PDF | PASS | 12.313 | Same view as Control Tower |
| `pages/1_Control_Tower.py` | Control Tower → Control Tower | `/Control_Tower` | Same shared view | PASS | 11.996 | Same view as Home |
| `pages/2_Decision_Twin.py` | Decision Twin | `/Decision_Twin` | Forecast, Monte Carlo engine, direct Plotly, PDF | PASS | 12.089 | Separate simulation view |
| `pages/3_Operations_Overview.py` | Operations Overview | `/Operations_Overview` | Forecast, vessel projection, optimizer, shared cards/charts | PASS | 13.928 | Overlaps overview purpose, but different renderer and KPIs |
| `pages/4_Market_Overview.py` | Market Overview → Market Intelligence | `/Market_Overview` | Cached CSV/features, shared freight chart | PASS | 12.624 | Separate market view |
| `pages/5_Forecasting.py` | Forecasting → Forecasts | `/Forecasting` | Freight models, validation cache, Plotly | FAIL | 15.095 | Main forecast plus external validation |
| `pages/6_Charter_Optimizer.py` | Charter Optimizer → Charter Workbench | `/Charter_Optimizer` | Forecast, optimizer, sensitivity, SQLite, PDF | PASS | 13.030 | Separate procurement view |
| `pages/7_Scenario_Lab.py` | Scenario Lab | `/Scenario_Lab` | Forecast, ScenarioRequest/Shock, scenario engine | PASS | 7.358 | Separate shock comparison |
| `pages/8_Backtesting.py` | Backtesting → Simulation Backtest | `/Backtesting` | Repeated forecast fits, candidate evaluation, charts | PASS | 34.213 | Separate historical-style simulation |
| `pages/9_Data_Integration.py` | Data Integration → Data & Integrations | `/Data_Integration` | Data quality, SQLite, config registry, validation | PASS | 12.565 | Separate administrative tabs |
| `pages/10_Data_Explorer.py` | Data Explorer | `/Data_Explorer` | Features, CSV validator, Plotly correlation | PASS | 11.983 | Separate dataset inspection |

**Total: 10 PASS, 0 BLANK, 1 FAIL.** Actual visible content, not successful imports, was the criterion. PASS means content reached the disclaimer with no exception panel in that default run; it does not certify hidden interactions.

Observed page content:

- Home and Control Tower: expected logistics cost ₹26.07 Cr, charter date 2026-09-04, hardcoded 82%, Freight Market Overview, Shipment Activity, Freight Forecast.
- Operations: ₹2,901/tonne, +0.6% outlook, 28 vessels, 52 h; Freight Market Outlook and Charter Recommendation, about ₹25.95 Cr.
- Market Intelligence: summary strip, Freight Market Benchmark & Commodity Signals, Market Signals, Market Events & Operational News.
- Forecasts: main freight chart, Demo-Series Model Metrics, Forecast Explanation & Drivers and real-validation metrics appear. Then **BROKEN** at `app/pages/5_Forecasting.py:236`, `fig_rv.add_vline(...)`: `TypeError: Addition/subtraction of integers and integer-arrays with Timestamp is no longer supported`. The annotated split line reaches Plotly's numeric mean calculation on a pandas Timestamp. The real-validation chart and final disclaimer do not complete.
- Charter: Feasible Charter Candidate Matrix, recommendation ₹26.09 Cr, Scenario Comparison, Cost Model Breakdown, Why This Recommendation Was Selected, Assumption Sensitivity panel.
- Twin: Panamax / 2026-09-01, ₹25.94 Cr, **54/100**, ₹102.5 Lakh expected regret, Decision Surface, Simulated Freight Futures, What Would Change This Decision.
- Scenario: Presets, Scenario Inputs, Impact Preview and Baseline vs Stressed Scenario Comparison. East Coast Disruption was also activated and verified: +12% freight, +55% congestion, −30% supply, High weather, ₹29.31 Cr and +12.4% vs baseline; same Panamax/date but UI says ALTERED.
- Backtest: 57 windows, 43.9% win rate, −₹5.15 Cr, ₹73/t MAE, cost and cumulative-difference charts and outcomes matrix.
- Integration: eight tabs; Data Quality, Audit Trail, Decision Parameters, Model Cards and Model Status were also opened. Model Status displays 731 cached external observations and 4.194 “m/s” MAE, with incorrect units.
- Explorer: 974 rows, 35 columns, 01 Jan 2024–31 Aug 2026; Dataset, Correlation Matrix, Quality Audit and Upload Dataset tabs.

Evidence: `runtime.json`, individual page `.txt` files, fresh `.png` captures and `scenario-preset-confirmed.txt` in the audit folder.

## 6–7. Current UI/design and light/dark mode

**Assessment: B — hackathon dashboard, with some reasonably polished SaaS styling.** It is beyond stock Streamlit styling but not a coherent commercial product experience.

There is a custom geometric F/arrow SVG and FreightIQ wordmark, pale grey/white surfaces, blue primary accent, bordered cards and a restrained financial-dashboard layout. Inter is requested from Google Fonts; JetBrains Mono is imported, but the `fiq-mono` class has no matching definition in the inspected CSS. Native Streamlit sidebar links, widgets, tab underlines, dataframe canvases and Plotly toolbars remain evident. Deploy remains visible despite attempts to hide the default header/menu. Some chart titles visibly show `undefined`. At narrower width the decorative top row wraps its status text awkwardly.

The top “Overview / Markets / Forecasts / Scenarios / Chartering / Decision Twin / Data” bar is made of HTML `span` elements, **not navigation links**. Actual navigation is the sidebar and selected action buttons. Page names differ between sidebar, document title and heading. Home and Control Tower duplicate the same dashboard; Operations adds a third overlapping overview.

Theme implementation is real but incomplete:

- Custom sidebar toggle exists. Session key: `fiq_theme`; default `light`; `toggle_theme()` switches it then `st.rerun()` executes.
- Runtime verified dark mode and persistence from Market Overview to Data Explorer through sidebar navigation. Persistence beyond the Streamlit session/reload is NOT IMPLEMENTED; there is no saved user preference.
- CSS variables cover page/sidebar backgrounds, typography, some inputs/buttons and cards. Light background `#F6F8FB`, light surface `#FFFFFF`, blue `#1667D9`; dark background `#0E1117`, dark surface `#151A22`, blue `#4D8DFF`.
- Shared Plotly helper reads `fiq_theme`; the market chart visibly changed to dark. Decision Twin's direct Plotly figures hardcode white plot backgrounds; the external validation chart also hardcodes white. These do not consistently follow the shared theme.
- Runtime dark screenshot: the Quality Audit dataframe remained white; the Market date input text had poor contrast. CSS customization is not equivalent to changing Streamlit's own theme for canvas-rendered tables.
- All pages call the shared CSS/sidebar helpers directly or through the shared view. Complete two-theme visual verification of every page/control is **UNVERIFIED**; consistent full support is contradicted by the inspected hardcoded colors and observed table/input mismatch.
- Hardcoded color examples: Market event text `#111827`; Twin heatmap text/white plots; Forecast validation white plots/dark annotations; many page subtitles use `#6B7280`; status colors and badges use fixed colors. `badge-demo`, `badge-online`, `fiq-avatar` have markup without corresponding styling in the inspected CSS.

## 8. Synthetic data generation and leakage

All five main CSVs are **SYNTHETIC**, with 974 daily rows from 2024-01-01 through 2026-08-31. Generator: `data/generate_demo_data.py`; `RANDOM_SEED=42`. It constructs latent demand, supply tightness, bunker cost, port stress, commodity demand, macro cycle, weather and discrete shock processes, then adds independent observation noise. It does not query external data.

Simplified formulas below omit clipping/rounding and use D=demand, S=supply, B=bunker, P=port stress, C=commodity, M=macro, H=shock, W=weather, t=day index, ε=series-specific noise:

| Series | Actual generator formula / bounds |
|---|---|
| Freight USD/t | `24 + 4D + 2.5S + 2B + 1.5P + 0.8H + Q3 bump + ε`; clipped 12–48 |
| BDI | `1100 + 280D + 140S + 65B + ε`; 300–3500 |
| Capesize index | `2200 + 520D + 240S + 90B + ε`; 500–7000 |
| Panamax index | `1150 + 245D + 115S + 42B + ε`; 350–3000 |
| Iron ore USD/t | `108 + 13C + 6M + 8cos(2πt/365.25) + .014t + ε`; 60–200 |
| Coking coal USD/t | `228 + 20C + 9M + 15sin(2πt/365.25+.5) + .025t + ε`; 130–400 |
| Congestion | `45 + 18P + exponential noise`; 15–98 |
| Waiting hours | `.65 × congestion + ε`; 8–96 |
| Vessel availability | `35 − 3.5S − 2D − .12(congestion−45) + ε`; 10–60, integer |
| Weather risk | `4W + 4 + ε`; 0–10 |
| Event risk | Base 1.5, fixed elevated windows around days 120/310/580/810, plus noise; 0–10 |

Demand/supply/bunker/port/commodity/macro use AR(1) coefficients .97/.99/.95/.90/.96/.98 respectively, with seasonality and/or drift. Shared latent factors create correlation; they do not copy the target into other observed series.

**Direct target-derived synthetic feature leakage in the generator has been removed.** BDI, vessel indices and commodity prices are no longer functions of `freight_rate`. This conclusion comes from formulas, not correlation alone. Structural/determinism/leakage tests passed.

This does not establish a generally leakage-free ML pipeline. `data_loader.py` performs backward fill and whole-data median imputation, which could introduce future information when historical data is incomplete. Rolling freight features include the current target; those must be aligned carefully if used in a future supervised model. Current Naive/SARIMA/Prophet freight models are univariate and do not consume those engineered regressors.

Other generators/fallbacks remain: Overview constructs a 60-day sinusoidal fallback if loading/evaluation fails; Decision Twin generates stochastic futures; CSV upload validation fabricates missing-column defaults. These must not be confused with external observed data.

Data categories: main CSVs and simulation paths SYNTHETIC; Open-Meteo archive cache PUBLIC_REAL external weather (reanalysis, see section 10); optional public current-weather adapter PUBLIC_LIVE; commercial CONNECTED_REAL retrieval NOT IMPLEMENTED; manual input is scenario/configuration input, not verified market observations. Cached processed data uses `st.cache_data` without TTL; archive CSV and one-hour UI validation cache are separate.

## 9. Actual provenance system

There is **no single unified provenance enum**:

- `backend.validation.DataMode`: `SYNTHETIC`, `PUBLIC_REAL`, `CONNECTED_REAL`, `MANUAL_REAL`.
- `backend.data_quality.DataMode`: `DEMO`, `PUBLIC_LIVE`, `CONNECTED`; metadata comments/strings also mention `MANUAL_OVERRIDE` and `LIVE_READY`.
- Adapter output: `source_name`, `source_mode`, `retrieved_at`; DEMO outputs add “Synthetic Demo”. Non-DEMO base metadata uses `LIVE_READY`, even when values still come from synthetic CSVs.
- UI badges/labels include D/P/C/M concepts, “DEMO MODE”, “LIVE API”, synthetic captions, limitations, model cards and status tables.
- PDF includes DEMO mode and synthetic validation disclosures; optional external result uses PUBLIC_REAL. Default page calls do not pass that external result.

The enum presence does not mean all modes have implementations. CONNECTED_REAL and MANUAL_REAL do not establish working commercial/manual ingestion. Data quality assigns weather PUBLIC_LIVE and fresh timestamps without fetching it. Static connection rows cannot verify connectivity. Model cards and validation panels communicate scope in places, but other visible statements contradict them.

## 10. External real-data validation

**Type B: validation of time-series forecasting machinery using a non-freight external series. Real freight validation is NOT IMPLEMENTED.**

Module: `backend/validation.py`. Source: Open-Meteo Archive API. Request coordinates 20.26 N, 86.67 E near Paradip; daily variable `windspeed_10m_max`; timezone Asia/Kolkata; default lookback 730 days ending five days before today. This is a public weather archive, not Baltic freight or AIS data.

Fresh cached execution returned:

| Item | Measured result |
|---|---|
| Source classification | PUBLIC_REAL in repository vocabulary |
| Date range | 2024-09-12 through 2026-09-12 |
| Observation count | 731 |
| Training split | 701 observations through 2026-08-13 |
| Held-out test | 30 observations, 2026-08-14 through 2026-09-12 |
| Requested model | SARIMA(1,1,1)(1,0,0)[7] |
| Status | OK |
| MAE | 4.194 |
| RMSE | 4.867 |
| MAPE | 25.00% |
| Cached validation runtime | 0.2303 s |

**Unit bug, verified:** fetch parameters do not request m/s. A fresh API request for 10–12 September returned `daily_units.windspeed_10m_max = "km/h"` and values 15.6, 28.6, 25.9, exactly matching the cache tail. Therefore the present MAE/RMSE are in **km/h**, while code/UI/PDF labels say **m/s**. The cache stores only dates/values, losing the response unit metadata. Converted numeric errors would be approximately 1.165 and 1.352 m/s, but the application does not perform that conversion.

Source terminology also needs precision: Open-Meteo describes the historical service as reanalysis using observations plus models. It is not a verified on-site anemometer measurement at the port. Treat PUBLIC_REAL as the app's external-data classification, not proof of direct observations. [Official Open-Meteo historical API documentation](https://open-meteo.com/en/docs/historical-weather-api).

Cache behavior: `data/validation/openmeteo_paradip_wind.csv` exists but is untracked. A cache with at least 90 rows is reused indefinitely unless `force_refresh=True`; there is no age/coordinate/variable validation. Fetch failure falls back to any readable cache; no cache yields UNAVAILABLE; fewer than horizon+60 observations yields INSUFFICIENT_DATA with null metrics. Offline branches have tests. UI caches chart data for 3600 seconds, while the underlying disk cache has no expiry. A clean clone may need network access to populate it.

The validation module implements its own predictor with the same SARIMA specification; it is not an end-to-end validation of the freight feature/data/optimizer pipeline. SARIMA exceptions silently fall back to the naive predictor while the result can retain `model_name="SARIMA"`; actual fallback identity is not exposed. The validation chart band is recent training standard deviation ±1σ, not model-derived 95% intervals. Its UI render currently fails at the annotated split line.

## 11. Current SYNTHETIC validation numbers

These are fresh calculations on the current 974-row CSV series, not historical report figures. MAE/RMSE below are USD/t; UI uses ×84 for INR/t.

| Evaluation | Model | MAE | RMSE | MAPE | Selected |
|---|---|---:|---:|---:|---|
| 14-day engine comparison | Naive Baseline | 0.634 | 0.757 | 1.81% | Yes |
| 14-day engine comparison | SARIMA | 0.680 | 0.871 | 1.93% | No |
| 30-day engine comparison | Naive Baseline | 0.619 | 0.760 | 1.79% | No |
| 30-day engine comparison | SARIMA | 0.519 | 0.664 | 1.50% | Yes |
| Default walk-forward backtest | Auto per decision point | 0.874 | 1.112 | 2.87% | Varies |

The default Forecasts page shows 14-day synthetic metrics (approximately ₹53/t MAE and ₹64/t RMSE); Operations also shows a synthetic MAE. Backtesting displays approximately ₹73/t MAE. Its 57 windows yield 25 wins, **43.9%**, and total simulated cost difference **−USD 612,577.50 = −INR 51,456,510 = approximately −₹5.15 Cr**, or −0.40% versus immediate charter. These are hypothetical repeated-shipment costs under the model, not realized financial results.

Default Twin: 1,000 SYNTHETIC futures, seed 42; Panamax/Paradip on 2026-09-01, mean USD 3,088,455.50 (₹25.94 Cr), robustness 54/100, mean regret ₹102.5 Lakh. Overview instead displays hardcoded 82%; Twin's caption also hardcodes 82%. Their provenance captions say demo, but those displayed figures are not generated by the current run.

Synthetic labels are explicit on Forecasts, Backtesting, Twin and sensitivity. Global footer labels the prototype synthetic. **It is not true that every figure is correctly and explicitly labeled:** the PDF's ~83%, INR 105/t, 82/100, INR 18 Lakh and scenario-stability statements remain hardcoded; static market news/activity/source freshness resemble current observations without local synthetic labels.

## 12. Forecast engine: models, evaluation and fallbacks

- Available here: Naive Baseline and SARIMA. Prophet is optional in code but **not installed** in this environment. No ensemble is computed despite “Ensemble v2.4” in the sidebar.
- Naive forecast = last rate + half of recent 14-day slope × future day. It uses recent 30-value standard deviation for a constant-width ±1.96σ band; with fewer than 30 values, σ defaults to **1.5**.
- SARIMA: `(1,1,1)` × `(1,0,0,7)`, stationarity/invertibility enforcement disabled, 95% forecast interval. Interval-shape fallback is prediction ±1.5. Fitting errors return naive output with a fallback label on the forecast dataframe.
- Prophet: yearly/weekly seasonality, no daily seasonality; code uses Prophet's returned interval without explicitly setting a 95% width, yet shared UI labels intervals 95%. This optional path was not runtime-tested here.
- Auto computes all available model candidates and chooses the lowest non-null MAE. Manual selection still computes other candidates. Models with insufficient metrics are excluded; if all are insufficient, naive is chosen with an explicit reason.
- Minimum metric history: naive needs `len(series) > horizon`; SARIMA/Prophet need a training remainder greater than 30, i.e. at least horizon+31 observations. Short series can still produce forecasts. Empty dataframe handling is not robust because naive immediately indexes the last row.
- **Evaluation inconsistency:** naive metrics compare each of the last horizon observations with its preceding actual observation (rolling one-step persistence). SARIMA/Prophet train before the last horizon rows and forecast the whole hold-out horizon. These are different protocols, and naive's scored persistence predictor differs from its deployed damped-trend multi-step forecast. Auto's MAE ranking is therefore not a fair same-task comparison.
- MAE/RMSE/MAPE are computed and rounded. Short-series fake metric triplets were removed. Null metrics and INSUFFICIENT_DATA are now real behaviors. Remaining numeric fallbacks include interval σ=1.5 and MAPE=0 if there are no nonzero targets; the latter should not be interpreted as demonstrated accuracy.
- Global warning suppression and broad fit exception handling can obscure model problems. Candidate name can still say SARIMA even when its dataframe contains a naive fallback.
- No exogenous BDI, fuel, congestion or commodity variables enter current freight models. The Forecasts “driver impact decomposition” is hardcoded. Its “soften moderately” interpretation is also static; default Operations currently computes a positive +0.6% outlook.

## 13–14. Optimizer and actual cost model

**Algorithm:** constrained exhaustive enumeration, followed by sorting. No PuLP import/use; no LP or MILP solve; no continuous optimization. It examines each forecast date inside the requested date window and either the requested vessel or three classes (Capesize/Panamax/Supramax). Origin and destination are fixed inputs for this optimizer call. Scenario alternate-port analysis and Decision Twin separately evaluate more ports; base optimizer does not jointly search all routes/ports.

Feasibility checks: cargo quantity ≤ vessel max capacity; vessel in route's allowed list; available vessel count ≥8. It does not enforce minimum vessel load, actual numeric draft against port depth, commodity stowage/handling, delivery deadlines, multi-cargo packing or charter-contract clauses. Unknown route silently gets multiplier 1 and all three vessels; unknown vessel/port uses Panamax/Paradip defaults. UI names Haldia and Gangavaram are not keys in the legacy destination dictionaries (`Kolkata/Haldia` is the supported key).

For a feasible candidate:

```
unit freight = forecast USD/t × route freight multiplier × vessel multiplier
freight cost = unit freight × cargo tonnes
demurrage = ((configured port laytime hours + waiting hours) / 24)
             × daily demurrage USD × exposure factor
congestion = congestion index × configured port USD/hour coefficient
             × congestion multiplier
risk = risk-tolerance multiplier ×
       (weather score × weather USD/point + event score × event USD/point)
total = freight + demurrage + congestion + risk
effective cost/t = total / cargo tonnes
```

Sort key: rounded total USD, then date, then vessel name. Option A is the first; Option B second; Option C earliest-date candidate. This establishes the lowest modeled cost within the enumerated feasible set, not the cheapest attainable market charter.

Current default Charter Workbench, 75,000 t Coking Coal, Australia→Paradip, 1–15 September 2026, demurrage 22,000 USD/day: 30 feasible candidates, Panamax on 2026-09-04; unit freight USD 40.96/t; freight USD 3,071,835; demurrage USD 9,900; congestion USD 16,875; risk USD 7,200; total USD 3,105,810 = ₹26.09 Cr.

**Input provenance:** freight is derived from SYNTHETIC historical data. In the workbench the forecast dataframe contains no congestion, waiting, supply, weather or event columns, so the optimizer uses hardcoded defaults **45, 24 h, 25 vessels, 3, 2**, respectively. These are not the latest CSV values (77.8, 51.8 h, 28, 7.3, 1.7). Port/vessel rates and multipliers are configured assumptions; YAML explicitly calls major penalty coefficients DEMO_ONLY_ASSUMPTION. No empirically calibrated/literature-cited cost coefficients were verified. Distance/transit/bunker fields exist in configuration/domain records but are not separate observed cost terms here.

Demurrage is not a contractual excess-laytime calculation: all configured laytime plus waiting is multiplied by a demo exposure factor. Congestion multiplies a dimensionless index by a USD/hour value and another arbitrary factor; it is not measured waiting hours × a verified rate. Cargo commodity prices do not enter total logistics cost.

Verified correctness defects:

- `optimizer.py:241` sets `earliest_dt` to `candidates[0]` **after cost sorting**, so it is the winning date; days-from-start becomes zero. The default report says “Charter immediately on earliest window date” while recommending September 4 in a September 1–15 window.
- `optimizer.py:338` builds `risk_cost_usd` when risk is the dominant cost component, but the stored field is `route_risk_penalty_usd`. A read-only call with dominant weather penalty reproduced **KeyError: 'risk_cost_usd'**.
- Workbench date-range code accepts only `list`; installed Streamlit range date widgets return tuples. Its fallback silently reinstates the default 1–15-day window. Market date filtering has the same list-only guard. Full arbitrary date-control interaction coverage remains UNVERIFIED, but the source/type mismatch is established.
- Workbench reruns calculations and SQLite writes even when “Solve Candidates” was not clicked; the button value is unused.

## 15. Decision-parameter registry

Eleven parameters, read once at import. Six are DEMO_ONLY_ASSUMPTION and five CONFIGURED_ASSUMPTION. None is classified OBSERVED, DERIVED or LITERATURE_INFORMED. Ten have `editable: true`, but this means a **future** UI may expose editing; the current UI registry is read-only. Editing YAML is possible as source/configuration work, and imported constants require process/module reload to take effect. No edits were made.

| Parameter | Value | Unit | Classification | Source / note | Sensitivity range | Editable metadata |
|---|---:|---|---|---|---|---|
| demurrage_exposure_factor | 0.15 | dimensionless fraction of daily demurrage rate | DEMO_ONLY_ASSUMPTION | Internal prototype calibration — no empirical basis — Scales the daily demurrage rate to an expected per-shipment cost. Real demurrage exposure depends on laytime clauses, commodity-specific stowage rates, and port productivity — none of which are modelled here. Must be replaced with a contract-specific calculation before production use. | 0.05–0.5 | True |
| congestion_cost_multiplier | 0.5 | dimensionless scaling factor on congestion_score × cost_per_hour | DEMO_ONLY_ASSUMPTION | Internal prototype calibration — no empirical basis — Converts the 0–100 port congestion index and port-specific cost-per-hour into a total congestion charge.  The 0.5 factor is arbitrary; real port waiting cost depends on berth allocation, commodity priority, and operator agreements. | 0.1–2.0 | True |
| vessel_availability_min_threshold | 8 | vessel count (integer) | CONFIGURED_ASSUMPTION | Operator judgment — consistent with thin spot-market liquidity heuristic — Below this fleet count a charter date is declared infeasible. Calibrate to actual spot-market depth for each trade lane. | 3–20 | True |
| risk_factor_low_tolerance | 1.5 | dimensionless multiplier on risk penalty | CONFIGURED_ASSUMPTION | Symmetric design choice: Low=1.5× Medium, High=0.5× Medium — Applied to weather and event risk penalties when the user selects Low risk tolerance (i.e. they are more averse to risk and pay a larger penalty for uncertain outcomes). | 1.0–3.0 | True |
| risk_factor_medium_tolerance | 1.0 | dimensionless multiplier on risk penalty | CONFIGURED_ASSUMPTION | Baseline (neutral) reference value — Reference level — all other risk factors are scaled relative to this. | 1.0–1.0 | False |
| risk_factor_high_tolerance | 0.5 | dimensionless multiplier on risk penalty | CONFIGURED_ASSUMPTION | Symmetric design choice: High=0.5× Medium — Applied when the user selects High risk tolerance (willing to accept uncertain outcomes; risk penalty is discounted by half). | 0.1–1.0 | True |
| weather_risk_penalty_per_point | 1200.0 | USD per risk-score point | DEMO_ONLY_ASSUMPTION | Internal prototype calibration — no empirical basis — Cost penalty applied per unit of the 0–10 weather risk score. The 1200 USD/point figure was chosen to make weather risk visible in the cost breakdown without dominating it; it has no contractual or actuarial foundation and must be replaced by real insurance/delay cost data before production use. | 200.0–5000.0 | True |
| event_risk_penalty_per_point | 1800.0 | USD per risk-score point | DEMO_ONLY_ASSUMPTION | Internal prototype calibration — no empirical basis — Cost penalty applied per unit of the 0–10 event risk score (port strikes, geopolitical disruptions, regulatory changes).  The 1800 USD/point figure is a prototype placeholder — 50% higher than weather risk to reflect the historically longer tail of event disruptions, but with no actuarial or empirical basis. | 300.0–8000.0 | True |
| availability_shortage_penalty_per_vessel | 2500.0 | USD per vessel below threshold | DEMO_ONLY_ASSUMPTION | Internal prototype calibration — not currently applied in cost calculation — Placeholder for a future penalty when fleet count drops toward the minimum threshold.  Not applied in the current cost formula — vessel availability below threshold causes hard infeasibility instead. | 500.0–10000.0 | True |
| freight_trend_detection_threshold | 0.5 | USD/tonne | CONFIGURED_ASSUMPTION | Heuristic — prevents noise from triggering trend labels on flat series — Minimum rate change between the first and last forecast point required to label the outlook as 'Rising' or 'Softening' rather than 'Stable'. Tune to the typical intra-period volatility of the trade lane being modelled. | 0.1–5.0 | True |
| congestion_to_waiting_hours_factor | 0.55 | hours per congestion-index point | DEMO_ONLY_ASSUMPTION | Internal prototype calibration — no port-operations data basis — Converts the 0–100 congestion index to waiting hours for Decision Twin Monte Carlo simulation paths.  The 0.55 factor is a placeholder; production use requires AIS berth-queue data or port productivity models. | 0.1–2.0 | True |

The registry does not cover all recommendation-driving constants. Remaining items include:

- `backend/config.py`: vessel capacity/rate/multiplier/draft values; route multipliers/allowed-vessel lists; port laytime and USD/hour coefficients; fixed 84 INR/USD.
- Optimizer row defaults 25 USD/t, congestion 45, waiting 24, supply 25, weather 3, event 2; fallback route multiplier 1; risk-map fallback and explanation comparison tolerances.
- Workbench 22,000 USD/day, Medium risk, fixed Auto vessel, default quantity and date window; cargo/port selectboxes do not use the full domain masters.
- Twin AR=.82, freight σ=.75, congestion σ=3.5, availability σ=2.5, weather σ=.8, event σ=.6, bounds, robustness weights .4/.2/.2/.2, CV/gap/regret multipliers 2.5/10/5, 2% premium and 15-point upgrade rule, port tipping denominator `500*.5`, +4.5% adjustment, quantity thresholds 90,000/110,000/55,000, −6.2%, 7.8%, +22 congestion, −12 vessels.
- Scenario confidence base 88, penalties/maps, bonus cap 8, clipping 10–98, influence thresholds 4.5/1.5%, sweep grids, INR cost-change thresholds; disruption severity/stress/stability weights and thresholds.
- Forecast band defaults, seasonal order and trend damping; PDF fallback percentages 85/8/5/2 and fixed financial/validation figures; storage default 18.58 Cr and robustness 82.

`availability_shortage_penalty_per_vessel` is registered but explicitly **unused** in the cost calculation. Below-threshold supply makes base optimizer candidates infeasible instead.

## 16. Computed assumption sensitivity

`backend/sensitivity.py` is a real computation, not a hardcoded percentage. Parameters: demurrage exposure factor, congestion multiplier, weather penalty and event penalty. Levels: −30%, −15%, 0%, +15%, +30%, independently. One baseline plus 20 sweep calls = **21 optimizer runs**; four repeated zero-level settings are excluded from the stability denominator, leaving **16 perturbed settings**.

Measured workbench baseline: Panamax, 2026-09-04, USD 3,105,810. Same vessel/date held in **16/16 = 100%**. All four first-flip fields are null: **no flip observed within the tested grid**, not proof no flip exists. Runtime: **0.1206 s** excluding forecasting/UI. This is not a 1,000-future probability or a Monte Carlo robustness score.

Interpretation limitation: the workbench supplies constant/default non-freight signals, so several penalty changes add the same amount across dates; freight dominates. One-at-a-time ±30% stability is a narrow assumption check, not broad empirical robustness. The YAML's full min/max ranges are not the sweep range, and no joint perturbations are tested.

The scenario engine also has a different “sensitivity” routine: freight +10%, congestion +20%, availability −25%, high weather, elevated geopolitics, demurrage +20%, ranked by absolute cost impact. Its comment claiming all are +10% is inaccurate.

## 17. Decision Twin

Defaults: **1,000 futures, seed 42**, fourteen forecast days on the UI; API permits 50–5,000 simulations. NumPy's global RNG is reseeded per generation, making repeated inputs deterministic but also affecting global RNG state.

Simulation variables: freight (AR(1) .82 with normal innovation σ=.75, floor 5); congestion (normal σ=3.5, clipped 5–98); waiting = .55 × simulated congestion; vessel count (rounded normal σ=2.5, clipped 3–80); weather (normal σ=.8, clipped 1–10); event risk (normal σ=.6, clipped 1–10). These are **assumed distributions on SYNTHETIC/default state**, not fitted real-market uncertainty. It is not an i.i.d. lognormal simulation as the model card claims.

Candidate dimensions: date × allowed vessel × primary plus alternate East Coast ports. Capacity/route allowed-vessel checks are applied before the grid. If none is feasible, an unconditional Panamax fallback candidate is inserted. Vessel availability paths are generated but are **not used in the cost matrix or per-path feasibility checks**. Input waiting hours are also superseded by the congestion conversion. Contract demurrage/laytime from the active workspace is not supplied to the engine; its internal vessel/port defaults apply.

For each future, hindsight minimum is the cheapest enumerated candidate. Regret = max(0, candidate cost − hindsight minimum). Outputs include mean/median/P90/worst costs and regret, win frequency (regret < USD 1), fan quantiles, heatmap, Pareto cost/P90-regret classification and candidate summaries.

Robustness score is a rounded composite:

```
0.40 × win-frequency percentage
+ 0.20 × max(0, 100 × (1 − 2.5 × cost coefficient of variation))
+ 0.20 × max(0, 100 × (1 − 10 × relative mean-cost gap))
+ 0.20 × max(0, 100 × (1 − 5 × P90 regret / mean cost))
```

It is **not** the percentage of futures retaining the recommendation or within 5% of optimum. Selection starts with minimum mean cost; it may upgrade to a candidate with at most 2% premium and at least 15 additional robustness points. A nearby comment describes different thresholds, so source comments are not authoritative.

Cost of waiting compares the selected vessel/port at +1/+3/+5 days, clamped to the final horizon date. Current deltas: USD 1,877.53 / 3,161.74 / 8,045.58, approximately ₹1.6 / 2.7 / 6.8 Lakh. At the horizon end clamping can make multiple offsets the same date.

Counterfactuals are **PARTIAL heuristics**, not the promised numerical sweeps: port threshold uses mean-cost gap divided by `500*.5` and clips at 98; charter threshold uses cost gap plus 4.5%; quantity thresholds and −6.2% delay advice are fixed. Validity 7.8% outlook, 3–5-day review horizon and “0 of 4 thresholds” are also fixed. The UI does not render these returned counterfactuals; it hardcodes congestion 58→74, supply 19→11 and freight +2.1→+8.4%. Do not demonstrate these as computed tipping points.

## 18. Scenario engine and propagation

Backend schema supports freight −20…+30%, congestion −50…+100%, availability −60…+50%, commodity −20…+30%, demurrage −20…+50%, target port, four weather levels and three geopolitical levels. Freight scales forecast rates; targeted congestion scales congestion/waiting; availability scales counts; weather/event fields map to fixed scores; demurrage changes the override rate. **Commodity shock is accepted but does not affect the implemented cost calculation.**

UI presets: East Coast Disruption, Freight Rate Spike, Paradip Congestion, Vessel Shortage, Severe Weather Risk, Market Relief. Visible editable controls are three percentage sliders, weather and target port. UI uses fixed Coking Coal/75,000 t/Australia/Medium risk, rather than the shared shipment context. Geopolitics is always passed as Normal, even though East Coast Disruption sets an unused Elevated session value. Commodity and demurrage state keys are initialized but not exposed/consumed by the current request construction.

Session keys: `freight_shock`, `cong_shock`, `target_port`, `avail_shock`, `comm_shock`, `weather_risk`, `geo_risk`, `dem_shock`. Presets update subsets, so prior settings can carry over. “Run Scenario Simulation” does not gate execution; calculation happens every rerun. **Reset control: NOT IMPLEMENTED.** Zeroing visible controls is possible; a complete reset path is absent.

Cross-page scenario propagation is **NOT IMPLEMENTED in the current UI**: Charter Workbench does not read shock state; Twin does not pass `active_shock`; Overview calls disruption evaluation without `shock_override`. APIs accept explicit shocks, but that is a different path. Shipment state sharing does not imply shared scenario state.

Backend comparison works, but narrative is overstated: an increase greater than INR 500,000 can set “Cost Increase Under Stress”, then generic text says the charter changed even if date/vessel are identical. This was observed in the East Coast preset. Alternate-port calculation reuses one shocked dataframe for all ports, so targeted shocks are not independently rebuilt per alternative.

## 19. Backtesting

`backend/backtesting.py:run_historical_simulation` uses the supplied dataframe; current UI supplies **SYNTHETIC** CSV history. UI defaults: start 2024-06-01, end 2026-08-01 (last data day minus 30), horizon 14, interval 14, 75,000 t Coking Coal, Australia→Paradip, Panamax.

For each sampled decision date: train through that date (skip <30 observations); find future rows (skip <3); generate Auto forecast; benchmark immediate charter using current synthetic observations; choose a future date using predicted freight and current-date non-freight signals; score the selected date using that future date's synthetic observations. No future freight target is used in the forecast training split. The strategy cannot select the present date among its forecast candidates; benchmark can. Periods can overlap for other interval/horizon choices.

Metrics: per-period modeled cost/difference, total benchmark and strategy costs, percentage difference, wins including ties, and pooled forecast MAE/RMSE/MAPE. Current totals: benchmark USD 154,228,428.75; strategy USD 154,841,006.25; difference −USD 612,577.50; 25/57 wins; 43.9%; −0.40%; MAE .874, RMSE 1.112, MAPE 2.87%. Standalone calculation took 18.054 s; browser page took 34.213 s in the measured pass.

UI wording explicitly says historical-style simulation on synthetic demo data, simulated win rate and simulated cost difference. **Real-market evidentiary value: none for profitability or freight predictive accuracy.** It demonstrates code behavior under an artificial market/cost model. There is no verified real historical freight backtest. Infeasible benchmark/realized candidates can cause missing-key errors because some accesses assume feasible results; default test does not exercise all such cases.

## 20. PDF reporting: generated and reread

Function: `backend.reporting.generate_charter_decision_pdf`. A fresh report was generated using the current workbench-style optimizer recommendation with `data_mode="DEMO"`, then reopened with PyMuPDF, text-extracted, rendered and visually inspected on **both pages**. File: `current-charter-report.pdf` in the audit folder. Generation took **0.0555 s**. It has **two A4 pages**, “Page 1 of 2” / “Page 2 of 2”.

Current numbering/headings:

1. SHIPMENT & FINANCIAL LOGISTICS SUMMARY
2. MARKET OUTLOOK & FREIGHT SIGNALS
3. CHARTER RECOMMENDATION & CANDIDATE EVALUATION
4. DECISION TWIN & ROBUSTNESS ANALYSIS
5. SCENARIO ANALYSIS & STRESS TESTING
6. HISTORICAL-STYLE SIMULATION ON SYNTHETIC DEMO DATA
7. FORECAST VALIDATION STATUS
8. DATA PROVENANCE & OPERATIONAL DISCLOSURES

Currency uses **INR**, Cr, Lakh and `/ t`, intentionally avoiding ₹ in generated numeric strings. These rendered legibly; header/footer em dash and bullet rendered using bundled Vera Sans. This is not a demonstration that arbitrary ₹ text will render in all body fonts: body/table styles still use Helvetica. Mixed USD appears in optimizer explanation prose. Numbering is sequential, but section 8 is split across pages and page 2 contains only three disclosure bullets, leaving most of it blank.

Critical content limitations observed in the generated text:

- Section 4 says 1,000 futures, 82/100 and INR 18.0 Lakh regret even though no Twin result was passed. Actual current Twin is 54/100 and INR 102.5 Lakh.
- Section 5 says stress testing “confirms decision stability” for ±10% freight/±30% queue despite no scenario result being passed.
- Sections 6/7 hardcode ~83% win rate and ~INR 105/t MAE, contradicting the current backtest. `backtest_metrics` is accepted but not used for that paragraph.
- Section 2 bunker/market commentary is hardcoded; `market_outlook` is not used to generate it.
- Missing financial components can be invented as 85/8/5/2% of total; missing/zero total can become INR 185,800,000 and per-tonne INR 2,477. A legitimate zero component is also treated as missing in these paths.
- The workbench passes only its recommendation, so alternative candidates are not included in the PDF table. The selected charter date is not explicitly included in the summary table; it appears only indirectly in explanation text on this sample.
- `scenario_result`, `decision_twin_result`, `synthetic_validation` and `real_validation` parameters have conditional rendering support. Current Overview and Workbench calls omit them; Twin passes its Twin result but still omits scenario/validation. There is no current Scenario Lab export button. Real validation is printed as “not included” by default; the suggested “Enable” action is misleading because Forecasts has no corresponding enable switch.
- Provenance/disclosures are present: DEMO mode, synthetic metric statement, prototype caveat, FX assumption, professional review. Those disclaimers do not make invented computations factual. YAML assumption registry and sensitivity results are not included.

PDF generation/rendering is WORKING; trustworthy run-specific analytical reporting is **PARTIAL**. No PDF content or source was corrected in this audit.

## 21. Storage / SQLite public API and migration

Database: root `freightiq_workspace.db`, ignored by Git. Tables: shipments, decision_versions, audit_logs. JSON payloads retain original input/recommendation dictionaries alongside selected columns. Import calls `init_db()`.

| Purpose | Public functions |
|---|---|
| Initialization | `init_db`, `initialize_storage` alias |
| Save shipment | `save_shipment(dict, db_path=...)`, `save_shipment_to_db(...)` wrapper |
| Read shipment | `load_shipment`, `load_shipment_from_db` alias |
| List shipments | `list_shipments`, `list_saved_shipments` alias |
| Active context | `get_active_shipment_context`, `set_active_shipment_context`, `update_active_shipment_context` |
| Append audit | `append_audit_log`, `log_audit_event` wrapper |
| Read audit | **`get_audit_trail` exists**, **`get_audit_logs` exists** and delegates |
| Decision save | **`save_decision_version` exists**, **`log_decision_version` exists** and delegates |
| Decision history | `get_decision_versions`, `get_decision_history` alias |

Exact inspected signatures are saved in `measurements.json` under `storage_api`. Audit read supports optional shipment filter and limit, sorts newest first and supplies display defaults. SQLite operational errors are printed and returned as an empty list, potentially resembling “no events”.

Migration: creates missing tables; inspects audit columns; renames legacy `log_id`→`id` if necessary; adds missing expected audit columns. It does not implement general versioned migrations for all historical shipment/decision schemas. Active shipment context is Streamlit session state with defaults; it does not automatically call SQLite load. There is a separate similar context helper in `app/components/helpers.py`.

Decision versions are keyed `shipment_id_vN`. Without explicit `version_number`, N=1; `ON CONFLICT` updates it. Workbench invokes the alias without a version number on every successful render, so it overwrites v1 while appending audit events. This is not immutable automatic version history. Stored columns can default to **18.58 Cr and robustness 82** independently of the actual JSON recommendation. The old positional-signature compatibility branch does not reliably recover a recommendation dict when passed in the version argument slot.

## 22. Integrations: actual connectivity versus labels

| Connector | Current default behavior | Other mode behavior / status |
|---|---|---|
| Freight | DEMO: synthetic CSV rate and indices | LIVE_READY without credentials: NOT_CONFIGURED. Even with endpoint/key, methods still read CSV; genuine CONNECTED retrieval NOT IMPLEMENTED. |
| AIS | DEMO: synthetic availability, fixed Panamax/region metadata | Same limitation; no actual AIS query/position processing. |
| Commodity | DEMO: synthetic coal/ore prices | Same limitation; no commercial price fetch. |
| Port | DEMO: synthetic congestion/waiting, fixed Paradip metadata | Same limitation; no real berth queue retrieval. |
| Weather | Default DEMO: CSV weather/event scores | Explicit PUBLIC_LIVE performs Open-Meteo request; audit probe succeeded in 0.8251 s with weather risk 2.1. Event risk remains fixed 1.5. Failure silently returns CSV fallback with potentially misleading non-DEMO metadata. |
| External validation archive | PUBLIC_REAL cached wind series | Separate from decision feeds; cache/hold-out calculation works; UI chart BROKEN and units mislabeled. |

Fresh manager checks found all five DEMO adapters HEALTHY by their configuration logic; all five LIVE_READY adapters were NOT_CONFIGURED in the audit environment. “HEALTHY” means mode/credentials present, not endpoint reachability. Actual secrets were not printed. UI explicitly instantiates DEMO regardless of environment, and connection rows are static. Public weather is callable, but current main decision pages do not consume it: their forecasts/optimizer use synthetic/default fields.

`.env.example` exists, but no `load_dotenv()` call was found in app/backend. Setting values in a file alone is not verified to configure execution; environment loading must be handled externally. Commercial connector credentials alone would still not implement retrieval.

## 23. FastAPI routes and schemas

Inspected from `backend/main.py` decorators and `backend/schemas.py`, not inferred from tests. All responses below are JSON; declared models include `is_demo_data=True` where present.

| Method / route | Purpose | Request | Response |
|---|---|---|---|
| GET `/health` | App health/title/demo flag | None | `HealthResponse` |
| GET `/market/latest` | Last merged synthetic market row | None | `MarketLatestResponse` with date and eleven market variables |
| POST `/forecast` | Forecast and model comparison | `ForecastRequest`: horizon 1–60 (default14), model_name default Auto | `ForecastResponse`: selected_model, metrics, reason, forecast_records, comparison_table |
| POST `/optimize` | Fixed-route date/vessel search | `OptimizeRequest`: cargo_type, quantity 10k–250k, origin, destination, optional earliest/latest strings, vessel_class, optional demurrage_rate, risk_tolerance | `OptimizeResponse`: success, recommendation, best_option, scenarios |
| POST `/backtest` | Walk-forward simulation | `BacktestRequest`: start/end, horizon7–30, step1–30, cargo, quantity, origin/destination, vessel | `BacktestResponse`: totals, win count/rate, error metrics, period table, disclaimer |
| POST `/scenario` | Apply shock and reoptimize | `ScenarioRequest`: shipment/route/window/vessel/risk plus nested `ScenarioShock` fields in section18 | `ScenarioResponse`: baseline/stress, comparison, status/explanation, sensitivity, thresholds, confidence, alternate ports |
| GET `/control-tower` | Default disruption/stability summary | None | `ControlTowerResponse`: recommendation, signals, alerts, ports/routes, stability/stress, action, log summary |
| POST `/decision-twin` | Monte Carlo cost/regret evaluation | `DecisionTwinRequest` extends OptimizeRequest, simulations_count50–5000 default1000, seed 42, optional shock | `DecisionTwinResponse`: hero, comparisons, waiting, heatmap, thresholds/counterfactuals, Pareto/fan/wins/candidates/disclaimer |
| POST `/data/upload` | CSV validation/preview | Multipart `UploadFile` field `file` | Untyped dict: filename, valid, missing columns, rows, columns, first-five sample records |

FastAPI also exposes standard `/docs`, `/redoc`, `/openapi.json`. No API routes were found for PDF download, shipment CRUD, config editing or external validation. Upload validates/previews only; it does not replace shared data. Decision Twin's inherited date/demurrage fields are not passed into the engine in its route. In several routes, intended HTTP 400 errors are caught by a broad `except Exception` and rethrown as HTTP 500. No authentication/authorization layer appears; CORS permits all origins/methods/headers with credentials. Deployment hardening was not implemented or tested here.

## 24. Compile/test results and coverage

Executed from the verified root:

```
python -m compileall app backend tests
python -m pytest -q
```

Compileall completed successfully with no syntax error. Its independent wall-clock duration was not recorded: **UNVERIFIED**. Pytest exact outcome: **144 passed, 0 failed, 0 skipped, 2 warnings in 51.59 seconds**. Both warnings were statsmodels Maximum Likelihood convergence warnings, in `test_auto_selection_excludes_insufficient_data_from_ranking` and `test_all_insufficient_data_fallback`.

| Test module | Collected / passed cases |
|---|---:|
| `tests/test_api.py` | 5 |
| `tests/test_backtest.py` | 1 |
| `tests/test_config_model.py` | 14 |
| `tests/test_data_loader.py` | 3 |
| `tests/test_decision_twin.py` | 14 |
| `tests/test_demo_mode.py` | 2 |
| `tests/test_disruption_engine.py` | 13 |
| `tests/test_domain_and_productization.py` | 9 |
| `tests/test_forecasting.py` | 9 |
| `tests/test_integrations.py` | 7 |
| `tests/test_no_leakage.py` | 15 |
| `tests/test_optimizer.py` | 3 |
| `tests/test_optimizer_integrity.py` | 15 |
| `tests/test_reporting.py` | 5 |
| `tests/test_scenario_engine.py` | 10 |
| `tests/test_storage.py` | 3 |
| `tests/test_validation.py` | 16 |
| **Total** | **144** |

Total is collected cases, including parametrization, not just function definitions. Sensitivity-related coverage sits mainly in optimizer-integrity/config tests; there is no dedicated test_sensitivity module. Validation tests include fixture/mocked network/cache branches; passing them is not proof of real freight validity. Reporting tests check bytes/contracts, not all assertions in the generated prose. Browser page rendering was separately exercised by this audit, not the repository pytest suite. The Forecasts crash and hardcoded metrics demonstrate that “144 passed” is not equivalent to “all pages correct”.

## 25. Performance and UX findings

All measured browser navigations exceeded approximately three seconds; see page table. Backtesting was slowest at 34.213 s. Charter 13.030 s, Forecasts 15.095 s to failure, Twin 12.089 s. These are single-run end-to-end observations, not statistically robust benchmarks. Initial browser loading also showed empty content below the heading before calculations finished.

Separate function timings on the same current data: forecast14 1.0800 s; forecast30 .2749 s; optimizer .0067 s; assumption sensitivity .1206 s; Twin .0561 s; cached external validation .2303 s; PDF .0555 s; default backtest 18.054 s. Warm imports/process state differ from browser runs. The evidence does **not** support blaming sensitivity alone for the slow Charter page. Browser/Streamlit initialization/render overhead was not separately profiled.

Known causes from code: forecasting is rerun on ordinary widget interactions; all model candidates fit even for manual selection; backtesting repeats those fits over 57 windows and is not cached/gated by its button; tabs execute their bodies including validation; page opening also generates PDFs and, in Workbench, database writes. Processed data is cached, but most expensive outputs are not. Heavy operations are not consistently surrounded by useful progress feedback.

Other UX defects: stale past default laycan relative to actual audit date; decorative navigation that is not clickable; missing Reset; misleading override/upload success wording; white tables on dark backgrounds; low-contrast date input; `undefined` chart titles; currency/score narratives not consistently derived from results.

## 26. Overclaim and misleading-output search

Searched tracked repository text and app/backend/config/docs for the requested terms: AI-powered, accurate, validated, proven, optimal/global optimum, linear programming, LP/MILP, savings, 83%, production-ready, real-time, live and industry-grade. Raw hits are preserved in `all-tracked-claim-search.txt` and `claim-search.txt`. Many matches are disclaimers, enum names, tests or explicit examples of wording to avoid; those are not endorsements. Risky occurrences and their evidence-based interpretation:

| File:line | Exact phrase / short literal | Assessment |
|---|---|---|
| `app/components/helpers.py:305` | `LIVE API` | Always displayed; not a connection probe or proof live data feeds decisions. |
| `app/components/helpers.py:335` | `Ensemble v2.4` | Unsupported: code selects one model, no versioned ensemble. |
| `app/components/helpers.py:277` | `matching commercial SaaS standard` | Internal docstring aspiration, not a demonstrated quality standard. |
| `app/views/control_tower_view.py:57` | `Real-time freight exposure` | No real-time freight feed; synthetic/static state. |
| `app/views/control_tower_view.py:66` | `Unable to refresh live market feeds` | Catch handles ordinary local computation failures too; not evidence of an attempted live fetch. |
| `app/views/control_tower_view.py:129–130` | `82%`; `Stable across 820 / 1,000 simulated futures` | Hardcoded, not current computation. |
| `app/views/control_tower_view.py:174–186` | `Congestion Index: 64/100`; `18 Panamax vessels open`; `₹54,200 / t`; `Normal passage conditions` | Static activity claims; not current market observations. |
| `app/pages/2_Decision_Twin.py:110` | `Stable in 82% of simulated scenarios` | Hardcoded and not definition of the displayed composite score. |
| `app/pages/2_Decision_Twin.py:246–255` | `Tipping Point: 74`; `11 vessels`; `+8.4%` | Fixed UI thresholds, not current backend sweeps. |
| `app/pages/4_Market_Overview.py:110–114` | `Softening (-1.2%)`; `Rising (+3.4%)`; `Bunker VLSFO Singapore` | Fixed trends/bunker quote beside calculated synthetic values. |
| `app/pages/4_Market_Overview.py:120–126` | `Recent market developments`; dated berth/rail/bunker/dredging news | Hardcoded unsourced news, not verified events. |
| `app/pages/5_Forecasting.py:130` | `Quantitative driver impact decomposition` | Fixed invented driver table; models have no exogenous regressors. |
| `app/pages/5_Forecasting.py:143` | `projected to soften moderately` | Static direction, independent of forecast trajectory. |
| `app/pages/5_Forecasting.py:101,143` | `Out-of-sample`; `out-of-sample MAPE` | Qualified synthetic, but naive metric protocol differs from deployed forecast and SARIMA comparison. |
| `app/pages/6_Charter_Optimizer.py:63` | `Commercial procurement solver` | Prototype enumeration/assumed inputs; wording stronger than evidence. |
| `app/pages/6_Charter_Optimizer.py:116` | `Ranked commercial options` | Modeled vessel/date candidates, not executable market offers. |
| `app/pages/9_Data_Integration.py:62` | `Public Live API [P]`; `Connected`; `12m ago` | Static row, not current adapter result. |
| `app/pages/9_Data_Integration.py:84` | `100% Valid` | Assigned literal, not a measured validation rate. |
| `app/pages/9_Data_Integration.py:142` | `every numeric constant` | Eleven registered assumptions do not cover legacy config/heuristics/defaults. |
| `app/pages/9_Data_Integration.py:248` | `within 5% of path-optimal` | Incorrect Twin robustness formula. |
| `app/pages/9_Data_Integration.py:251–252` | `i.i.d. lognormal`; `no serial correlation` | Contradicts Gaussian/AR(1) simulation. |
| `app/pages/9_Data_Integration.py:352` | `SARIMA fit, held-out MAE/RMSE/MAPE` | Valid narrow backend scope; chart/unit bug means a broad green approval is unwarranted. |
| `app/pages/9_Data_Integration.py:368` | `known material limitation ... (none currently)` | Contradicted by current runtime/source findings. |
| `backend/main.py:225` | `real-time Control Tower disruption status` | Computes on synthetic/default state, not a streaming feed. |
| `backend/optimizer.py:297` | `Option A (Optimal)` | Justified only as minimum within the enumerated modeled candidate set. |
| `backend/decision_twin.py:345` | `across 1,000 market simulations` | Synthetic, and hardcodes 1,000 in narrative even when API count differs. |
| `backend/reporting.py:4` | `enterprise-grade PSU PDF decision notes` | Unsupported internal description; fabricated defaults and sparse pagination remain. |
| `backend/reporting.py:404` | `82/100 (Strong)`; `INR 18.0 Lakh` | Fabricated fallback analysis when no Twin is supplied. |
| `backend/reporting.py:451` | `confirms decision stability` | No scenario supplied in default export; unsupported claim. |
| `backend/reporting.py:457` | `~83%`; `~INR 105/tonne` | Hardcoded, stale versus current 43.9%/₹73 backtest. |
| `backend/reporting.py:489` | `MAE ~INR 105/t` | Same stale fallback. |
| `README.md:47,129` | `LIVE_READY`; `unless live adapters are configured` | Credentials do not turn four CSV-only adapters into real retrieval. |
| `DEMO_SCRIPT.md:23,44,55–58` | `approximately 83%`; `about 83%` | Synthetic qualifier is good, numerical claim stale. |
| `DEMO_SCRIPT.md:24,60–63` | `82% ... kept the same ... recommendation` | Both fixed figure and wrong robustness definition. |
| `DEMO_SCRIPT.md:26` | `All metrics are computed on synthetic` | Now incomplete: separate weather validation exists. |
| `DEMO_SCRIPT.md:32–35` | `connected end-to-end`; `every ... model execution is logged`; `swap ... live API feeds` | Overstates scenario integration, audit coverage and adapter completeness. |

The terms LP/global optimum/production-ready in DEMO_SCRIPT's “Instead of saying” column are explicitly discouraged, not current implementation claims. Backend enumeration terminology is materially more accurate after recent commits. Simulated savings variable names and disclaimers are acceptable when their synthetic/model scope is preserved.

## 27. Documentation and scripts

README and DEMO_SCRIPT exist. No standalone walkthrough/technical-documentation/model-card files were found in the inspected tree; model cards are embedded in Data Integration Python. `baseline_optimizer.json` is a recorded optimizer snapshot, not a regression execution or external validation result.

README's basic launch/test commands match entrypoints. Its prototype framing is appropriate. Live-ready wording overstates retrieval, and “100% offline” applies only to core synthetic computation: a missing weather cache can trigger a network request and typography references Google Fonts. Requirements omit explicit PyYAML (imported by config_model), requests (validation), and python-multipart (FastAPI UploadFile setup); packages happen to be available locally, but a clean declared-dependency install/container was **UNVERIFIED**. Unbounded minimum versions also permit behavior differences. Compose has no persistent SQLite volume or explicit shared workspace database between its app/API containers. `.dockerignore` does not exclude workspace databases or `.claude/`/screenshots; local build context may contain them.

DEMO_SCRIPT's 83%/82% explanations are stale and should not be presented as current facts. It overstates scenario propagation and audit completeness. Model cards contain incorrect cost formulas (e.g. congestion × quantity, demurrage without /24/laytime), claim use of domain masters the optimizer does not use, describe the wrong Twin distribution/score, and call the synthetic series stationary despite drift/seasonality. Their existence is a documentation strength; their accuracy is PARTIAL.

## 28. Meaningful change history

Diff/stat and current-source inspection establish these effects; attribution to Claude or a particular AI is **UNVERIFIED**. Git authors identify Jyotiraditya Deb, not which development tool wrote the changes.

- Latest Batch E replaced the generator and regenerated five CSVs using shared latent drivers; updated baseline snapshot and added structural/correlation/determinism tests. Therefore older performance numbers are especially unsafe to reuse.
- Batch D introduced weather archive validation/cache, chart code, provenance result types, UI model cards/status, optional PDF validation arguments and tests. It did not establish freight accuracy; current chart and unit bugs remain.
- Batch C2 added actual one-at-a-time sensitivity and cost-derived winner/alternative explanations. It did not remove older generic recommendation language or fully test the risk-dominant explanation branch.
- Batch C1 moved eleven assumptions to YAML, wired selected constants into optimizer/Twin, and removed PuLP from requirements/import claims. Many other constants remain outside the registry; richer domain masters are still separate.
- Batch B replaced fabricated short-history metric triples with null/INSUFFICIENT_DATA handling and adjusted UI/schema/tests. It did not remove fabricated PDF/Twin/dashboard prose.
- Batch A added explicit synthetic wording/disclosures and DEMO_SCRIPT. It changed framing more broadly than numeric provenance.
- Earlier fixes renamed audit `log_id` to `id`, improved error visibility, registered Vera for PDF header/footer and silenced the Pydantic namespace warning.
- `c901a85` changed shared theme/layout, moved Home/Control Tower into a shared view, added forecast compatibility module and reporting/storage UI compatibility. It created a cleaner visual shell but retained duplicated navigation and static content.

## 29. Remaining risks, ranked by evidence

### CRITICAL

No critical security exploit, data-loss event or total offline-demo failure was established in this audit. **Operational decision reliability is not established**: the system must not be represented as validated commercial charter advice. The following high risks are concrete blockers to that claim.

### HIGH

1. Fabricated/stale analytical figures in default PDF and dashboard/Twin captions, including current contradictions of 83% vs 43.9% and 82 vs 54. An exported decision note can claim computations never run.
2. No real freight validation; backtest is entirely SYNTHETIC and currently underperforms its benchmark. Demo assumptions do not establish contract cost accuracy.
3. Forecasts page crashes with current local versions/cache; automated tests miss it. External validation units are wrong and “observed” terminology overstates reanalysis.
4. Unequal naive/SARIMA evaluation protocols undermine Auto ranking; naive evaluated predictor differs from its forecast.
5. Unsupported destination names silently get fallback costs/feasibility; numeric draft and richer domain restrictions do not drive base optimization. Date range controls have tuple/list mismatch.
6. Scenario settings, manual overrides and uploaded data are not connected across the claimed workflow. Workbench/Overview/Twin can show different shipment assumptions.
7. Twin does not use simulated supply for path feasibility and can insert a capacity-infeasible fallback when no candidate exists. UI tipping points are hardcoded.
8. Adapter/source-health displays can imply live connectivity while returning synthetic rows. Credentials do not implement freight/AIS/commodity/port clients.
9. Risk-dominant optimizer explanation raises KeyError, reproduced. Default tests do not cover all valid parameter regimes.

### MEDIUM

- Decision v1 overwritten on every workbench rerun; audit events accumulate without immutable corresponding versions; default stored score/cost can be fictitious.
- Repeated synchronous fitting and un-gated buttons produce slow page execution, especially Backtesting; no committed browser-render checks.
- Incomplete/contradictory parameter and domain registries, heuristic sensitivity and counterfactuals, uncited cost assumptions.
- Cache never ages out or checks units/location/variable; cache is untracked; fallback model identity can be concealed.
- API lacks auth, has permissive CORS, loose enum/date validation and swallowed intended 400 errors; clean deployment dependency sufficiency is UNVERIFIED.
- Full-series backward fill/median risks leakage for incomplete external data; CSV “quality” shown after imputation can hide original missingness.
- Model-card/README/demo-flow descriptions do not consistently match execution; demo recommendations are in the past relative to 17 September.

### LOW

- Duplicate overview navigation and decorative non-clickable top tabs; sidebar/headings use different names.
- Incomplete dark table/input/chart styling, visible Deploy, `undefined` chart titles.
- Two-page PDF leaves an almost empty second page; important run context/selected date/assumptions are incompletely presented.
- Font dependency on external Google Fonts and broadly unpinned requirements reduce reproducibility.

## 30. Verified strengths

- Clear separation of UI, forecast, optimizer, scenario, simulation, storage, validation and adapter modules makes the calculation paths inspectable.
- Seeded synthetic generator now avoids direct target-derived indices/commodities; structural and deterministic checks exist and pass.
- Base optimizer costs and feasible candidate ordering are explicit, reproducible and auditable; no hidden solver is needed for its small search space.
- Four assumption sweeps genuinely recompute the optimizer and expose stability/flip results, with synthetic scope stated in the UI.
- Monte Carlo costs/regret/fan distributions and Pareto comparisons are computed, despite important feasibility/interpretation limitations.
- Real external weather caching/hold-out evaluation exists separately from synthetic freight evaluation and handles unavailable data without fabricating metrics.
- Insufficient-data metrics now use explicit null/status behavior; synthetic disclaimers appear in major analytical pages.
- SQLite APIs, audit retrieval/migration, PDF byte generation and a broad 144-case test suite are present and runnable.
- Default rendering works for ten pages, and actual cost components, dataframe exports, a theme toggle and readable PDF output are available.

## 31. Judge-safe statements

| Area | SAFE | NOT SAFE |
|---|---|---|
| Forecasting | “We compare univariate time-series models on a synthetic freight series; the current evaluation protocols still need alignment.” | “Our AI accurately predicts live freight markets.” |
| Optimizer | “We enumerate feasible date/vessel candidates for a selected route and rank their assumed logistics costs.” | “LP/MILP guarantees the cheapest real charter or global market optimum.” |
| Decision Twin | “We compute cost and hindsight regret across seeded synthetic futures; the composite score is a model-specific indicator.” | “82% is a calibrated probability that this decision succeeds.” |
| Scenario | “This page applies selected shocks to a synthetic baseline and recomputes modeled costs.” | “The shock automatically updates every page and proves real-world resilience.” |
| Backtesting | “The current synthetic walk-forward run wins 25 of 57 windows and has a negative modeled cost difference.” | “We proved 83% market success.” |
| External validation | “A separate SARIMA hold-out test uses public weather archive data, not freight; we identified a display-unit bug and chart failure.” | “Freight prediction is validated on real maritime market data.” |
| Savings | “Cost differences are hypothetical model outputs, not realized savings.” | “Users will save ₹X or a guaranteed percentage.” |
| Readiness | “This is a runnable decision-support prototype with tested backend components and known UI/data-integration gaps.” | “Industry-grade, production-ready autonomous chartering.” |

Do not read the stale demo script's exact metric claims to judges. Show the data period and distinguish calculated results from remaining placeholders.

## 32. Recommended demo order for this exact state

Use existing sidebar entries. Preload expensive pages if timing matters. Do not conceal the known Forecasts failure or present static activity/tipping-point text as observations.

| Step | Page / exact element | Expected output | Measured page delay | Judge-facing message |
|---|---|---|---:|---|
| 1 | Data Explorer → Dataset / Quality Audit | 974 rows, 35 columns, dates Jan 2024–Aug 2026; processed rows/schema | ~12 s | “This is the synthetic demonstration dataset; cleaning precedes this quality view.” |
| 2 | Data Integration → Decision Parameters | Eleven values/classifications/source notes | ~13 s; tab switches lighter | “These expose selected prototype assumptions, not every domain constant.” |
| 3 | Market Overview → Market Intelligence summary/chart | Synthetic freight/indices, current final-row values | ~13 s | “The chart demonstrates market-context presentation; news/trend text remains illustrative.” |
| 4 | Charter Optimizer → candidate matrix, cost breakdown, why-selected | Panamax Sep 4, ~₹26.09Cr, ranked costs | ~13 s | “Lowest modeled cost among our enumerated candidates under these assumptions.” |
| 5 | Same page → Assumption Sensitivity panel / Detailed perturbation results | Four sweeps, 16/16 held | No separate page; .121 s engine | “The recommendation holds in this limited one-at-a-time sweep on demo inputs.” |
| 6 | Scenario Lab → East Coast Disruption | 12/55/−30 shock controls, High weather, ~₹29.31Cr, +12.4% | ~7 s baseline; preset reruns | “The modeled cost rises. Date/vessel can stay unchanged despite the ALTERED label.” |
| 7 | Decision Twin → Decision Surface / Simulated Freight Futures | 1,000 paths, ~₹25.94Cr, 54/100, ~₹102.5Lakh regret | ~12 s | “These are assumed futures and a composite robustness score; ignore the stale 82% caption and fixed tipping cards.” |
| 8 | Backtesting → current metrics / outcomes | 43.9%, 25/57, −₹5.15Cr | ~34 s | “This synthetic test currently loses on aggregate; it is diagnostic, not savings evidence.” |
| 9 | Data Integration → Model Status / Audit Trail | External cache status, audit entries | ~13 s | “Weather-only external evaluation exists; displayed m/s should be km/h. Logs cover implemented actions.” |
| 10 | Optional Workbench → Download Procurement Report | Two-page PDF | .056 s generation, already eager | “Export mechanics work; this version has stale analytical fallback text and is not an authoritative decision note.” |

Forecasts is **not a clean demo step** until the known rendering defect is separately fixed: if shown, explain that the synthetic chart/metrics load before the external-chart exception. Overview/Control Tower can serve as an optional opening view, but avoid repeating both or claiming their hardcoded 82%/activity as computed observations. Do not claim cross-page shock propagation, working manual overrides or dataset replacement.

---

# FREIGHTIQ — CURRENT STATE HANDOFF

## 1. One-paragraph product summary

FreightIQ is a Python/Streamlit maritime bulk-procurement decision-support prototype for India-bound cargo. It combines synthetic freight time-series forecasts, explicit date/vessel candidate costs, scenario shocks, Monte Carlo cost/regret simulations, synthetic walk-forward backtesting, SQLite persistence and ReportLab exports. Core calculations run and 144 tests pass, but UI/PDF placeholders, disconnected controls, uneven evaluation methods and a Forecasts render failure prevent treating it as an operational or real-market-validated product.

## 2. Current architecture

Streamlit calls backend modules directly; FastAPI exposes nine parallel application endpoints. Main entrypoint `app/Home.py`. `backend/config.py` legacy dictionaries drive optimization; richer `backend/domain/` masters are mostly separate. Eleven assumptions load from YAML at import. Data is merged from five CSVs, then feature-engineered; forecasting remains univariate.

## 3. Current page map

Eleven pages: Home `/`, Control Tower `/Control_Tower`, Decision Twin `/Decision_Twin`, Operations Overview `/Operations_Overview`, Market Overview `/Market_Overview`, Forecasting `/Forecasting`, Charter Optimizer `/Charter_Optimizer`, Scenario Lab `/Scenario_Lab`, Backtesting `/Backtesting`, Data Integration `/Data_Integration`, Data Explorer `/Data_Explorer`. Home and Control Tower share a renderer. Ten default pages PASS; Forecasting FAILS in external validation chart.

## 4. Data modes and sources

Main market/port/vessel/commodity/event inputs are SYNTHETIC, 974 rows, 2024-01-01–2026-08-31, seed 42. Direct generator target leakage removed through latent factors. Public weather archive cache is external PUBLIC_REAL in application vocabulary; public current-weather adapter can fetch Open-Meteo. No commercial freight/AIS/port/commodity retrieval is implemented. Several provenance vocabularies coexist.

## 5. Forecasting status

Naive and SARIMA work; Prophet optional/not installed. Auto picks lowest non-null MAE, but naive one-step evaluation and SARIMA horizon hold-out are not comparable. Current 14-day selected naive MAE .634 USD/t; 30-day selected SARIMA .519 USD/t, both SYNTHETIC. Insufficient metric history gives nulls/status; empty-series safety and fallback labeling remain incomplete. Driver decomposition is static.

## 6. Optimizer status

Exhaustive date × vessel enumeration for fixed route, not LP/MILP/PuLP. Total = freight + scaled demurrage + congestion + weather/event risk. Workbench default recommends Panamax September 4, USD 3,105,810 (₹26.09Cr). Missing operational columns use constants. Date-range handling, unknown-port fallbacks, missing numerical draft checks, false earliest-date narrative and risk-dominant KeyError remain.

## 7. Decision Twin status

Computed 1,000 seeded synthetic futures; default recommendation Panamax/Paradip September 1, ₹25.94Cr, robustness 54/100, regret ₹102.5Lakh. Score is weighted win/CV/cost-gap/regret, not a probability. Simulated vessel supply is unused in feasibility/costs. Counterfactual heuristics and UI thresholds/82% captions are not reliable computed guidance.

## 8. Scenario status

Backend freight/congestion/supply/weather/event/demurrage perturbation exists; commodity shock has no implemented cost effect. East Coast preset was verified. UI shipment values are fixed; geopolitics state is ignored; no Reset; scenario state does not feed Workbench/Twin/Overview. Cost-only change can be described as a changed charter decision.

## 9. Backtesting status

SYNTHETIC walk-forward against immediate charter. Current UI-default run: 57 windows, 25 wins, 43.9%,−USD612,577.50/−₹5.15Cr,−0.40%; MAE .874, RMSE 1.112, MAPE 2.87%. No real-market savings or performance evidence.

## 10. Validation status

External wind-speed hold-out: 731 rows, 701 train/30 test, 2024-09-12–2026-09-12; MAE 4.194,RMSE 4.867,MAPE 25%. Actual units km/h, incorrectly labeled m/s. Public archive is reanalysis rather than direct port measurements. This is non-freight validation using similar statistical machinery. Chart fails at Plotly add_vline with pandas Timestamp.

## 11. Parameter/provenance status

Eleven YAML entries: six demo-only/five configured assumptions; ten marked future-editable, UI read-only. Other decision constants remain in config/Twin/scenario/UI. Source labels and live/freshness status are inconsistent and partly fabricated. No empirical/literature calibration established.

## 12. Sensitivity status

Four actual one-at-a-time coefficient sweeps at ±15/±30%, 21 optimizer calls, 16 counted perturbations. Default Panamax/Sep 4 holds 16/16; .121s engine. No flip in this grid; no joint or real-market robustness validation.

## 13. PDF/reporting status

Fresh two-page report generated/reopened/rendered; INR amounts and page numbers legible, sparse second page. Default export invents Twin/scenario analysis and repeats stale 83%/INR105 metrics. Optional real/scenario inputs exist but current page wiring omits them. Treat PDF mechanics as working and analytical reliability as PARTIAL.

## 14. Storage/audit status

SQLite shipment and audit APIs work; all requested aliases exist. Migration handles audit log_id→id and missing audit columns. Active session context does not restore automatically from DB. Workbench overwrites default v1 each rerun, creates audit entries and can store placeholder score/INR columns. Not immutable decision history.

## 15. Integrations

Four commercial adapters remain CSV-only regardless of credentials. Current DEMO health is not endpoint health. Explicit PUBLIC_LIVE weather succeeded, but main decision pages do not use it. Manual override only appends a log; upload only validates/previews. Static connection/freshness panels must not be treated as monitoring.

## 16. UI/theme status

Custom logo, CSS cards, blue accents and light/dark session toggle. Dark persists through sidebar navigation; shared charts adapt. Native tables remain light, some inputs have poor contrast and Twin/validation charts use hardcoded white. Decorative top bar is not clickable, Deploy remains visible, some plots show undefined. Overall a styled hackathon dashboard, not near-commercial.

## 17. Test status

Compileall successful. Pytest: 144 passed/0 failed/0 skipped/2 statsmodels convergence warnings in 51.59 s. Seventeen test modules; no committed page-render suite. Separate fresh browser audit: 10 PASS/1 FAIL/0 BLANK. Passing backend tests do not cover all semantic/UI failures.

## 18. Current runtime/performance issues

Measured navigation: Charter 13.03 s, Forecasts 15.10 s to exception, Twin 12.09 s, Backtesting 34.21 s; other pages 7.36–13.93s. Individual sensitivity/PDF/Twin functions are fast. Repeated synchronous forecasting/backtesting and browser/Streamlit overhead contribute; no detailed profile. Buttons generally do not gate calculations.

## 19. Current credibility limitations

No real freight validation, no realized savings, assumed cost weights/distributions, unequal model evaluation, fixed claims beside computed numbers, partly disconnected workflow, unsupported destination fallbacks and incomplete provenance. Old 83%/82% talking points and model-card formulas are not current facts.

## 20. Judge-safe claims

“We demonstrate a transparent synthetic freight decision workflow.” “We rank the lowest modeled cost in an enumerated candidate set.” “We compute synthetic scenario and Monte Carlo cost/regret outputs.” “We separately test statistical forecasting on public weather data, not real freight.” “Our current synthetic backtest does not establish savings.” Avoid market accuracy, calibrated success probabilities, LP/global market optimum, automatic live integration or production-readiness claims.

## 21. Remaining work

No fixes were performed. Priorities for a separately authorized implementation: remove fabricated run results; repair Forecasts/units; align forecast evaluation; wire actual shipment/scenario/dataset/override inputs; correct route/draft/date handling and explanation failures; enforce Twin feasibility; reconcile registries/model cards/docs; make persistence/versioning deliberate; add browser/edge-case tests; profile/cache expensive reruns; implement and validate licensed real-data ingestion before operational claims.

## 22. Exact current git HEAD

`edb25dd1beca6e3e4e1bdec3547dfbfbe2ff5122` on `main`, repository `C:\Users\jyoti\OneDrive\Desktop\FreightIQ`. Tracked source remained unchanged throughout this audit. Initial untracked `.claude/`, `data/validation/`, `screenshots/` remain; `test_report.pdf` also exists at final inspection with unverified creating process. Audit evidence and this handoff are outside the repository.
