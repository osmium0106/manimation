# Introduction

**Manimations Studio** is a local-first web app for creating Manim course animations without writing Python by hand. Describe beats in natural language or structured scripts — OpenAI structures them, the visual resolver picks Iconify icons, and Manim renders preview and **1080p60** export asynchronously.

**Author:** Divyanshu Singh

## How it works

```
Theme  →  Chat / Beat script  →  Beat JSON  →  Manim preview  →  1080p export
```

1. **Pick a theme** — background, typography, color palette.
2. **Author beats** — Chat, Beat script tab, or Beats editor.
3. **Preview** — async 420p render (`-ql`) with **live progress percentage** and phase (e.g. `23% — Animation 4 (50%)`).
4. **Export** — background 1080p60 render with progress tracking.

Studio does **not** block on renders. Chat and script ingestion save beats immediately; rendering runs in the background.

## Who this is for

- **Course creators** who want repeatable beat-based videos with cards, icons, and typed text.
- **Developers** who want generated Manim code they can tweak in the Code tab.
- **Teams** who need a theme library and project hub without cloud lock-in.

## Key concepts

| Term | Meaning |
|------|---------|
| **Beat** | One idea on screen (~5–8 seconds) — label, text, optional icons, hold, exit |
| **Layout** | Where card and icons sit (`card_right_icon_left`, etc.) |
| **Theme** | Global background + fonts + palette applied at render time |
| **Beat script** | Structured markdown-like format parsed into beat JSON |
| **Visual resolver** | Maps icon descriptions → Iconify refs via GPT + catalog |

## Where data lives

| Path | Contents |
|------|----------|
| `~/manimations-studio/studio.db` | Theme library (SQLite) |
| `~/manimations-studio/themes/{id}/` | Uploaded theme assets |
| `~/manimations-studio/projects/{id}/project.json` | Beats, chat, theme, visuals |
| `~/manimations-studio/projects/{id}/renders/` | Preview and HD MP4s |

Override with `MANIMATIONS_DATA_DIR` in Docker deployments.

## Next steps

- [Quick start](quick-start) — run Studio locally
- [Studio UI](studio-ui) — hub, header docs icon, beat editor tabs, preview toolbar
- [Beat script format](beat-script) — copy-paste template and field reference
