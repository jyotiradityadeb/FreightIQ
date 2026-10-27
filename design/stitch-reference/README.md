# FreightIQ — Stitch reference package

**306 actual UI screenshots covering all 11 pages and all 13 tabs.** Captured on 24 October 2026 from commit `0e1d2e87f6fa43c3c47e34d651323e9fd013860d`. Application source is unchanged.

## Start here

1. Open [the visual gallery](gallery.html) to browse and filter screenshots.
2. Give Stitch [STITCH_CONTEXT.md](STITCH_CONTEXT.md) alongside the selected screenshots.
3. Use [FEATURE_INVENTORY.md](FEATURE_INVENTORY.md) as the functionality-preservation checklist.
4. Read [DESIGN_AUDIT.md](DESIGN_AUDIT.md) for specific redesign recommendations and existing defects.
5. Use [SCREENSHOT_INDEX.md](SCREENSHOT_INDEX.md) for every filename, state and pixel dimension. [VERIFICATION.md](VERIFICATION.md) records coverage, capture methods and limitations.

## Files

| Location | Contents |
|---|---|
| `screenshots/desktop-1920/` | 125 primary desktop images: initial viewports, complete pages, tabs, expanded and interaction states |
| `screenshots/desktop-1440/` | 64 secondary desktop images: every page/tab plus selected key states |
| `screenshots/components/` | 109 readable chart/table detail captures, including rightmost columns and last rows of overflowing tables |
| `screenshots/responsive/` | 8 images: viewport/full-page pairs for Overview, Forecasts, Charter Workbench and Data & Integrations at 768 px width |
| `evidence/` | Runtime UI text, page/state manifest, source hash baseline, PNG integrity checks, contact sheets and five actual downloads |
| `tools/` | Playwright capture and package-generation scripts used for this task |

Viewport files are exactly **1920×1080**, **1440×900**, or **768×1024**. Full-page images have the same width and the height needed for the full content. Component images use their actual element dimensions. Dark mode is included for Overview, Decision Twin, Forecasts and Data Explorer.

## Captured pages

| Page | Primary complete-page reference |
|---|---|
| Overview / Home | [Overview](screenshots/desktop-1920/01-overview--default--full.png) |
| Control Tower | [Control Tower](screenshots/desktop-1920/02-control-tower--default--full.png) |
| Decision Twin | [Decision Twin](screenshots/desktop-1920/03-decision-twin--default--full.png) |
| Operations Overview | [Operations](screenshots/desktop-1920/04-operations--default--full.png) |
| Market Intelligence | [Markets](screenshots/desktop-1920/05-market-intelligence--default--full.png) |
| Forecasts | [Forecasts](screenshots/desktop-1920/06-forecasting--default--full.png) |
| Charter Workbench | [Chartering](screenshots/desktop-1920/07-charter-optimizer--default--full.png) |
| Scenario Lab | [Scenarios](screenshots/desktop-1920/08-scenario-lab--default--full.png) |
| Simulation Backtest | [Backtesting](screenshots/desktop-1920/09-backtesting--default--full.png) |
| Data & Integrations | [Data](screenshots/desktop-1920/10-data-integrations--default--full.png) |
| Data Explorer | [Explorer](screenshots/desktop-1920/11-data-explorer--default--full.png) |

## Important secondary states

- Every Integration and Explorer tab, all four model-card expanders and the parameter classification legend.
- Charter alternatives, sensitivity details, demo-period laycan, calendar/cargo menus, Brazil–Gangavaram with 150,000 t, unsupported Mumbai route and infeasible 250,000 t cargo.
- SARIMA and Naive model states, 30-day horizon, three-route comparison and alternate Brazil route.
- All six scenario presets, reset, and an active East Coast scenario carried into Decision Twin.
- Route-series filtering, valid CSV preview, missing-column warning, manual note confirmation and the resulting local audit log.
- A shorter-period backtest, market date-range controls, dark themes and optional responsive references.
- Three PDF and two CSV downloads, produced by the app's actual controls, under `evidence/downloads/`.

## Interpreting the reference

This is the existing interface, including its defects. Do not reproduce the literal “undefined” chart titles, tiny/wrapped navigation, dark-mode contrast failures, silent date fallback, empty Dataset tab or misleading fixed market text as desired behavior. The screenshots are not altered to hide those issues. No real commercial integrations were activated. No interactive map or standalone Settings/Weather/Reports page exists.

No page is inaccessible. The empty Dataset tab is a verified implementation issue: its table/export currently appear under Route Freight Series. Virtualized dropdown automation initially needed retries; those were resolved, and the intended states are included.

## Reproduction

Use the same tracked source revision and installed application dependencies. Run a separate copy containing the bundled synthetic CSVs and, if available, the existing public weather validation cache. Do not copy credentials or a private workspace database. Start in DEMO mode:

```powershell
$env:DATA_MODE='DEMO'
$env:SIH_DEMO_MODE='true'
python -m streamlit run app/Home.py --server.port 8518 --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
```

The capture scripts use Python Playwright with headless Microsoft Edge and Pillow, device scale factor 1, `en-US` locale and `Asia/Kolkata` browser timezone. From the original package workspace, run `tools/capture_reference.py`, then `tools/capture_interactions.py`, `tools/capture_supplement.py`, and `tools/build_package.py` sequentially. The supplement resolves virtualized dropdown selections and explicitly confirms the Decision Twin dark theme. Capture default sessions separately; preserve session state within scenario/navigation workflows. Current-date defaults can change; the named historical laycan capture explicitly uses 2026-09-01 through 2026-09-15.

The temporary runtime database belonged only to the isolated copy. It is not included in this package. No redesign, refactor, model adjustment, production change or GitHub push was performed.
