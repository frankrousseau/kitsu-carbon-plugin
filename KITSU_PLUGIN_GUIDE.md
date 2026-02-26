# Kitsu Plugin Development Guide

Generic conventions and patterns for building Kitsu plugins. Plugin-specific details belong in `SPECS.md` and `FRONTEND_SPECS.md`.

## Plugin Structure

```
plugin-name/
├── manifest.toml          # Plugin metadata
├── __init__.py            # Routes and lifecycle hooks
├── models.py              # SQLAlchemy models
├── services.py            # Business logic
├── resources.py           # Flask-RESTful API endpoints
├── migrations/            # Alembic database migrations
└── frontend/              # Vue 3 frontend (optional)
    ├── package.json
    ├── vite.config.js
    ├── eslint.config.js
    └── src/
        ├── main.js
        ├── router.js
        └── components/
```

## manifest.toml

```toml
id = "plugin-id"
name = "Plugin Name"
description = "Short description."
version = "0.1.0"
maintainer = "CGWire <contact@cg-wire.com>"
website = "cg-wire.com/kitsu"
license = "AGPL-3.0-only"
icon = "leaf"                        # Lucide icon name
frontend_project_enabled = true      # Show in production context
frontend_studio_enabled = true       # Show in studio context
maintainer_name = "CGWire"
maintainer_email = "contact@cg-wire.com"
```

## Backend

### Routes (`__init__.py`)

Routes are defined as a list of `(path, Resource)` tuples. Paths are relative — Zou automatically prefixes them with `/api/plugins/<plugin_id>/`.

```python
from . import resources

routes = [
    ("/my-endpoint", resources.MyResource),
    ("/items/<item_id>", resources.ItemResource),
]
```

### Lifecycle Hooks (`__init__.py`)

Four optional hooks are called during plugin install/uninstall:

```python
def pre_install(manifest):
    pass

def post_install(manifest):
    # Seed initial data, run setup tasks
    pass

def pre_uninstall(manifest):
    pass

def post_uninstall(manifest):
    pass
```

### Models (`models.py`)

Use SQLAlchemy models. Table names must be prefixed with `plugin_<plugin_id>_` to avoid collisions.

### Resources (`resources.py`)

Use Flask-RESTful `Resource` classes. Available Zou models for querying:

- `TimeSpent` — work time entries
- `Task` — tasks with entity and task_type references
- `Entity` — shots, sequences, episodes, assets
- `EntityType` — asset types
- `TaskType` — task type definitions
- `Person` — artist info
- `Project` — production/project data

### Migrations

Use Alembic for database migrations. They run automatically on `zou install-plugin`.

## Installation

```bash
zou install-plugin /path/to/plugin
```

This will:
1. Run Alembic migrations
2. Call `pre_install()` then `post_install()` hooks

## Testing

Tests use Zou's `ApiDBTestCase` base class which provides:
- Automatic database setup/teardown with transactions
- Fixture generators (`generate_fixture_project()`, `generate_fixture_task()`, etc.)
- Authentication helpers (`log_in_admin()`, `log_in_cg_artist()`)
- HTTP method helpers (`get()`, `post()`, `put()`, `delete()`)

```bash
pip install -e .
pytest tests/ -v
```

## Frontend

### Technology Stack

- Vue 3 (Composition API with `<script setup>`)
- Pinia (state management)
- Vite (build tool)
- Vue Router with `createWebHashHistory` (required for static plugin serving)

### Vite Configuration

```js
export default defineConfig({
  plugins: [vue()],
  base: './',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

- `base: './'` is required for static file serving inside Kitsu
- The dev proxy forwards `/api` to the local Zou server

### Router

Must use `createWebHashHistory` since plugins are served as static files. Kitsu passes context via the real URL query string (`?production_id=xxx`), so on initial load, transfer these params into the hash-based route:

```js
const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

const realParams = new URLSearchParams(window.location.search)
if (realParams.toString()) {
  const query = {}
  realParams.forEach((value, key) => {
    query[key] = value
  })
  router.isReady().then(() => {
    router.replace({ path: '/', query })
  })
}
```

### Context from Kitsu

Kitsu provides context to plugins via URL query parameters:

| Parameter | Description |
|-----------|-------------|
| `production_id` | Current production UUID (absent in studio context) |
| `episode_id` | Current episode UUID (for TV series) |

Use these to determine which view to show (studio-wide vs production-specific).

### Zou API Access

Plugins can fetch data from the main Zou API. Common endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /api/data/task-types` | All task types |
| `GET /api/data/projects/open` | All open productions |
| `GET /api/data/projects/:id/sequences` | Sequences for a production |
| `GET /api/data/projects/:id/episodes` | Episodes for a production |
| `GET /api/data/projects/:id/asset-types` | Asset types for a production |

### Code Style

- **Backend**: [Black](https://black.readthedocs.io/) formatter with `--line-length 80`
- **Frontend**: ESLint + Prettier using [Kitsu's ESLint config](https://github.com/cgwire/kitsu/blob/main/eslint.config.js) — run `npm run lint`

### Build

```bash
cd frontend
npm run build
```

Output goes to `frontend/dist/`, which Zou serves as static files.
