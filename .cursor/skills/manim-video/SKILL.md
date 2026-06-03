---
name: manim-video
description: >-
  Write, validate, and render Manim Community Edition v0.20.1 animation scripts
  for the manimations repo. Converts narration/beat scripts to Manim using
  TypeWithCursor, split-screen white cards, and progressive reveal. Use when
  the user asks for Manim scenes, course videos, beat scripts, text-to-manim,
  or manim -ql/-qh renders.
---

# Manim Video Authoring

Write Manim CE **v0.20.1** scenes for this repo. Match [conventions.md](conventions.md) and validate by rendering.

## Text → animation workflow

When the user gives narration or beats (not Python):

1. Read [text-to-manim.md](text-to-manim.md) — NLU/scene-graph pipeline adapted from [manim-video-generator](https://github.com/rohitg00/manim-video-generator)
2. Read [script-template.md](script-template.md) — beat format, layouts, **camera IDs**
3. Camera details: [reference/cameras/COURSE_GUIDE.md](reference/cameras/COURSE_GUIDE.md)
4. Generate ASCII grid: `scripts/generate_grid.py --list-layouts` or `--example beat1`
5. Read [reference/rohitg00-patterns.md](reference/rohitg00-patterns.md) — layout and pacing patterns
6. Implement in `Episode{N}/beats/beat{M}/` using `BeatScene` + `load_beat_icon` (or `MovingCameraScene` if camera beat)

## Code workflow

1. Read [conventions.md](conventions.md) and [examples.md](examples.md)
2. API lookup: [reference/INDEX.md](reference/INDEX.md) or [tutorials/](tutorials/)
3. Create/edit `Episode{N}/beats/beat{M}/<scene>.py` (or legacy `animations/<file>.py`)
4. Sync icons: `scripts/fetch_icons.py --episode N --beat M`
5. Validate:
   ```bash
   manim -ql Episode1/beats/beat1/welcome_to_python.py WelcomeToPython
   ```
6. Final: `manim -qh Episode{N}/beats/beat{M}/<scene>.py <SceneClass>`

## Manimations Studio

Web UI at `platform/` — chat/script → beats JSON → async Manim preview + 1080p export. **Author:** Divyanshu Singh.

- **In-app docs:** book icon in **top header** (left of project name) → opens `/docs` in a new tab
- Beat types: `statement`, `question`, `joke`, **`code_demo`**, `list`, `compare`, `explain`, `recap`
- Beat script format: [script-template.md](script-template.md) · `platform/assets/beat-script-template.md` · `platform/assets/docs/`
- **Beats editor tabs:** Content, Icon (full picker + hex color), Emphasis, Camera
- **Icon entrances:** `fade_in`, `pop_in`, `slide_from_*`, `pulse`, `none`
- **Preview progress:** percentage + phase during 420p async render
- **Themes:** pick/create before project; backgrounds + typography stored in SQLite
- Chat/script **save beats only**; preview via async `POST /render` + poll `/render-status`

## Layout defaults (required)

- **Background:** default theme `builtin_orange` uses `background/orange_theme_BG.png`; Studio themes may use image, GIF, or looping video
- **Split screen:** left 50% = visual/animation, right 50% = white card (alternate sides sometimes)
- **No camera zoom** unless user explicitly requests it — use plain `Scene`
- **Text on cards:** black, `TypeWithCursor` with yellow cursor
- **Labels:** yellow, top edge only
- **Text on orange BG (no card):** white, left-aligned in half-screen

## Animation defaults

| Content | Use |
|---------|-----|
| Card | `GrowFromCenter` |
| Text | `TypeWithCursor` + optional `Blink` |
| Code | `TypeWithCursor` on `Text(..., font="Courier New")` |
| Lists | `LaggedStart(FadeIn(...))` |
| Morphs | `ReplacementTransform` (circle→square) |
| Exit beat | `fade_clear(...)` |

## Reference lookup

| Topic | File |
|-------|------|
| Studio full guide | `platform/assets/docs/` · `/docs` in browser |
| Beat script format | [script-template.md](script-template.md) |
| Text/narration → scenes | [text-to-manim.md](text-to-manim.md) |
| External repo patterns | [reference/rohitg00-patterns.md](reference/rohitg00-patterns.md) |
| Manim API | [reference/INDEX.md](reference/INDEX.md) |
| Tutorials | [tutorials/quickstart.md](tutorials/quickstart.md) |

Do not load the entire reference corpus. Open only the file you need.

## Golden reference file

`animations/intro_python_hello_world.py` — split layout, TypeWithCursor, white cards, 18 beats.

## Output checklist

- [ ] Orange BG, white cards where appropriate
- [ ] TypeWithCursor for text (not Write)
- [ ] No camera unless requested
- [ ] Validated with `validate.sh`
- [ ] User given video path and `-qh` command

## Refresh Manim docs

```bash
python3 .cursor/skills/manim-video/scripts/fetch_docs.py
```

## External training source

Manim text-to-animation patterns: https://github.com/rohitg00/manim-video-generator
