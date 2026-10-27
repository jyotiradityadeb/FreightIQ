# Stitch interface architecture

The app now has a dedicated browser interface in `web/index.html`, `web/styles.css` and `web/app.js`. A plain JavaScript module was chosen because the Stitch export is static HTML with Tailwind CDN, not React components, and the existing repository had no React build. This keeps exported typography, shell and tokens easy to reproduce without introducing a second frontend framework. The original Streamlit app remains runnable for regression comparison.

The browser handles navigation, form state, rendering and interactive tables/charts. Graphs use a locally bundled Plotly.js 3.4.0 asset from the installed Plotly Python package, with its license included in `web/vendor/`. This restores hover inspection, zoom, pan, reset, range selection and PNG export without an external chart CDN. It does **not** implement forecast, optimization, simulation, scenario or backtest formulas. All results are requested from FastAPI and computed by the existing Python modules. `backend/web_api.py` exposes the existing business functions. `backend/stitch_api.py` adds only presentation-oriented pagination, CSV/quality views, audit notes and decision persistence. SQLite remains the decision/audit store; `FREIGHTIQ_DB_PATH` optionally redirects it for isolated testing.

```text
web/app.js + web/styles.css
        │ HTTP /api/*
        ▼
local Node proxy or Netlify function
        │
        ▼
FastAPI backend.main
  ├─ web_api → existing forecasting, optimizer, scenario, twin, backtest, report
  └─ stitch_api → explorer, source status, audit, upload preview, save result
        │
        ▼
existing data files and SQLite storage
```

Local development uses `scripts/serve-web.mjs` on port 3000 and Python FastAPI on port 8000. `npm run build` packages the static frontend into `dist/`. Netlify can host the static frontend and proxy `/api/*` to a separately hosted Python service through `FREIGHTIQ_API_URL`. A static Netlify deployment alone cannot run the Python calculations. The proxy accepts only known endpoints and methods. The frontend API errors identify unavailable services. Upload is preview/validation only and limited to 2 MB. A manual override note is audit-only and does not silently change model inputs.

Shared client state tracks active route, cargo, quantity, model, date constraints, shocks, tabs, cached read-only responses and recent result panels. Server calculations are rerun on explicit action. Solve persists the returned Python recommendation and decision version. PDF requests call the existing Python report generator. CSV download streams the existing datasets. No model logic is duplicated in JavaScript.
