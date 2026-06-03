# Manimations Studio — Complete Guide

**Author:** Divyanshu Singh  

> **Full documentation site:** open **http://127.0.0.1:5173/docs** — **book icon in the top header bar** (left of project name)  
> Multi-page reference with sidebar nav, search, and on-page table of contents.

This file is a legacy single-page export. The live docs live in `platform/assets/docs/`.

---

## What is Manimations Studio?

Local-first web app: describe beats in **Chat** or **Beat script** → OpenAI structures them → visual resolver picks Iconify icons → async Manim preview and **1080p60** export.

**Data lives at** `~/manimations-studio/` (or `MANIMATIONS_DATA_DIR` in Docker):

| Path | Contents |
|------|----------|
| `studio.db` | Theme library (SQLite) |
| `themes/{id}/` | Uploaded theme backgrounds |
| `projects/{id}/project.json` | Beats, chat, theme, resolved visuals |
| `projects/{id}/renders/latest.mp4` | Preview |
| `projects/{id}/renders/export_1080p60.mp4` | HD export |

---

## Studio UI

### Projects hub

- **New project** — pick or create a theme first (background, typography, palette).
- **Open** — resumes last project via `localStorage`; deep link `?project={id}`.
- **Rename / delete** projects from the hub.

### Studio tabs (left panel)

| Tab | Purpose |
|-----|---------|
| **Chat** | Plain-English prompts → AI updates beats → auto preview render |
| **Beat script** | Paste structured script or JSON → **Generate from script** |
| **Beats** | Timeline editor — Content / Icon / Emphasis / Camera tabs, icon picker, save |

### Right panel

- **Preview (420p)** — async render with **percentage progress** + phase text + cancel
- **1080p60** — background export with progress
- **Code** — view/edit generated Manim Python
- **Theme** dropdown in header — switch theme per project

### Header

- **Documentation** (book icon) — left of project name → `/docs` in new tab
- **Projects** — back to hub
- **Revert** — local snapshots

### Beats editor tabs

| Tab | Edits |
|-----|--------|
| Content | Label, type, layout, text, hold, continue beat |
| Icon | Entrance + full icon picker (search, upload, hex color) |
| Emphasis | Word highlights — hex color, indicate/wiggle |
| Camera | Per-beat camera toggle, steps, load type defaults |

### Two-phase flow

1. **Ingest** — chat/script saves beats only (fast)
2. **Render** — `POST /render` + poll `/render-status` (may take minutes)

Use **Re-render** after edits. Chat may show “Rendering…” while preview runs.

---

## Beat types

| TYPE | Use |
|------|-----|
| `statement` | Card + icon(s), normal reveal |
| `question` | Single icon: white text on BG, no card. Multi-icon: card + grid |
| `joke` / `joke punchline` | Setup + punchline; **2 icons** (primary + swap at punchline) |
| `explain` | Card + tool icon (terminal, code) |
| `recap` | Summary card, optional multi-icon grid |
| `list` | Checklist card — use `LIST (card, checks):` |
| `compare` | Two cards (`dual_card`) — good vs bad, before vs after |
| `code_demo` | Full-width code editor + output panel |

---

## Layout presets

| Layout ID | When to use |
|-----------|-------------|
| `card_right_icon_left` | **Default** — white card right, icon(s) left |
| `card_left_icon_right` | Card left, icon(s) right |
| `text_right_icon_left` | Single icon — white text on theme BG, no card |
| `text_left_icon_right` | White text left, icon(s) right |
| `card_right_only` | Card only, no icon |
| `card_left_only` | Card only, no icon |
| `dual_card` | Cards both sides (compare beats) |
| `code_full_card` | Full-width code + output (`code_demo`) |

**Icon panel side:** icons go on the side **opposite** the card — `card_left_*` → icons **right**, `card_right_*` → icons **left**.

---

## Icon entrances

Controls how icons appear when revealed (batch reveal, not word-sync). Set per beat in **Beats** editor or in script:

```
ICON_ENTRANCE: pop_in
```

| Value | Effect |
|-------|--------|
| `fade_in` | **Default** — FadeIn |
| `pop_in` | Scale from small |
| `slide_from_left` | Enters from left |
| `slide_from_right` | Enters from right |
| `pulse` | FadeIn + subtle pulse |
| `none` | Instant (no animation) |

