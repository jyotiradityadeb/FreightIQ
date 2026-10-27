# Stitch visual audit

`python scripts/verify-stitch-visuals.py` captures each exported HTML state and the working page at the same 1440 × 900 viewport. Outputs are in `design/visual-verification/references/`, `implementation/` and `diffs/`. It also captures working layouts at 768 × 1024 and 390 × 844. The RGB mean absolute difference is a whole-screen diagnostic (0 = identical; 255 = maximum); text rasterization and live numerical content affect it. A low value alone does not prove layout fidelity.

| State | Mean difference / 255 | Visual finding |
| --- | ---: | --- |
| Overview | 21.6 | Shell and palette align; content density and exact card copy differ |
| Control Tower | 19.6 | 256 px rail and 64 px header align; route illustration still differs |
| Forecasts | 13.9 | Title/selector panel and chart placement align more closely; backend model values differ |
| Charter Workbench | 21.2 | Compact input row and recommendation placement align more closely; source contains fabricated metrics |
| Decision Twin | 23.8 | Sidebar input and adjacent decision surface align more closely; heatmap content differs |
| Scenario Lab | 19.7 | Presets, shock sliders and vertical preview align more closely; reference impact values are illustrative |
| Data Explorer | 17.1 | Compact summary, tabs and separate filter toolbar align; real schema/table contents differ |
| Integrations: Quality | 20.2 | Summary cards and matrix align structurally; source/status rows reflect actual adapters |
| Integrations: Overrides | 21.8 | Working audit-only note replaces implied live override |
| Integrations: Audit | 22.0 | Real local audit rows change between runs; this metric varies with the database |
| Integrations: Limitations | 23.9 | Source has a more specific visual composition and different text hierarchy |

Operations Overview, Market Intelligence and Simulation Backtest have PNG mockups but no matching `code.html`; they were inspected against those screenshots and built in the same shell. Their numerical values come from Python. No exact DOM comparison is possible for them from the archive.

The exported shell, dark surfaces, cyan/green accents, font families, mono labels, rail width, header height, card borders and active navigation state have been carried into the implementation. The remaining discrepancies are meaningful: several source illustrations and charts contain invented real-time telemetry, a more detailed hydrography graphic and cost values that disagree with the Python engine; the working interface uses explicit synthetic labels and actual calculations. Some screen-specific spacing, chart line shapes and content hierarchy are still different. **The result is not pixel-perfect**, and the screenshot differences remain the precise evidence for that limitation.

Mobile captures show the rail hidden behind a menu and cards stacked without horizontal page overflow at 768 and 390 px. The source export does not supply complete interactive mobile states, so those layouts follow the extracted responsive system.
