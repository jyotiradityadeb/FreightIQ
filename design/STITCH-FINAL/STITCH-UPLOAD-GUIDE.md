# FreightIQ — curated Google Stitch upload guide

## What to upload

Extract `FreightIQ-STITCH-FINAL.zip`. Upload the **15 PNG files in `screenshots/` in numerical order (01–15)**. Supply `STITCH-FEATURE-SUMMARY.md` as accompanying context (attach it where supported, or paste its text). This guide explains image selection and preservation requirements. The archive contains only these 15 images and these two Markdown documents.

Start with 01–11 to establish all page layouts, then add 12–15 for the four distinct tab references. If uploading in batches, keep them in the same redesign conversation and retain numerical order. These are suggested workflow steps, not a claim about a specific Stitch attachment limit.

## Selection and fidelity

All images are from the existing verified 24 October 2026 captures under `design/stitch-reference/screenshots/desktop-1920/`. No new captures were needed. Original references remain untouched.

Every image retains its original **1920-pixel width, height, aspect ratio and exact decoded pixels**. Full-page captures are deliberately used where 1920×1080 cuts off analytical content; no image is shrunk, stretched, cropped, recolored or reconstructed. Open long captures at 100% and scroll to read small labels. Native scrollable tables still show representative rows/columns, not their entire underlying datasets.

Light mode was selected after reviewing dark references: dark mode has pale download-button labels, low-contrast chart legends/axes and inconsistent white chart/table panels. Preserve theme switching in the redesign, but do not reproduce those contrast defects. Lossless PNG compression preserves small type and chart lines; JPG is unnecessary for this compact package and would introduce edge artifacts.

Overview and Control Tower are inherently similar because they share the same implementation. Both are included solely to satisfy coverage of all 11 actual page entries. The four extras show different analytical/governance/upload tabs rather than repeated default views. Mobile/tablet captures, empty Dataset state, menus, intermediate states and redundant variants are excluded.

## Suggested redesign prompt

> Redesign FreightIQ as a coherent, readable maritime procurement decision-support interface. Treat these 15 images as verified current-state references and the feature summary as the complete functional inventory. Preserve all 11 page destinations, all 13 tabs, shipment/route context, calculation controls, chart and table interactions, PDF/CSV exports, scenario comparison, sensitivity evidence, audit notes and provenance. Improve navigation, spacing, hierarchy, form consistency and light/dark accessibility. Keep synthetic demo outputs distinct from observed weather validation and illustrative text. Do not invent live vessel tracking, maritime maps, booking or working API-connection controls. Correct presentation defects rather than copying them. Do not silently omit features that are documented but not separately pictured.

## Upload order and preservation checklist

The table below uses actual page headings; navigation aliases and all unpictured tabs are mapped in the feature summary. Source names identify the exact original capture for traceability.

