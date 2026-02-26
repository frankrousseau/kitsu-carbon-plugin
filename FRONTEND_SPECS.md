# Carbon Tracking Plugin - Frontend Specifications

## Technology Stack

- Vue 3 (Composition API with `<script setup>`)
- Pinia (state management)
- Vite (build tool)
- Lucide Vue Next (icons)

## Code Style

- ESLint + Prettier using the same config as [Kitsu](https://github.com/cgwire/kitsu/blob/main/eslint.config.js)
- Run `npm run lint` to lint and auto-fix

## Pinia Store (`stores/main.js`)

Central store fetching data from the main Zou API.

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

### Router (`CarbonFootprint.vue`)

- Reads `production_id` and `episode_id` from route query params
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

## Color Palette

| Element | Color |
|---------|-------|
| Page background | `#36393f` |
| Card / square background | `#202225` |
| Accent border / mid-tone | `#2f3136` |
| Interactive element background | `#42464e` |
| Green (lowest impact, active tab, highlights) | `#00aa3c` |
| Orange (medium impact) | `#fb923c` |
| Red (highest impact) | `#ff5252` |

## Unit Toggle

- Container: `#202225` background, `3px solid #202225` border, rounded
- Unselected button: transparent background, `#888` text
- Selected button: `#42464e` background, white text, rounded corners

## Persistence

- Unit preference saved to `localStorage` key `carbon-unit`
- Active tab saved to `localStorage` key `carbon-tab`

## Vite Dev Proxy

```js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
}
```

## Frontend Files

| File | Purpose |
|------|---------|
| `frontend/src/main.js` | App entry, registers Pinia + Router |
| `frontend/src/router.js` | Vue Router with hash history + query param transfer |
| `frontend/src/stores/main.js` | Pinia store (Zou API data) |
| `frontend/src/components/CarbonFootprint.vue` | Router component |
| `frontend/src/components/StudioFootprint.vue` | Studio-wide view |
| `frontend/src/components/ProductionFootprint.vue` | Per-production view |
| `frontend/vite.config.js` | Vite config with dev proxy |
