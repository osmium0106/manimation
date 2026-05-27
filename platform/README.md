# Manimations Studio

Local-first platform: describe beats in chat → OpenAI structures them → visual resolver picks icons → Manim renders preview.

**No database. No cloud storage.** Projects saved to `~/manimations-studio/projects/`.

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

See **[platform/DEPLOY-DIGITALOCEAN.md](DEPLOY-DIGITALOCEAN.md)** for step-by-step VPS deployment (Nginx + systemd + Manim + HTTPS).

Example configs: `platform/deploy/nginx.conf.example`, `platform/deploy/manimations-backend.service.example`

## Architecture

```
Chat (React)  →  FastAPI  →  OpenAI (beat JSON)
                    ↓
              visual_resolver (semantic icons)
                    ↓
              beat_interpreter (Manim)
                    ↓
              preview MP4 (local)
```

## Local storage

| Path | Contents |
|------|----------|
| `~/manimations-studio/projects/{id}/project.json` | Beats, chat, resolved visuals |
| `~/manimations-studio/projects/{id}/history/` | Snapshots for **Revert** |
| `~/manimations-studio/projects/{id}/renders/latest.mp4` | Preview video |

## Visual resolver

- Catalog: `assets/visual_catalog.json`
- Style packs: `assets/style_packs/`
- Resolver: `animations/visual_resolver.py`
- Loader: `animations/visual_library.py`

Concepts (`python`, `question`, `terminal`, `frustration`) map to procedural shapes, brand SVGs, or Iconify icons based on style pack.

## Example prompts

- "Create a 3-beat intro: welcome to Python, what is Python?, simple answer with joke."
- "Change beat 2 to use a bigger question mark."
- "Make the punchline icon less scary — use a volume icon instead."

## Beat script mode

Switch to **Beat script** in the left panel. Paste:
- `beat.script.md` format (### BEAT headers, LABEL, TEXT, ICONS)
- Or JSON: `{"beats": [...]}`

Click **Generate from script**. Optional: **Use AI to parse** for free-form text.

## Manim code editor

Switch to **Code** tab to:
- View auto-generated scene Python after chat/script
- Write Manim code from scratch (starter template provided)
- Edit and click **Apply & Re-render**
- **From beats** regenerates code from beat JSON (discards manual edits)

Scene file saved locally: `~/manimations-studio/projects/{id}/generated_scene.py`

## Download 1080p60

Click **1080p60** in the preview toolbar. Manim renders at `-qh` (1080p 60fps) and downloads the MP4 locally. File also saved at:

`~/manimations-studio/projects/{id}/renders/export_1080p60.mp4`

Revert restores any auto-saved snapshot from local history.
