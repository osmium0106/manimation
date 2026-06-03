# Quick start

Get Manimations Studio running locally in a few minutes.

## Prerequisites

- Python 3.11+ with the repo Manim venv
- Node.js 18+
- OpenAI API key

## Setup

1. **Environment**

```bash
cp platform/.env.example platform/.env
# Add OPENAI_API_KEY=sk-...
```

2. **Backend** (uses repo Manim for rendering)

```bash
chmod +x platform/start-backend.sh platform/start-frontend.sh platform/start.sh
./platform/start-backend.sh
```

3. **Frontend** (separate terminal)

```bash
./platform/start-frontend.sh
```

4. Open **http://127.0.0.1:5173**

Or run both: `./platform/start.sh`

## First project

1. On the **Projects hub**, click **New project**.
2. **Pick or create a theme** — required before any video.
3. Describe your animation in **Chat**, or switch to **Beat script** and paste from the template.
4. Wait for preview render — progress shows **percentage + phase** (Preparing → Compiling → Animation N).
5. Click **1080p60** when ready for HD export.

## Two-phase flow

Studio separates **ingest** (fast) from **render** (slow):

| Phase | What happens | Endpoint |
|-------|--------------|----------|
| Ingest | Parse/save beats | `POST /chat`, `POST /script`, `PUT /beats` |
| Render | Manim preview (420p) | `POST /render` → poll `/render-status` (~400ms) |
| Export | 1080p60 | `POST /export` → poll `/export-status` |

After editing beats, use **Re-render** in the preview toolbar. Chat may show “Rendering…” while the follow-up render runs.

## Example Chat prompts

- "Create a 3-beat intro: welcome to Python, what is Python?, simple answer with joke."
- "Create a code_demo beat showing a Python decorator."
- "Change beat 2 to use slide_from_right icon entrance and triple_top grid."
- "Make beat 1 continue into beat 2 without fading to black."

## Deployment

For VPS / DigitalOcean with Nginx + Docker, see `platform/DEPLOY-DIGITALOCEAN.md`. The frontend SPA serves `/docs` routes via `try_files … /index.html`.

## Related

- [Studio UI](studio-ui) — full interface tour
- [Beat script format](beat-script) — structured authoring
