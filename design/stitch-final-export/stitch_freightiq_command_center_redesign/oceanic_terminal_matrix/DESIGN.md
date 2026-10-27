---
name: Oceanic Terminal Matrix
colors:
  surface: '#061424'
  surface-dim: '#061424'
  surface-bright: '#2d3a4c'
  surface-container-lowest: '#020f1f'
  surface-container-low: '#0f1c2d'
  surface-container: '#132031'
  surface-container-high: '#1e2b3c'
  surface-container-highest: '#293647'
  on-surface: '#d6e3fa'
  on-surface-variant: '#bbc9cb'
  inverse-surface: '#d6e3fa'
  inverse-on-surface: '#243142'
  outline: '#859395'
  outline-variant: '#3c494b'
  surface-tint: '#3bd9eb'
  primary: '#7ff0ff'
  on-primary: '#00363c'
  primary-container: '#35d6e8'
  on-primary-container: '#005962'
  inverse-primary: '#006973'
  secondary: '#41deb9'
  on-secondary: '#00382c'
  secondary-container: '#00c19e'
  on-secondary-container: '#00493a'
  tertiary: '#6bf8ba'
  on-tertiary: '#003824'
  tertiary-container: '#4adba0'
  on-tertiary-container: '#005c3e'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#90f1ff'
  primary-fixed-dim: '#3bd9eb'
  on-primary-fixed: '#001f23'
  on-primary-fixed-variant: '#004f57'
  secondary-fixed: '#65fbd5'
  secondary-fixed-dim: '#41deb9'
  on-secondary-fixed: '#002019'
  on-secondary-fixed-variant: '#005141'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#061424'
  on-background: '#d6e3fa'
  surface-variant: '#293647'
typography:
  display-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  display-md:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  title-md:
    fontFamily: Geist
    fontSize: 15px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0em
  body-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0em
  code-data:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
    letterSpacing: 0.03em
  label-xs:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 12px
    letterSpacing: 0.08em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 0.75rem
  gutter-desktop: 1rem
  margin: 1rem
  margin-desktop: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system expresses a high-stakes maritime intelligence command environment. It bridges the computational rigor of high-frequency financial terminals (Bloomberg, Palantir) with the navigational poetry of hydrographic surveys and oceanic cartography. 

The aesthetic is cool-toned, hyper-precise, and unapologetically dense. It eliminates decorative ambiguity in favor of mission-critical clarity: dark sea canvases, luminous telemetry lines, etched bathymetric contours, and crisp tabular typography. The interface prioritizes executive decision readiness—communicating real-time cargo movement, geopolitical bottlenecks, marine fuel arbitrage, and predictive supply route disruptions without latency or cognitive clutter.

## Colors

The color architecture is built around an oceanic twilight spectrum designed to mitigate eye strain in prolonged control room operations while highlighting volatile anomaly spikes.

- **Base Canvas (`#071525`):** The foundational infinite depth; used for full-screen dashboards, chart voids, and underlying viewport architecture.
- **Surface Tier 1 / Navigation Bar (`#0D2033`):** Sidebar rails, command docks, and secondary utility shelves.
- **Surface Tier 2 / Card Elevated (`#13283C`):** KPI modules, analytical inspector flyouts, decision matrix cards, and modal dialogs.
- **Structural Dividers (`#244155`):** Fine hairline demarcations (1px) used instead of drop shadows to define operational perimeters.
- **Primary Accent (`#35D6E8` - Electric Cyan):** Active filters, focused data paths, synthetic forecasts, predictive trend vectors, and primary metric indicators.
- **Secondary Accent (`#36D6B2` - Ocean Turquoise):** Active sea-lanes, confirmed maritime routes, waypoint selections, and bathymetric highlights.
- **Semantics:**
  - **Favorable / Confirmed (`#10B981`):** Optimal passage, on-schedule ETA, certified cargo integrity.
  - **Caution / Divergence (`#F59E0B`):** Chokepoint congestion, synthetic demo state, weather advisories, bunkering price divergence.
  - **Critical / Threat (`#EF4444`):** War-risk zones, AIS signal loss, severe mechanical casualty, margin deficit.
  - **Neutral Anchor (`#64748B`):** Dormant waypoints, historic vessel tracks, and structural inactive nodes.
