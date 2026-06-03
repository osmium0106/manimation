# Manimations Studio

Local-first platform: describe beats in chat or script → OpenAI structures them → visual resolver picks icons → async Manim preview and 1080p export.

**Author:** Divyanshu Singh  
**Documentation:** [http://127.0.0.1:5173/docs](http://127.0.0.1:5173/docs) — book icon in the **top header bar** (left of project name)

**SQLite** stores the global theme library. **Projects** remain JSON on disk under `~/manimations-studio/projects/` (or `MANIMATIONS_DATA_DIR` in Docker).

## Setup

1. **OpenAI key** — copy and edit:
   ```bash
   cp platform/.env.example platform/.env
   # Add OPENAI_API_KEY=sk-...
   ```

2. **Backend** (uses repo Manim venv for rendering):
   ```bash
   chmod +x platform/start-backend.sh platform/start-frontend.sh platform/start.sh
   ./platform/start-backend.sh
   ```

3. **Frontend** (separate terminal):
   ```bash
   ./platform/start-frontend.sh
   ```

4. Open **http://127.0.0.1:5173**

Or run both: `./platform/start.sh`

## Deploy to DigitalOcean

See **[platform/DEPLOY-DIGITALOCEAN.md](DEPLOY-DIGITALOCEAN.md)** for step-by-step VPS deployment (Nginx + Docker + Manim + HTTPS).

Example configs: `platform/deploy/nginx.conf.example`, `platform/deploy/nginx-host-docker.conf.example`

## Architecture

Two-phase flow — **ingest** (fast) then **render** (async, may take minutes):

```
Theme picker  →  create project (theme_id)
       ↓
Chat / Beat script  →  FastAPI  →  OpenAI (beat JSON)
       ↓
Save project.json (beats only — no render yet)
       ↓
POST /render (returns immediately, status: rendering)
       ↓
GET /render-status (poll every ~400ms)
       ↓
preview MP4 (latest.mp4) — UI shows progress % + phase

1080p60: POST /export → GET /export-status (progress % + phase) → download
```

| Endpoint | Purpose |
|----------|---------|
| `GET /api/docs` | Documentation manifest (multi-page nav) |
| `GET /api/docs/pages/{slug}` | Single documentation page |
| `GET /api/studio-guide` | Legacy combined guide markdown |
| `GET /api/beat-script-template` | Beat script starter template |
| `POST /api/projects/{id}/chat` | AI updates beats; returns project (no render) |
| `POST /api/projects/{id}/script` | Parse script → beats (no render) |
| `POST /api/projects/{id}/render` | Start preview render (`-ql`) in background |
| `GET /api/projects/{id}/render-status` | Poll until preview ready |
| `POST /api/projects/{id}/export` | Start 1080p60 export in background |
| `GET /api/projects/{id}/export-status` | Poll progress % and phase |
| `GET/POST /api/themes` | Theme library (SQLite + uploaded backgrounds) |

Use **Re-render** in the preview toolbar after chat/script changes. Chat loading may show “Rendering…” while the follow-up `/render` poll runs.

**Note:** `PUT /api/projects/{id}/code` with `render: true` still renders synchronously on the server (code editor path).

## Local storage

| Path | Contents |
|------|----------|
| `~/manimations-studio/studio.db` | Theme library (SQLite) |
| `~/manimations-studio/themes/{id}/` | Uploaded theme backgrounds |
| `~/manimations-studio/projects/{id}/project.json` | Beats, chat, theme_id, resolved visuals |
| `~/manimations-studio/projects/{id}/history/` | Snapshots for **Revert** |
| `~/manimations-studio/projects/{id}/renders/latest.mp4` | Preview video |
| `~/manimations-studio/projects/{id}/renders/export_1080p60.mp4` | HD export |

## Themes

Before creating a video, pick or create a **theme** (background image/GIF/video loop, typography, optional color palette). Themes are global on the server. The selected `theme_id` is stored on the project and embedded in generated Manim scenes at render time.

Built-in default: `builtin_orange` (repo `background/orange_theme_BG.png`).

## Visual resolver

- Catalog: `assets/visual_catalog.json`
- Style packs: `assets/style_packs/` (icon policy; often set per theme)
- Resolver: `animations/visual_resolver.py`
- Loader: `animations/visual_library.py`

## Example prompts

- "Create a 3-beat intro: welcome to Python, what is Python?, simple answer with joke."
- "Create a code_demo beat showing a Python decorator."
- "Change beat 2 to use a bigger question mark."

## Beat script mode

Switch to **Beat script** in the left panel. Paste:
- Beat script format (`### BEAT` headers — see `platform/assets/beat-script-template.md`)
- Or JSON: `{"beats": [...]}`

Click **Generate from script** — this **parses and saves beats only**; preview render runs separately (async). Optional: **Use AI to parse** for free-form text.

Supported beat types: `statement`, `question`, `joke`, `code_demo`, `list`, `compare`, `explain`, `recap`.

**Beat options** (per beat in script, Beats editor, or JSON):

- **Icon entrance:** `fade_in`, `pop_in`, `slide_from_left`, `slide_from_right`, `draw_on`, `pulse`
- **Icon grid:** `auto`, `horizontal`, `vertical`, `triple_top`, `triple_bottom`, `quad`
- **Icon reveal:** `auto`, `on_word`, `together`
- **Continue beat:** skip black transition to next beat (`CONTINUE: yes`)
- **Camera:** `moving` + hooks — see `platform/assets/studio-guide.md`

## Beats editor

Switch to **Beats** in the left panel to reorder beats, edit fields inline, pick icons, set icon entrance, and toggle **Continue into next beat**. Changes sync to the Beat script tab.

## Manim code editor

Switch to **Code** tab to:
- View auto-generated scene Python after chat/script
- Write Manim code from scratch (starter template provided)
- Edit and click **Apply & Re-render**
- **From beats** regenerates code from beat JSON (discards manual edits)

Scene file: `~/manimations-studio/projects/{id}/generated_scene.py`

## Download 1080p60

Click **1080p60** in the preview toolbar. Export runs in the background; the UI shows a **progress bar** and phase (e.g. `Animation 12 (63%)`) while polling `/export-status`. When complete, the MP4 downloads automatically. Also saved at:

`~/manimations-studio/projects/{id}/renders/export_1080p60.mp4`

Revert restores any auto-saved snapshot from local history.
