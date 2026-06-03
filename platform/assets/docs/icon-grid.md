# Icon grid

When **2–4 icons** appear together, they are placed in an **invisible grid** inside the **icon panel** (half the frame below the heading). No grid lines are drawn.

## Grid values

| Icons | Grid value | Layout |
|-------|------------|--------|
| 1 | `single` | 100% × 100% |
| 2 | `horizontal` (default) | 50% × 100% side by side |
| 2 | `vertical` | 100% × 50% stacked |
| 3 | `triple_top` (default for 3) | 2 top + 1 bottom full width |
| 3 | `triple_bottom` | 1 top full width + 2 bottom |
| 4 | `quad` | 2×2 grid |

## Script syntax

```
ICON GRID:  auto            # pick from icon count (default)
ICON GRID:  horizontal
ICON GRID:  vertical
ICON GRID:  triple_top
ICON GRID:  triple_bottom
ICON GRID:  quad
```

## Joke beats vs grid

| Icons | Behavior |
|-------|----------|
| **2 (joke)** | Primary + swap at punchline — **no grid** |
| **3+** | Grid layout applies |

## Example — three platforms

```
TYPE:       question
LAYOUT:     card_left_icon_right
ICON GRID:  triple_top
ICON REVEAL: on_word

─── CONTENT ───
TEXT (card, black):
Flutter allows you to build apps for
mobile, web, and desktop!

─── ICONS ───
icon_mobile: fe:mobile | color: WHITE | trigger: mobile
icon_web: streamline:web-solid | color: WHITE | trigger: web
icon_desktop: boxicons:desktop-filled | color: WHITE | trigger: desktop
```

Card on **left**, 2+1 icon grid on **right**.

## JSON

```json
{
  "icon_grid": "triple_top",
  "layout": "card_left_icon_right"
}
```

## Related

- [Icon reveal](icon-reveal)
- [Layouts](layouts)
- [Camera](camera) — full-frame restore during 3–4 icon word-sync