- **Text & Contrast:** Primary glyphs use Soft Crisp White (`#ECF5F7`) to guarantee WCAG AAA contrast against dark surfaces. Secondary and contextual metadata utilize Blue-Gray (`#9BB2C2`).

## Typography

The typographic hierarchy prioritizes rapid scannability and structural alignment under dense information loads.

- **Primary Matrix (Geist):** Handles standard display, section headers, and core operational body text. Geist provides geometric neutrality with a sharp digital character, ensuring high rendering fidelity across high-DPI and standard command monitors. All numerical readouts in Geist must mandate `font-variant-numeric: tabular-nums` to preserve vertical decimal tracking across dynamic ticker streams.
- **Telemetry & Identity Matrix (JetBrains Mono):** Dedicated to technical data tags, latitude/longitude coordinates (`24°18'N 054°22'E`), Port UN/LOCODEs (`AU_HPT -> IN_PDP`), vessel IMO numbers, hash signatures, and protocol timestamps. The monospaced rhythm creates an authentic tactical terminal aesthetic, ensuring that fluctuating telemetry rows never cause horizontal layout jitter.

## Layout & Spacing

The layout employs a high-density, 12-column analytical grid optimized for 1920x1080 tactical workspaces, with horizontal responsiveness scaling down to multi-window split views (minimum 1280px).

- **Grid Architecture:** 12 columns with tight `1rem` (16px) gutters to maximize data real estate. Pinned navigation rail on the far left spans a fixed `64px` collapsed or `240px` expanded width. Main operational viewports use flexible proportional splits (e.g., 8-column primary tactical chart coupled with a 4-column real-time manifest feed).
- **Spatial Rhythm:** Built upon a compact 4px base increment (`space-xs` = 4px, `space-sm` = 8px, `space-md` = 12px, `space-lg` = 16px, `space-xl` = 24px). Micro-paddings ensure data tables and KPI aggregates display maximum context per vertical inch without causing visual collisions.
- **View-Pane Logic:** High-priority command screens avoid long document scrolling. Panels favor fixed-height containers with internal independent scrolling (`overflow-y: auto`) and sticky table headers, ensuring continuous visibility of baseline coordinate planes and metric summaries.

## Elevation & Depth

This design system avoids traditional, soft cloud-like shadows, which dilute the technical clarity of marine instruments. Depth is established through **architectural surface stratification** and **luminescent edge telemetry**:

- **Layered Surfaces:** Hierarchy progresses strictly from dark to lighter oceanic depths: Canvas (`#071525`) sits at the base; interactive panels and cards lift to Surface Tier 2 (`#13283C`). Floating tooltips and diagnostic modals lift to Surface Tier 3 (`#1A344E`).
- **Hairline Bounding:** Rather than fuzzy drop shadows, surfaces are contained by a 1px border of `#244155`. When a card is active, targeted, or in a critical evaluation state, this border shifts to Electric Cyan (`#35D6E8`) or Ocean Turquoise (`#36D6B2`) with a subtle 1px inner glow (`box-shadow: inset 0 0 8px rgba(53, 214, 232, 0.15)`).
- **Bathymetric Glass & Overlays:** Secondary diagnostic overlays utilize frosted hydrographic glass: `background: rgba(13, 32, 51, 0.85)` combined with `backdrop-filter: blur(12px)` and a subtle `#244155` outline, maintaining visibility of underlying route geometry and ocean currents.

## Shapes

The design system embraces an engineered, angular physical form factor with minimal radiuses (`0.25rem` or 4px for core components), evoking mil-spec equipment, precision radar enclosures, and naval navigation computers.

