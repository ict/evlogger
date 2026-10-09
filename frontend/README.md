# EVLogger Frontend

React (Vite) single-page app for the EVLogger API. Built as a static
bundle and served by Caddy, which also reverse-proxies `/api/*` to the
backend so the UI and API share one origin.

## Local development

```bash
npm install
npm run dev
```

Vite dev server runs on `http://localhost:5173` and proxies `/api/*` to
`http://localhost:8000` (the backend). Start the backend separately
(`docker-compose up api mongo`) or point `vite.config.js` at wherever it
runs.

## Production build

```bash
npm run build
```

Outputs to `dist/`. The Docker image (`docker/Dockerfile`) does this in a
build stage and copies the result into a Caddy container.

## Caddy

`Caddyfile` listens on `:80`:
- `/api/*` → `reverse_proxy api:8000` (path stripped)
- everything else → static files from `/srv` with SPA fallback to
  `index.html`
