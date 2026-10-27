# Functional verification

Checks performed against the dedicated frontend and the existing Python service:

| Check | Result |
| --- | --- |
| `python -m pytest -q` | 184 passed; 10 statsmodels convergence warnings on synthetic forecasting fixtures |
| `npm test` | 3 proxy allowlist/method/configuration tests passed |
| `npm run build` | Static bundle created in `dist/` |
| Browser navigation | All 11 pages loaded without page errors |
| Tab navigation | All eight Data & Integrations and all five Data Explorer tab states loaded |
| Forecast interaction | Changed horizon and reran the Python forecast |
| Charter solve | Python result saved in isolated SQLite test DB; candidate CSV and filter exercised |
| Scenario | Applied Freight Rate Spike preset, adjusted shock slider and ran Python scenario engine; recommendation date/vessel displayed |
| Operator note | Created audit-only note in isolated SQLite DB |
| Explorer upload | Preview/schema validation exercised with a temporary CSV |
| Backtest | Short-period Python walk-forward run produced outcome matrix |
| Charts/tables | Plotly hover, zoom, pan, reset, PNG download, three-route overlay, market date filter, Decision Twin and correlation heatmaps, backtest bars/curve; column sort and full-screen table exercised in browser |
| Downloads | Route CSV (2,084,117 bytes), modeling CSV (344,134 bytes), Python PDF (24,766 bytes, `%PDF` header) returned HTTP 200 |
| Responsive | 1440, 768 and 390 px screenshot captures generated |

The browser workflow uses `scripts/verify-stitch-functions.py` against ports 3001/8001 and an isolated database set by `FREIGHTIQ_DB_PATH`. `scripts/verify-interactive-graphs.py` exercises every chart type on the running local app, including graph controls and dynamic graph updates. The visual capture uses `scripts/verify-stitch-visuals.py` against the app on port 3000 by default; `FREIGHTIQ_VISUAL_URL` can select another URL. These are manual verification scripts because they start from running services. The standard Python and Node test suites do not require those services. The existing Streamlit app was preserved; the new app uses the same Python calculations through FastAPI. A fixed demo-case backtest request now uses Panamax as required by the existing backtest engine.