- **Standard Containers & Cards:** Set to `rounded` (4px). Keeps data borders crisp and enables seamless horizontal tile stacking without awkward corner voids.
- **Status Tags & Terminal Badges:** Sharp 2px corner radius or pure rectangular forms with 1px structural framing, keeping micro-tags compact.
- **Action Buttons & Route Nodes:** Subtle 4px radius (`space-xs`), transitioning to pill shapes exclusively for interactive vessel tracking anchors and real-time live radar indicator beacons.

## Components

### 1. Executive KPI Tiles
- **Structure:** Surface background (`#13283C`), 1px `#244155` border, 4px corner radius.
- **Header:** Upper row features metric name in `label-xs` Blue-Gray (`#9BB2C2`), paired with a monospaced provenance tag on the right (e.g., `[AIS_SAT_FEED]` or `[BDI_INDEX]`).
- **Data Core:** Large tabular metric (`display-md` or `headline-sm`) in `#ECF5F7` accompanied by small denomination tags (`USD/MT`, `₹ Lakhs`, `DWT`).
- **Delta Indicator:** Sub-label showing trend vectors with directional arrows (`+4.2%`) highlighted in Emerald Green (`#10B981`) or Coral Red (`#EF4444`).

### 2. Maritime Route Schematic Banner
- **Background Canvas:** Gradient transitioning from `#0D2033` to `#071525` with SVG-etched vector bathymetric contour lines (`#244155` at 40% opacity).
- **Telemetry Track:** Luminous bezier arc connecting Origin and Destination ports (rendered in Ocean Turquoise `#36D6B2`). Projected or synthetic alternative routes render in dashed Electric Cyan (`#35D6E8`).
- **Waypoint Nodes:** Monospaced route identifier labels (`code-data`) set over pulsing circular radar blips. Current vessel position glows with an animated radial pulse (`box-shadow: 0 0 12px #35D6E8`).

### 3. High-Density Tactical Tables
- **Header:** Pinned top row, `#0D2033` background with a solid 1px bottom border in `#244155`. Labels set in `label-xs` uppercase tracking.
- **Rows:** Alternating rows leverage `#13283C` and `#0E2337` to guarantee horizontal tracking ease across multi-column voyage ledgers. Row height is strictly capped at `36px`.
- **Numerics & Cell Formatting:** Tabular alignment—all currency, coordinates, and vessel metrics right-aligned using `JetBrains Mono`. Status columns house micro-chips with 6px semantic indicator dots.

### 4. Recommendation Decision Cards
- **Visual Weight:** Prominent card with a specialized 1px gradient stroke border (`linear-gradient(135deg, #35D6E8, #244155)`).
- **Decision Engine Split:**
  - *Left Pillar:* Robustness Score gauge (e.g., `94.8% OPTIMAL`) rendered in Electric Cyan with an circular telemetry meter.
  - *Center Body:* Strategic rationale synopsis (`body-sm`) describing fuel-oil spread benefits, piracy risk avoidance, and Suez congestion bypass metrics.
  - *Right Pillar:* Cost-benefit delta matrix highlighting projected demurrage savings in tabular Green numerals.
- **Action Footprint:** High-contrast tactical confirmation button with full Electric Cyan fill (`#35D6E8`) and dark ink (`#071525`) for instant visual acquisition.

### 5. Terminal Toolbars & Filter Bars
- **Arrangement:** Horizontal rail anchored below the global header. Houses segmented operational view switches (`TACTICAL MAP`, `FLEET MATRIX`, `PORT CONGESTION`, `ARBITRAGE LEDGER`).
- **Active State:** Underlined by a 2px `#35D6E8` accent line accompanied by a subtle ambient top wash.
- **Micro Chips:** Monospaced filter toggles with border `#244155` that invert to background `#35D6E8` with dark typography `#071525` when toggled.