**Word-sync icons** (`ICON REVEAL: on_word` + `trigger:`) still use per-word FadeIn timing; `ICON_ENTRANCE` applies to batch reveals (primary icon, `together` mode, joke primary before swap).

**JSON:** `"icon_entrance": "slide_from_left"`

---

## Icon grid (multi-icon panel, max 4)

When **2–4 icons** appear together, they sit in an **invisible grid** inside the icon panel (half frame below heading).

| Icons | Grid value | Layout |
|-------|------------|--------|
| 1 | `single` | 100% × 100% |
| 2 | `horizontal` (default) | 50% × 100% side by side |
| 2 | `vertical` | 100% × 50% stacked |
| 3 | `triple_top` (default for 3) | 2 top + 1 bottom full width |
| 3 | `triple_bottom` | 1 top full width + 2 bottom |
| 4 | `quad` | 2×2 grid |

```
ICON GRID:  auto            # pick from icon count (default)
ICON GRID:  horizontal
ICON GRID:  vertical
ICON GRID:  triple_top
ICON GRID:  triple_bottom
ICON GRID:  quad
```

**Joke beats:** exactly **2 icons** — primary then swap at punchline (no grid). **3+ icons** use the grid.

---

## Icon reveal (word-sync)

| Mode | Behavior |
|------|----------|
| `auto` (default) | Word-sync when any icon has `trigger:`; others at end |
| `on_word` | Icons with `trigger` fade in as the word is typed |
| `together` | All icons after text (ignore trigger timing) |

```
ICON REVEAL:  on_word

─── ICONS ───
icon_mobile: mobile phone icon | color: WHITE | trigger: mobile
icon_web: web browser globe | color: WHITE | trigger: web
```

**Trigger words must appear in your TEXT lines.**

---

## Icons section (beat script)

Each line:

```
icon_id: description or fa6-brands:ref | color: WHITE | scale: 1.2 | trigger: word
```

| Part | Meaning |
|------|---------|
| **icon_id** | Local name (`icon_python`, `shape_question`) |
| **description** | Plain English — GPT searches Iconify (or paste `prefix:name`) |
| **color** | `WHITE`, `BLUE`, `#3776AB`, etc. |
| **scale** | Optional (default 1.2) |
| **trigger** | Optional — word in TEXT that reveals this icon |

Browse catalog in **Beats** tab → icon picker, or `GET /api/visual-catalog`.

---

## Card section

```
─── CARD ───
SIDE: right | SIZE: 5.6 × 5.0
```

| SIZE (w × h) | Use |
|--------------|-----|
| 5.6 × 5.0 | 4–5 lines + punchline |
| 5.6 × 4.6 | 3–4 lines |
| 5.6 × 3.8 | 2–3 short lines |
| 5.0 × 2.8 | 1–2 lines |

Card: white, rounded, **black** text, left-aligned. **Grow empty card first** — never bundle text inside `GrowFromCenter(card)`.

Text variants:

- `TEXT (card, black):` — lines inside white card
- `TEXT (white, on BG):` — no card, white on theme background
- `LIST (card, checks):` — checklist items

---

## Emphasis

Highlight a word during typing:

```
─── EMPHASIS ───
word: screaming | color: #FC6255 | animation: wiggle
word: Python | color: #FFD700 | animation: indicate
```

| animation | Effect |
|-----------|--------|
| `indicate` | Pulse highlight (uses emphasis color) |
| `wiggle` | Wiggle — jokes, punchlines |

Word must appear in beat text; otherwise skipped at render. Beats editor **Emphasis** tab has hex color picker.

---

## Camera (moving beats)

Episode meta and/or per beat:

```
CAMERA: moving          # none | moving
```

When `CAMERA: moving`, use **MovingBeatScene** — pan/zoom between panels.

### Camera hooks (beat script)

```
─── CAMERA ───
cam_focus_left: after_icon
cam_focus_right: after_line_1
cam_focus_card: punchline
cam_restore: exit
```

