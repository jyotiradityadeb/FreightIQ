# FreightIQ — final verification

Verified on 24 October 2026 (Asia/Kolkata).

Source HEAD: `0e1d2e87f6fa43c3c47e34d651323e9fd013860d`. All 97 tracked source files match their pre-capture SHA-256 hashes. No tracked file was modified; only the new design reference package was added to the repository working directory.

## Coverage

| Reachable page | Render result | Initial render seconds | Desktop viewport + full page | Tabs |
|---|---|---:|---|---|
| 01-overview / | RENDERED | 6.22 | 1920 and 1440 | 0 |
| 02-control-tower /Control_Tower | RENDERED | 7.08 | 1920 and 1440 | 0 |
| 03-decision-twin /Decision_Twin | RENDERED | 6.47 | 1920 and 1440 | 0 |
| 04-operations /Operations_Overview | RENDERED | 7.14 | 1920 and 1440 | 0 |
| 05-market-intelligence /Market_Overview | RENDERED | 7.03 | 1920 and 1440 | 0 |
| 06-forecasting /Forecasting | RENDERED | 8.38 | 1920 and 1440 | 0 |
| 07-charter-optimizer /Charter_Optimizer | RENDERED | 6.41 | 1920 and 1440 | 0 |
| 08-scenario-lab /Scenario_Lab | RENDERED | 6.08 | 1920 and 1440 | 0 |
| 09-backtesting /Backtesting | RENDERED | 22.56 | 1920 and 1440 | 0 |
| 10-data-integrations /Data_Integration | RENDERED | 6.89 | 1920 and 1440 | 8 |
| 11-data-explorer /Data_Explorer | RENDERED | 6.53 | 1920 and 1440 | 5 |

All eleven pages rendered to the application footer. All eight Integration tabs and five Explorer tabs were visited and captured at both desktop widths. All visible normal-state expanders were opened, including four model cards, classification legend, route comparison, three charter alternatives and detailed perturbations. No nested tab group was found. Conditional debug-error expanders were not manufactured.

## Image integrity

- 306 indexed UI PNGs decoded successfully and had nonblank pixel variation.
- Viewport filenames have exact 1920×1080, 1440×900 or 768×1024 dimensions, at device scale factor 1. Full-page widths match their desktop class; content height varies.
- Full pages were captured by increasing viewport height to fit Streamlit’s scrolling main container. Images were not stitched or retouched.
- Component images are real chart/table element screenshots. Table rightmost-column/last-row views supplement naturally clipped scrollable tables. No attempt was made to show all thousands of data rows simultaneously.
- Visual review included the eleven-page contact sheet, tab/expander contact sheets, full Forecasts and Overview screens, detailed parameter table, infeasible shipment, route-comparison chart, dark Twin and narrow Overview.
- All screenshot paths are indexed in SCREENSHOT_INDEX.md. SHA-256, dimensions and decode results are in evidence/integrity-check.json.

## Interaction verification

- Captured all six scenario presets and reset; confirmed East Coast Disruption values (12% freight, 55% congestion, -30% supply, High weather) and the active-scenario banner after navigating to Decision Twin.
- Captured SARIMA/Naive 30-day forecasts, three explicit route overlays, alternate-route forecasting, route filtering, and short-period backtesting.
- Entered a supported historical laycan through the actual date field; captured successful chartering, unsupported route and capacity-infeasible outputs.
- Captured valid synthetic CSV upload success and missing-column warning. Upload preview did not replace the dataset.
- Recorded a synthetic manual note only in the isolated database and captured the resulting audit view.
- Verified Overview navigation actions and actual PDF/CSV download events.
- Confirmed dark theme via the Light Mode toggle label and CSS state before the corrected Decision Twin capture. Other dark-state text evidence records Dark Mode.

## Download checks

| Actual UI download | Bytes |
|---|---:|
| FreightIQ_Charter_Decision_2026-10-24.pdf | 24771 |
| FreightIQ_Decision_Report_2026-10-24.pdf | 25722 |
| FreightIQ_Decision_Twin_Report_2026-10-24.pdf | 25722 |
| FreightIQ_route_freight_rates.csv | 2084117 |
| FreightIQ_modelling_dataset.csv | 344134 |

Download success confirms file delivery, not correctness of every narrative or metric in the PDFs. Existing report limitations remain documented.

## Privacy and isolation

- No original workspace database, credentials, `.env` secrets, browser account profile, or private audit history was copied into the runtime.
- The capture used a fresh headless browser profile, synthetic market files, a cached public weather series and a temporary SQLite database.
- Screenshots contain demonstration shipment identifiers and demo notes only. No credential entry, production connection or external publication was performed.
- Screenshot review and extracted-text scanning found no credential/token/password values. Model/connector status labels are documented as application display states, not independent live-connectivity verification.

## Existing issues retained, not capture blockers

- Literal “undefined” chart titles appear in the real browser.
- Top navigation breaks words over multiple lines at 1440 px and into narrow columns at 768 px.
- The Dataset tab is empty; its table/export is under Route Freight Series.
- Dark mode leaves white chart/table/export surfaces and low-contrast input text.
- Charter defaults outside the forecast period silently fall back to September candidates. Historical demo-period and unsupported/infeasible states are captured separately.
- Decision Twin heatmap date labels show unintended date interpretation/overlap in the browser.
- Static market/activity text, cache/live-label ambiguity and inconsistent shared-versus-route data remain in the implementation.

## Remaining blockers

**None for page or tab capture.** All requested documents and screen classes are delivered. Three virtualized-menu automation failures were recovered; their resolved records remain in the manifest for traceability. Representative meaningful input states were captured; exhaustive enumeration of every possible parameter combination was not attempted. Optional 768-width coverage includes four pages, not all eleven.
