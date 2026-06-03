# API reference

REST endpoints for Manimations Studio backend (FastAPI, default `http://127.0.0.1:8000`).

## Documentation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/docs` | GET | Documentation manifest (nav tree) |
| `/api/docs/pages/{slug}` | GET | Single doc page markdown |
| `/api/studio-guide` | GET | Legacy combined guide markdown |
| `/api/beat-script-template` | GET | Beat script starter template |

## Projects

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects` | GET | List projects |
| `/api/projects` | POST | Create project |
| `/api/projects/{id}` | GET | Load project |
| `/api/projects/{id}` | PATCH | Update project metadata |
| `/api/projects/{id}` | DELETE | Delete project |
| `/api/projects/{id}/chat` | POST | AI chat → beats |
| `/api/projects/{id}/script` | POST | Parse script → beats |
| `/api/projects/{id}/script` | GET | Export beats → script |
| `/api/projects/{id}/beats` | PUT | Save beats from editor |
| `/api/projects/{id}/validate-beats` | POST | Pre-render validation |

## Render & export

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects/{id}/render` | POST | Start preview render (`-ql`) in background — returns immediately |
| `/api/projects/{id}/render-status` | GET | Poll preview progress (`progress` 0–100, `phase` string) |
| `/api/projects/{id}/render/cancel` | POST | Cancel preview job |
| `/api/projects/{id}/export` | POST | Start 1080p60 export |
| `/api/projects/{id}/export-status` | GET | Poll export progress |

## Code editor

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects/{id}/code` | GET | Generated scene Python |
| `/api/projects/{id}/code` | PUT | Save code (+ optional sync render) |
| `/api/projects/{id}/code/regenerate` | POST | Regenerate from beats |

## Themes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/themes` | GET, POST | List / create themes |
| `/api/themes/{id}` | GET, PATCH, DELETE | Theme CRUD |

## Visuals

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/beat-types` | GET | Beat type metadata |
| `/api/visual-catalog` | GET | Icon concept catalog |
| `/api/icons/search?q=` | GET | Search Iconify |

## Health

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Server status, OpenAI configured |

## Polling pattern

```text
POST /render     → { "status": "rendering" }  (compile + Manim run in background)
GET  /render-status (every ~400ms) → { "status": "rendering", "progress": 23, "phase": "Animation 4 (50%)" }
                                  → { "status": "done", "preview_url": "..." }
```

Export follows the same pattern with `export-status` and progress percentage.

## Related

- [Quick start](quick-start)
- [Studio UI](studio-ui)
