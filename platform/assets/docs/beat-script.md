# Beat script format

Structured text format for the **Beat script** tab. Studio parses each `### BEAT` block into JSON — rendering is separate.

Download the full starter: **View template** in Beat script tab, or `GET /api/beat-script-template`.

## Episode meta (top of file, once)

```
CAMERA:      moving          # none | moving
THEME:       builtin_orange
STYLE_PACK:  course_clean
NAME:        Your Episode Title
```

## Beat block structure

```
### BEAT 1 — short_slug

TYPE:       statement
LAYOUT:     card_right_icon_left
ICON GRID:  auto              # optional
ICON REVEAL: auto              # optional
ICON_ENTRANCE: fade_in         # optional
CONTINUE:   yes                # optional
CAMERA:     moving              # optional
DURATION:   ~6s                 # optional hint

─── CONTENT ───
LABEL:
Your Yellow Heading

TEXT (card, black):
Line one
Line two

─── ICONS ───
icon_primary: Python logo | color: #3776AB

─── CARD ───
SIDE: right | SIZE: 5.6 × 5.0

─── EMPHASIS ───
word: keyword | color: YELLOW | animation: indicate

─── CAMERA ───
cam_focus_right: after_line_1
cam_restore: exit

HOLD: 1.2s
EXIT: anim_fade_all
```

## Beats editor (visual)

Same fields as the script, organized in tabs — see [Studio UI](studio-ui):

- **Content** — type, layout, text lines, hold, continue beat
- **Icon** — entrance + picker (catalog, Iconify, upload, hex color)
- **Emphasis** — word, hex color, animation
- **Camera** — per-beat toggle, steps, load type defaults

Saving beats syncs back to this script format via `GET /api/projects/{id}/script`.

## Per-beat checklist

| Field | Required? | Notes |
|-------|-----------|-------|
| `### BEAT N — slug` | Yes | Unique slug per beat |
| TYPE | Yes | See [Beat types](beat-types) |
| LAYOUT | Yes | See [Layouts](layouts) |
| ICON GRID | If 2–4 icons | auto, horizontal, vertical, triple_*, quad |
| ICON REVEAL | Optional | auto, on_word, together |
| ICON_ENTRANCE | Optional | fade_in, pop_in, slide_*, pulse, none |
| CONTINUE | Optional | yes — skip transition to next beat |
| LABEL + TEXT | Yes | Content sections |
| ICONS | Usually | Skip for `code_demo` |
| CARD | If card layout | SIDE + SIZE |
| EMPHASIS | Optional | word, color, animation |
| CAMERA | If moving | hooks + `cam_restore: exit` |
| HOLD | Yes | Pause before exit (e.g. 1.2s) |

## JSON alternative

Paste directly in Beat script tab:

```json
{
  "name": "Python Intro",
  "theme_id": "builtin_orange",
  "beats": [
    {
      "label": "Welcome",
      "type": "statement",
      "layout": "card_right_icon_left",
      "card_lines": ["Hello, world!"],
      "icon_entrance": "pop_in",
      "hold": 1.2
    }
  ]
}
```

## Icon patterns at a glance

| Pattern | Icons | Layout | ICON REVEAL |
|---------|-------|--------|-------------|
| Single brand | 1 | `card_right_icon_left` | — |
| Joke swap | 2 | `card_right_icon_left` | — (swap at punchline) |
| Multi grid | 2–4 | `card_left_icon_right` | `together` |
| Word-sync list | 2–4 | `card_left_icon_right` | `on_word` + `trigger:` |
| Question (no card) | 1 | `text_right_icon_left` | — |

## Related

- [Icons](icons) · [Icon grid](icon-grid) · [Icon reveal](icon-reveal) · [Icon entrances](icon-entrances)
- [Camera](camera) · [Continue beat](continue-beat)