| Order / file | Page or tab | Pixels | What to preserve |
|---|---|---|---|
| 01 — [01-overview.png](screenshots/01-overview.png) | Overview / Home | 1920×2028 | Full command view: shipment, modeled cost/date/robustness, history, forecast, activity and recommendation/scenario/PDF actions. |
| 02 — [02-control-tower.png](screenshots/02-control-tower.png) | Control Tower | 1920×2028 | Separate page heading and navigation entry; preserve its shared command-view functionality and navigation mapping. |
| 03 — [03-decision-twin.png](screenshots/03-decision-twin.png) | Decision Twin | 1920×2138 | Shipment sidebar, robustness/regret, decision heatmap, simulated futures envelope, counterfactuals and PDF export. |
| 04 — [04-operations-overview.png](screenshots/04-operations-overview.png) | Operations Overview | 1920×1717 | Four operational KPIs, forecast interval, charter recommendation, costs and decision drivers. |
| 05 — [05-market-intelligence.png](screenshots/05-market-intelligence.png) | Market Intelligence | 1920×1835 | Active-route snapshot, benchmark/commodity KPIs, date filter, history/moving average, signal table and illustrative news. |
| 06 — [06-forecasts.png](screenshots/06-forecasts.png) | Forecasts | 1920×2569 | Route/model/horizon controls, forecast interval, comparison expander, model metrics and separate observed-weather validation. |
| 07 — [07-charter-workbench.png](screenshots/07-charter-workbench.png) | Charter Workbench | 1920×3503 | In-period laycan, procurement inputs, ranked candidates, route arrow, recommendation/costs, alternatives, sensitivity and PDF. |
| 08 — [08-scenario-lab.png](screenshots/08-scenario-lab.png) | Scenario Lab | 1920×1747 | East Coast Disruption applied: presets, editable shocks, weather/port, impact preview, explanation and populated comparison. |
| 09 — [09-simulation-backtest.png](screenshots/09-simulation-backtest.png) | Simulation Backtest | 1920×2236 | Completed run: route/date/horizon/interval controls, performance metrics, comparison bars, cumulative curve and outcomes. |
| 10 — [10-data-and-integrations.png](screenshots/10-data-and-integrations.png) | Data & Integrations / Connections | 1920×1080 | All eight tab labels plus complete five-source status table. Preserve source/type/status/freshness and informational action cells. |
| 11 — [11-data-explorer.png](screenshots/11-data-explorer.png) | Data Explorer / Route Freight Series | 1920×1928 | All five tab labels, dataset KPIs, route filter, route/processed tables and both CSV exports. |
| 12 — [12-data-and-integrations-decision-parameters.png](screenshots/12-data-and-integrations-decision-parameters.png) | Data & Integrations / Decision Parameters | 1920×1207 | Read-only parameter values, units, classifications, ranges and provenance; expandable legend and table overflow. |
| 13 — [13-data-and-integrations-model-status.png](screenshots/13-data-and-integrations-model-status.png) | Data & Integrations / Model Status | 1920×1415 | Trust table, scoped validation/limitations, status interpretation and public-weather validation/cache status. |
| 14 — [14-data-explorer-correlation-matrix.png](screenshots/14-data-explorer-correlation-matrix.png) | Data Explorer / Correlation Matrix | 1920×1080 | Readable coefficient heatmap, axes and color scale; preserve interactive inspection. |
| 15 — [15-data-explorer-validate-and-preview-dataset.png](screenshots/15-data-explorer-validate-and-preview-dataset.png) | Data Explorer / Validate & Preview Dataset | 1920×1495 | Completed 12-row upload validation with file control, success feedback and preview table; preview does not replace active data. |

## Original capture mapping

All source paths below are relative to `design/stitch-reference/screenshots/desktop-1920/` in the original project; unused originals are intentionally not in the ZIP.

1. `01-overview--default--full.png` → `01-overview.png`
2. `02-control-tower--default--full.png` → `02-control-tower.png`
3. `03-decision-twin--default--full.png` → `03-decision-twin.png`
4. `04-operations--default--full.png` → `04-operations-overview.png`
5. `05-market-intelligence--default--full.png` → `05-market-intelligence.png`
6. `06-forecasting--default--full.png` → `06-forecasts.png`
7. `07-charter-optimizer--demo-laycan-2026-09-01-to-15--full.png` → `07-charter-workbench.png`
8. `08-scenario-lab--east-coast-disruption--full.png` → `08-scenario-lab.png`
9. `09-backtesting--default--full.png` → `09-simulation-backtest.png`
10. `10-data-integrations--default--viewport.png` → `10-data-and-integrations.png`
11. `11-data-explorer--default--full.png` → `11-data-explorer.png`
12. `10-data-integrations--tab-decision-parameters--full.png` → `12-data-and-integrations-decision-parameters.png`
13. `10-data-integrations--tab-model-status--full.png` → `13-data-and-integrations-model-status.png`
14. `11-data-explorer--tab-correlation-matrix--viewport.png` → `14-data-explorer-correlation-matrix.png`
15. `11-data-explorer--upload-valid-demo-preview--full.png` → `15-data-explorer-validate-and-preview-dataset.png`

## Package verification

- Exactly 15 images, all 1920 pixels wide; 11 page representatives and four additional tab references.
- All 13 tabs documented in the feature summary.
- Lossless pixel-for-pixel equality and original dimensions checked for every selected image.
- All 306 original screenshots retained with unchanged SHA-256 hashes.
- No application files changed during this curation.
- No new captures, compositing, cropping, color changes or synthetic screens.
