# FreightIQ — existing UI design audit

Audit scope: actual Streamlit pages at commit `0e1d2e87f6fa43c3c47e34d651323e9fd013860d`, captured on 24 October 2026. These are recommendations only. No application UI, algorithm or business rule was changed.

## Executive priorities

1. Establish one coherent navigation system and a persistent active-shipment/route/data-period context.
2. Make the selected decision and its evidence easy to scan without several screens of scrolling.
3. Separate synthetic data, external weather evaluation, illustrative text and model-generated outputs visually and semantically.
4. Design table, chart, form, empty and infeasible states together, including dark mode and narrow widths.
5. Treat inconsistencies in data/date handling as engineering issues to resolve separately, not issues that visual polish can conceal.

## Findings and recommendations

| Area | Existing evidence | Redesign recommendation |
|---|---|---|
| Navigation | Sidebar and ten-button top navigation duplicate most destinations. Home/Control Tower duplicate the same view; labels differ between navigation and headings. | One primary navigation hierarchy, consistent naming, a compact persistent context bar. Keep all eleven existing entry points mapped during migration. |
| Hierarchy | Overview hero is tall, with large gaps between labels and values; charts and their evidence sit far below the fold. | Compact decision summary: recommended action/date, expected cost, robustness and provenance first; supporting detail in a second tier. |
| Scrolling | Charter explanations, alternatives and sensitivity create a very long page. Forecasts appends model metrics and public weather validation below a large chart. | Use clearly named sections, anchor navigation or contextual detail drawers; retain all content and disclosure. |
| Spacing | Large top gutter, repeated spacer blocks and generous card padding use substantial vertical space. | Define a small spacing scale and distinct compact/expanded card patterns. Avoid empty space that hides decision evidence. |
| Typography | Small muted labels compete with dense table text; page headings use inconsistent levels, including Operations' smaller heading. | Establish a consistent page title, section, KPI, label and body scale. Reserve monospace/tabular numerals for identifiers and quantities. |
| Information architecture | Market Intelligence mixes an active-route snapshot with the original benchmark strip and fixed news. Public weather validation sits on the freight forecast page. | Distinguish active route vs benchmark; place external-method validation in an explicitly separate validation section. |
| Data tables | Wide, canvas-backed tables require horizontal scrolling; long source/notes/route columns are difficult to read. | Pin key columns, right-align numbers, provide short visible summaries with row detail, and allow full-screen inspection. Preserve units and provenance. |
| Charts | Actual browser screenshots contain the literal title “undefined” despite source-level checks. Decision Twin heatmap packs many dates and costs into small cells. | Use explicit titles or truly omit them; reduce default date label density, provide readable hover detail and clear legends. Keep a comparison-friendly scale. |
| Forms | Shipment inputs are in the sidebar on Decision Twin and in a horizontal toolbar on Chartering. Dense top navigation competes with inputs at 1440 width. | Use one consistent shipment-context editor; group cargo, route and timing logically, with an explicit apply/recompute state. |
| Interactions | Some buttons trigger recomputation, while other controls rerun immediately. Connection-table action text looks actionable but is not. | Make control effects explicit. Distinguish informational cells from buttons and provide clear calculation freshness/loading feedback. |
| Weak differentiation | Most bordered containers have similar visual weight; cautionary or simulated results often resemble decision-ready output. | Use restrained semantic status styling with text and icons. Distinguish assumption, simulated result, verified external observation and unavailable result. |
| Date consistency | With capture-date defaults in October, Charter Workbench shows an October/November laycan but returns September candidates. Backend falls back to the entire forecast when the filtered window is empty. | Show an explicit out-of-coverage state and require a valid date selection. This needs a separate behavior change; do not conceal it in the redesign. |
| Route consistency | Some pages use route-specific synthetic histories; Charter Workbench/Decision Twin page load the original shared dataset. Route metadata card has legacy/fallback values. | Show data lineage and active context consistently; reconcile backend wiring before implying all outputs share one route baseline. |
| Empty state | Data Explorer's Dataset tab has no body. Its intended processed table/download are under Route Freight Series in the current source. | Give Dataset its correct content or an explicit empty state; preserve the existing table/download capability. |
| Theme consistency | Custom light/dark CSS coexists with native dataframe canvases and charts that explicitly use white backgrounds. | One semantic theme across chart plot/paper, table cells, inputs, borders and text; validate contrast in the actual browser. |
| Trust | Activity/news/bunker statements are fixed text; model cards include descriptions that do not always match backend calculations. | Use “illustrative” labels and distinguish model documentation from computed run evidence; verify copy before promoting it to executive metrics. |
| Responsive layout | Many fixed multicolumn groups and a ten-button shell lack a dedicated narrow-screen navigation pattern. | Collapse navigation into an accessible menu; reflow KPI groups and forms; retain horizontal table inspection without clipping controls. Use the 768 captures as current-state evidence, not target designs. |

## Executive dashboard opportunity

The existing inputs and outputs can support a clearer summary without adding fictional capabilities: active shipment → recommended candidate → cost and downside → comparison evidence → assumptions/data scope → next available action. Put baseline/scenario context and last calculation scope next to the result. Keep model validation, audit history and detailed sensitivity one interaction away. Consolidate duplicate summaries after explicitly mapping their different data dependencies.

## States the new design must handle

- Initial synthetic demo state and stale/out-of-period history.
- Infeasible cargo/route/date constraints and unsupported routes.
- Forecast model choice and short/long horizon; expanded route comparison.
- Scenario preset, custom shock, reset and active-scenario propagation.
- Empty audit log and logged operator note; read-only parameter registry.
- Valid uploaded CSV, missing-column warning and parse errors.
- Download-ready PDF/CSV; unavailable analytical content must not be fabricated.
- Empty Dataset tab in the reference, dense table overflow, collapsed/expanded explanations, light/dark and narrow-screen layouts.

## Scope limits

This is design discovery, not a production-readiness certification, accessibility conformance audit or numerical validation of every model. Screenshots faithfully preserve current defects and display copy. Download verification checks that the existing controls produce files; it does not endorse every analytical statement inside the reports. The screenshot index and verification report separate successfully captured UI states from any blocked interactions.
