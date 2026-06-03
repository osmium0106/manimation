# Beat types

Each beat has a `TYPE` that controls content structure and default pacing.

| TYPE | Pattern |
|------|---------|
| `statement` | Card + icon(s), normal reveal |
| `question` | Single icon: white text on BG, no card. Multi-icon: card + grid |
| `joke` / `joke punchline` | Setup lines + punchline; **2 icons** (primary + swap) |
| `explain` | Card + tool icon (terminal, code) |
| `recap` | Summary card, optional multi-icon grid |
| `list` | Checklist card — use `LIST (card, checks):` |
| `compare` | Two cards (`dual_card`) — good vs bad, before vs after |
| `code_demo` | Full-width code editor + output panel |

## statement

Default teaching beat. Yellow label, white card with black typed lines, one or more icons on the opposite panel.

```
TYPE: statement
LAYOUT: card_right_icon_left
```

## question

Two patterns:

**No card** — single large icon + white text on theme background:

```
TYPE: question
LAYOUT: text_right_icon_left
TEXT (white, on BG):
So first…
what exactly is Python?
```

**With card + multi-icon** — list platforms or options:

```
TYPE: question
LAYOUT: card_left_icon_right
ICON GRID: triple_top
ICON REVEAL: on_word
```

## joke / joke punchline

Setup lines in card text; last line is punchline (may replace earlier lines visually). **Exactly 2 icons:**

1. **Primary** — shows during setup
2. **Swap** — fades in at punchline (same anchor)

```
TYPE: joke punchline
─── EMPHASIS ───
word: screaming | color: RED | animation: wiggle
```

## list

Checklist items with checkmarks:

```
TYPE: list
LIST (card, checks):
Install Python
Write your first script
Run hello world
```

## compare

Two cards side by side via `dual_card` layout — before/after, good/bad, etc.

## code_demo

See [Code demo beats](code-demo) — no icons required.

## JSON

```json
{
  "label": "Welcome to Python",
  "type": "statement",
  "layout": "card_right_icon_left",
  "card_lines": ["Today we meet Python…"],
  "hold": 1.2
}
```

## Related

- [Layouts](layouts)
- [Icons](icons)
- [Beat script format](beat-script)
