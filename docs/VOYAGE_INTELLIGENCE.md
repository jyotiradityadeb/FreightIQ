# Voyage Intelligence map

The Overview, Control Tower, and Charter Workbench cards render the same interactive geographic view of the selected FreightIQ route. The map is a **decision-support illustration**, not a passage plan or vessel tracker.

## Implementation

- [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/) 6.16.0 is bundled locally with its worker and CSS. It renders the land, corridor, and port markers without runtime tile requests or a paid mapping account. The rest of the web client remains plain JavaScript.
- Land polygons come from [Natural Earth 1:110m land](https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_land.geojson), a public-domain small-scale map. This is a geographic backdrop, not a detailed nautical chart.
- `web/geo/voyages.json` contains 23 precomputed **illustrative** corridors from [searoute 1.6.0](https://github.com/genthalili/searoute-py). The upstream project explicitly warns that it is not for routing purposes. `scripts/generate-voyage-geometry.py` regenerates the data with `python -m pip install searoute==1.6.0` followed by `python scripts/generate-voyage-geometry.py`.
- Port reference points for Hay Point, Gladstone, and Paradip are converted from published coordinates by [North Queensland Bulk Ports](https://nqbp.com.au/__data/assets/pdf_file/0021/3279/Port-of-Hay-Point_Factsheet_Port-Security-Advice-2024.pdf), [Gladstone Ports Corporation](https://gpcl.com.au/wp-content/uploads/2024/09/About-the-Port_Updated-September-2024.pdf), and [Paradip Port Authority](https://paradipport.gov.in/know-your-port/). Other port markers use the approximate coordinates already in FreightIQ's port master. Popup source labels distinguish these cases.
- Distance is the generated sea-graph length in nautical miles. Estimated sea transit is distance divided by the selected vessel class's configured speed in knots, divided by 24. It excludes port wait, weather delay, canal delay, and other operational time. These values are separate from the optimizer's configured distance and transit assumptions, which Charter Workbench labels separately below the map; the map does not change optimization output.
- The map reads synthetic weather, destination congestion, and waiting-time signals from the active route's existing data. It does not combine them into a route-level risk score. After a Scenario Lab run for its fixed Hay Point–Paradip case, the map shows applicable shock inputs and the scenario engine's baseline and stressed total cost. Scenarios do not move the geographic corridor.

## Interaction and fallback

The map fits the selected corridor on load. Port markers open details on click, map drag and scroll allow inspection, and Reset View restores the fitted extent. The Alternatives tab explains that the app has no validated alternative navigation routes; charter date alternatives are separate. A missing geometry file or unavailable WebGL leaves the dashboard usable and displays an explanatory map state. Map instances are removed when the view changes.

The footer and route overlay disclose **DEMO / SYNTHETIC**, **NOT LIVE AIS TRACKING**, and **ROUTING NOT VERIFIED**. There is no live vessel position, arrival prediction, or warning feed. Future integration would require a licensed maritime routing source with vessel-draft constraints, validated port approaches, route-level risk calculations, and (if offered) a real AIS feed.

## Verification

Run `python scripts/verify-voyage-map.py` against the local web and Python services. It checks map rendering, marker details, map controls, unavailable alternatives, Gladstone route selection, mobile overflow, and missing-geometry fallback. Screenshots are saved under `design/visual-verification/implementation/`.
