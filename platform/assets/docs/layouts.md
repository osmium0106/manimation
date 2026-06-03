# Layouts

Every beat needs a `LAYOUT` preset that positions the card, text, and icon panel.

## Layout reference

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

## Icon panel side rule

Icons go on the side **opposite** the card:

| Layout prefix | Icon panel |
|---------------|------------|
| `card_right_*` / `text_right_*` | **Left** |
| `card_left_*` / `text_left_*` | **Right** |

## Canvas (16:9)

Origin `(0, 0)` = screen center. Frame **14.22 × 8.0**.

```
┌─────────────────────────────────────────────────────────────┐
│  HEADING ZONE  — yellow label @ top                         │
├──────────────────────┬──────────────────────────────────────┤
│  LEFT PANEL          │  RIGHT PANEL                         │
│  icons / visuals     │  white card OR white text on BG      │
└──────────────────────┴──────────────────────────────────────┘
```

Content centers **below the heading**, not in the full frame height.

## Text placement

| Script syntax | Result |
|---------------|--------|
| `TEXT (card, black):` | Lines inside white card |
| `TEXT (white, on BG):` | No card — white on theme background |
| `LIST (card, checks):` | Checklist in card |

If you use `TEXT (white, on BG)` on a card layout, Studio may promote it to card content automatically.

## Choosing a layout

| Goal | Layout |
|------|--------|
| Standard lesson slide | `card_right_icon_left` |
| Flip card to left for variety | `card_left_icon_right` |
| Big question, one icon | `text_right_icon_left` |
| Compare two ideas | `dual_card` |
| Live code walkthrough | `code_full_card` |

## Script example

```
### BEAT 2 — what_is_python

TYPE:       question
LAYOUT:     text_right_icon_left

─── CONTENT ───
LABEL:
Big Question

TEXT (white, on BG):
So first…
what exactly is Python?
```

## Related

- [Beat types](beat-types)
- [Icon grid](icon-grid)
- [Cards & emphasis](cards-emphasis)
