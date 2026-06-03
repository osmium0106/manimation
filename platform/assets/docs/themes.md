# Themes

Global visual identity applied to every render in a project.

## Before you create a project

Studio requires a **theme** before the first beat:

- Background image, GIF, or looping video
- Typography (label + body fonts)
- Optional color palette (code window, accents)

Themes are **global** on the server — stored in SQLite + `~/manimations-studio/themes/{id}/`.

## Built-in default

| ID | Background |
|----|------------|
| `builtin_orange` | `background/orange_theme_BG.png` |

## Custom themes

Create from the theme gate or theme editor:

1. Upload background asset
2. Set name and optional palette
3. Save — `theme_id` assigned

Switch themes per project from the header dropdown. Re-render to apply.

## Style packs

```
STYLE_PACK:  course_clean    # course_clean | playful
```

Icon policy and visual density — often inherited from theme. Affects resolver behavior.

## Project storage

```json
{
  "theme_id": "builtin_orange",
  "style_pack": "course_clean"
}
```

Episode meta in beat script:

```
THEME:       builtin_orange
STYLE_PACK:  course_clean
```

## Code demo theming

Theme palette wires into code editor window colors (background, gutter, syntax) at render time.

## API

| Endpoint | Purpose |
|----------|---------|
| `GET /api/themes` | List themes |
| `POST /api/themes` | Create theme |
| `GET /api/themes/{id}` | Theme detail |
| `PATCH /api/themes/{id}` | Update theme |

## Related

- [Quick start](quick-start)
- [Code demo beats](code-demo)
- [Studio UI](studio-ui)