| Hook ID | When |
|---------|------|
| `cam_focus_left` | After icon appears / focus left panel |
| `cam_focus_right` | After line N (`after_line_1`, `after_line_2`, …) |
| `cam_focus_card` | On punchline or card emphasis |
| `cam_restore` | **`exit`** — required every moving beat |

**3–4 icon word-sync:** camera restores to **full frame** so card + grid stay visible.

---

## Continue beat (no fade between beats)

Skip the black sweep transition into the next beat — content stays on screen:

```
CONTINUE:   yes
```

Use when two beats should feel like one continuous scene (e.g. setup → punchline split across beats). **JSON:** `"continue_beat": true`

Set in **Beats** editor checkbox **Continue into next beat**.

---

## Themes

- Pick/create theme **before** new project
- `theme_id` stored on project (e.g. `builtin_orange`)
- Custom themes: upload background (image/GIF/video loop), fonts, palette
- Built-in default: `builtin_orange` → `background/orange_theme_BG.png`

**Style packs:** `course_clean` | `playful` (icon policy; often from theme)

---

## Code demo beats

```
TYPE:       code_demo
LAYOUT:     code_full_card

─── CODE ───
language: python
result: success          # success | error
output: |
  Hello, World!
lines:
  print("Hello, World!")
```

Theme palette wires into code window syntax colors at render time.

---

## Animation IDs (timeline reference)

| ID | Use |
|----|-----|
| `anim_type` | TypeWithCursor (all text) |
| `anim_grow_card` | GrowFromCenter empty card |
| `anim_fade_in` / `anim_fade_out` | Icons / elements |
| `anim_fade_in_on_word` | Icon when trigger word typed |
| `anim_swap_icon` | FadeOut + FadeIn same anchor (joke) |
| `anim_word_red` + `anim_wiggle` | Joke emphasis |
| `anim_indicate` | Highlight word |
| `anim_fade_all` | End of beat |

---

## Per-beat checklist

| Field | Required? | Notes |
|-------|-----------|-------|
| `### BEAT N — slug` | Yes | Unique slug |
| TYPE | Yes | See beat types |
| LAYOUT | Yes | See layouts |
| ICON GRID | If 2–4 icons | auto, horizontal, vertical, triple_*, quad |
| ICON REVEAL | Optional | auto, on_word, together |
| ICON_ENTRANCE | Optional | fade_in, pop_in, slide_*, draw_on, pulse |
| CONTINUE | Optional | yes — skip transition to next beat |
| LABEL + TEXT | Yes | Content sections |
| ICONS | Usually | Skip for `code_demo` |
| CARD | If card layout | SIDE + SIZE |
| EMPHASIS | Optional | word, color, animation |
| CAMERA | If moving | hooks + cam_restore exit |
| HOLD | Yes | Pause before exit (e.g. 1.2s) |

---

## API quick reference

| Endpoint | Purpose |
|----------|---------|
| `GET /api/studio-guide` | This document |
| `GET /api/beat-script-template` | Copy-paste starter script |
| `GET /api/beat-types` | Beat type metadata |
| `GET /api/visual-catalog` | Icon concepts |
| `GET /api/icons/search?q=` | Search Iconify |
| `POST /api/projects/{id}/chat` | AI → beats |
| `POST /api/projects/{id}/script` | Parse script → beats |
| `PUT /api/projects/{id}/beats` | Save beats from editor |
| `GET /api/projects/{id}/script` | Export beats → script |
| `POST /api/projects/{id}/render` | Start preview |
| `POST /api/projects/{id}/export` | Start 1080p60 |

---

## Example prompts (Chat)

- "Create a 3-beat intro: welcome to Python, what is Python?, simple answer with joke."
- "Create a code_demo beat showing a Python decorator."
- "Change beat 2 to use slide_from_right icon entrance and triple_top grid."
- "Make beat 1 continue into beat 2 without fading to black."

---

## Related docs

| File | Purpose |
|------|---------|
| `platform/assets/beat-script-template.md` | Full starter script + examples |
| `.cursor/skills/manim-video/script-template.md` | Agent + Episode hand-authoring |
| `platform/README.md` | Setup and architecture |
| `.cursor/skills/manim-video/reference/cameras/COURSE_GUIDE.md` | Deep camera reference |

---

*Manimations Studio — built by Divyanshu Singh*
