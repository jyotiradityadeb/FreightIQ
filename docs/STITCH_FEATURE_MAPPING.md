# Feature mapping

| Screen / tabs | Working source and action |
| --- | --- |
| Overview | Python route data, forecast, optimizer and Decision Twin summary; links to workbench, scenario and PDF |
| Control Tower | Same active shipment intelligence in the exported command-center shell; route history and forecast |
| Operations Overview | Fixed demo case from Python route data, forecast and charter recommendation |
| Market Intelligence | Route history, latest market summary and date-window filter; synthetic provenance shown |
| Forecasts | Route/model/horizon selectors, selected Python model, metrics, interactive confidence band, three-route overlay and cached weather method status |
| Decision Twin | Python Monte Carlo results, heatmap, risk/cost views, editable shipment inputs, rerun and report |
| Charter Workbench | Cargo, quantity, origin/destination, laycan and vessel controls; Python solve, candidate ranking, sensitivity, saved decision version and PDF |
| Scenario Lab | Six presets and individual shocks; Python baseline/stressed comparison and reset |
| Simulation Backtest | Date range, horizon and interval; Python walk-forward engine, interactive cost bars and cumulative curve, signed outcomes and period table |
| Data & Integrations: Connections | Existing adapter status and provenance; no simulated connection button |
| Data & Integrations: Data Quality | Existing Python signal matrix, freshness and mode |
| Data & Integrations: Overrides | Local audit note only; explicit non-effect on model inputs |
| Data & Integrations: Audit Trail | SQLite decision/note history and refresh |
| Data & Integrations: Model & Data Limitations | Synthetic-data and validation limits |
| Data & Integrations: Decision Parameters | Existing Python parameter registry and provenance |
| Data & Integrations: Model Cards | Purpose and limitations of the four engines |
| Data & Integrations: Model Status | Scoped trust panel and cached public weather status |
| Data Explorer: Route Freight Series | Paginated canonical route table, filter and full CSV |
| Data Explorer: Dataset | Paginated processed modeling data and full CSV |
| Data Explorer: Correlation Matrix | Python-generated Pearson correlation table |
| Data Explorer: Quality Audit | Column-level missingness and types |
| Data Explorer: Validate & Preview Dataset | CSV schema check and preview; does not replace model data |

The original 11-page Streamlit application remains accessible with `streamlit run app/Home.py`. The new interface contains the same 11 navigation destinations and the requested eight Integration plus five Explorer tabs. All monetary displays are labeled and derived from the existing USD outputs using the original app's ₹84/USD display conversion. Synthetic market data, limited connector status and simulated outcomes remain explicitly labeled.
