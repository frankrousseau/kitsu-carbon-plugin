# Carbon Tracking Plugin - Frontend Specifications

See [KITSU_PLUGIN_GUIDE.md](./KITSU_PLUGIN_GUIDE.md) for technology stack, code style, color palette, and Vite dev proxy conventions.

Additional dependency: Lucide Vue Next (icons).

## Pinia Store (`stores/main.js`)

Central store using the options API (`state` + `actions`) fetching data from the main Zou API.

**State:**
- `taskTypes` — all task types from `GET /api/data/task-types`
- `openProductions` — all open productions from `GET /api/data/projects/open`
- `sequences` — sequences for current production from `GET /api/data/projects/:id/sequences`
- `episodes` — episodes for current production from `GET /api/data/projects/:id/episodes`
- `assetTypes` — asset types for current production from `GET /api/data/projects/:id/asset-types`

**Actions:**
- `init()` — fetches task types + open productions in parallel
- `setCurrentProduction(productionId)` — handles production change:
  - No productionId: clears sequences, episodes, asset types
  - TV show (`production_type === "tvshow"`): fetches episodes + asset types, clears sequences
  - Other: fetches sequences + asset types, clears episodes

## Views

### Studio View (`StudioFootprint.vue`)

Displayed when no `production_id` query parameter is set.

**Stat Cards (3 columns):**
1. **Total Studio Emissions** (Cloud icon) — `data.total_co2_kg`
2. **Weekly Average Emissions** (Calendar icon) — total CO2 divided by number of weeks between oldest production start date and latest production end date (from `store.openProductions`)
3. **Total Man-Days** (Users icon) — `data.total_man_days`

**Tabs:**
- **Matrix view** — productions x task types grid with color-coded values
- **Production breakdown** — horizontal bar chart sorted by emissions

**Data behaviors:**
- Task type columns sourced from `store.taskTypes` (falls back to carbon API data)
- Empty columns (all zero values) are hidden
- Info button (top-right) opens calculation modal

### Production View (`ProductionFootprint.vue`)

Displayed when `production_id` query parameter is set.

**Stat Cards (3 columns):**
1. **Total Project Emissions** (Cloud icon) — `data.total_co2_kg`
2. **Weekly Average Emissions** (Calendar icon) — total CO2 divided by number of weeks between the project `start_date` and `end_date` (from `store.openProductions`)
3. **Total Man-Days** (Users icon) — `data.total_man_days`

**Tabs:**
- **Matrix view** — task types grid with color-coded values
- **Step breakdown** — horizontal bar chart sorted by emissions

**Data behaviors:**
- Task type columns sourced from `store.taskTypes` (falls back to carbon API data)
- Empty columns (all zero values) are hidden

### Shared Components & Composable

Duplicated UI elements are extracted into reusable sub-components:

| Component | Purpose |
|-----------|---------|
| `FootprintHeader.vue` | Page header with title, subtitle, unit toggle, and info button |
| `StatCards.vue` | 3-column stat cards (total emissions, weekly average, man-days) |
| `ViewTabs.vue` | Matrix / breakdown tab switcher |
| `ImpactLegend.vue` | Color legend (low / medium / high impact) |
| `InfoModal.vue` | Calculation explanation modal |
| `UnitToggle.vue` | kg/t unit toggle (`v-model`) |

Shared logic lives in `composables/useCarbon.js`:
- Shared state: `unit`, `activeTab`, `showInfo` (with localStorage persistence)
- Formatting: `formatValue`, `formatValueOrDash`, `formatNumber`
- Impact helpers: `getImpactClass`, `getBarWidth`, `getPercent`
- Task type styling: `getTaskTypeColor`, `taskTypeHeaderStyle`, `taskTypeCellStyle`
- Escape key handler for modal dismissal

### Router (`CarbonFootprint.vue`)

- Reads `production_id` from route query params
- Calls `store.init()` on mount
- Watches `productionId` and calls `store.setCurrentProduction()`
- Renders `ProductionFootprint` or `StudioFootprint` based on `production_id` presence
- Uses `createWebHashHistory` for static plugin serving
- On initial load, transfers real URL query params into hash-based route

## Calculation Modal

Explains how carbon is calculated. Shown on Info button click.

**Formula** (monospace font, dark background):
```
Work Time  x  People  x  Carbon Factor
```
"Carbon Factor" displayed in green (#00aa3c).

**Included factors** (2-column grid with icons):
| Icon | Factor |
|------|--------|
| Monitor | Workstation |
| Building2 | Building Energy |
| Zap | Electricity Mix |
| UtensilsCrossed | Meals |
| Cloud | Cloud & Infra |
| TrainFront | Commute |

## Persistence

- Unit preference saved to `localStorage` key `carbon-unit`
- Active tab saved to `localStorage` key `carbon-tab`

## Frontend Files

| File | Purpose |
|------|---------|
| `frontend/src/main.js` | App entry, registers Pinia + Router |
| `frontend/src/router.js` | Vue Router with hash history + query param transfer |
| `frontend/src/stores/main.js` | Pinia store (Zou API data, options API) |
| `frontend/src/composables/useCarbon.js` | Shared state, formatting, and helpers |
| `frontend/src/components/CarbonFootprint.vue` | Router component |
| `frontend/src/components/StudioFootprint.vue` | Studio-wide view |
| `frontend/src/components/ProductionFootprint.vue` | Per-production view |
| `frontend/src/components/FootprintHeader.vue` | Shared page header |
| `frontend/src/components/StatCards.vue` | Shared stat cards |
| `frontend/src/components/ViewTabs.vue` | Shared tab switcher |
| `frontend/src/components/ImpactLegend.vue` | Shared impact legend |
| `frontend/src/components/InfoModal.vue` | Shared calculation modal |
| `frontend/src/components/UnitToggle.vue` | Shared unit toggle |
| `frontend/vite.config.js` | Vite config with dev proxy |
