# Stitch implementation specification

## Source of truth

The approved archive is `C:\Users\jyoti\Downloads\stitch_freightiq_command_center_redesign.zip`. Its unchanged extraction is under `design/stitch-final-export/stitch_freightiq_command_center_redesign/`. Eleven folders contain `code.html`; ten numbered folders contain PNG contact or screen references. `oceanic_terminal_matrix/DESIGN.md` supplies supplementary palette guidance. The HTML files are the primary reference where available. Market Intelligence, Operations Overview and Simulation Backtest have PNG references only. The reference HTML contains illustrative data and controls, so those values do not specify backend behavior.

## Extracted visual system

| Element | Reference value | Implementation |
| --- | --- | --- |
| Rail | `w-64`, 256 px, fixed desktop | `.sidebar` 256 px |
| Header | 64 px, begins after rail | `.topbar` 64 px |
| Main surface | `#061424` | `--surface` |
| Deep surface | `#020f1f` | `--lowest` |
| Low surface | `#0f1c2d` | `--low` |
| Card | `#132031` | `--card` |
| Raised surfaces | `#1e2b3c`, `#293647` | `--high`, `--highest` |
| Main text | `#d6e3fa` | `--text` |
| Border | `#3c494b` | `--outline` |
| Primary cyan | `#7ff0ff` | `--cyan` |
| Chart cyan | `#35d6e8` | `--cyan2` |
| Secondary green | `#41deb9` | `--teal` |
| Type | Geist; JetBrains Mono for data, labels | Google Font references in `web/index.html` |
| Icons | Material Symbols Outlined | Same font family |

The reference uses a dense terminal layout, thin card borders, compact mono labels, cyan action accents, dark graph panels, small rectangular status chips and 2/3-column card grids. The implementation uses 16 px content spacing, 4 px card corners, 12 px form gaps, 10–12 px chart labels, and 32 px page titles. These are aligned to the exported HTML and screenshot measurements. Source screens are responsive HTML with variable screenshot dimensions, not a single fixed artboard. Visual QA uses a common 1440 × 900 viewport.

## Navigation and interaction

Desktop rail stays fixed; navigation scrolls within it. The active item has a brighter surface, cyan label, left border and dot. At 850 px and below it becomes a slide-in menu. The top bar retains the terminal path and shipment context. Integrations and Explorer use horizontal tab strips with cyan selection. Forms use dark filled inputs, outline borders and visible keyboard focus. Tables keep sticky headers, horizontal scroll, row hover, column sorting and full-screen inspection. Time-series charts use muted historical lines, cyan forecasts, a translucent uncertainty band, mono axes and zoom controls. Breakpoints are 1190, 850 and 520 px; reduced-motion preference removes transitions.

## Screen reference inventory

| New screen | Reference |
| --- | --- |
| Overview | `freightiq_overview_home/code.html` |
| Control Tower | `freightiq_control_tower/code.html` |
| Operations Overview | Combined numbered PNG composition, no HTML |
| Market Intelligence | `02_market_intelligence.png/`, no HTML |
| Forecasts | `freightiq_freight_forecasts/code.html` |
| Decision Twin | `freightiq_decision_twin/code.html` |
| Charter Workbench | `freightiq_charter_workbench/code.html` |
| Scenario Lab | `freightiq_scenario_lab/code.html` |
| Simulation Backtest | `07_simulation_backtest.png/`, no HTML |
| Data & Integrations | Four HTML tab states: quality, overrides, audit, limitations |
| Data Explorer | `freightiq_data_explorer/code.html` |

Stitch screenshots do not define all 13 live tab states or every error/loading state. Their missing states follow the corresponding exported shell, colors and component system. Source screenshots include fabricated telemetry, connectors and market activity; live app values come from the Python services and are visibly identified as synthetic or simulated.
