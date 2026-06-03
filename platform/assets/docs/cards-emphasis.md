# Cards & emphasis

White cards, text variants, sizes, and highlighted words.

## CARD section

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

## Card rules

- White background, rounded corners, **black** text, left-aligned
- **Grow empty card first** — never `GrowFromCenter(card + text)` (text would appear instantly)
- Each line typed separately with `TypeWithCursor` + yellow cursor on card

## Text variants

| Syntax | Use |
|--------|-----|
| `TEXT (card, black):` | Standard card content |
| `TEXT (white, on BG):` | No card — question beats |
| `LIST (card, checks):` | Checklist with checkmarks |

## Emphasis

Highlight a word during or after typing:

```
─── EMPHASIS ───
word: screaming | color: #FC6255 | animation: wiggle
word: Python | color: #FFD700 | animation: indicate
```

| Field | Effect |
|-------|--------|
| **word** | Must appear in beat text (Content tab); skipped silently if not found |
| **color** | Named (`RED`, `YELLOW`, `BLUE`) or hex (`#FC6255`) — recolors the word |
| **animation** | `indicate` = pulse highlight; `wiggle` = wiggle (jokes, punchlines) |

### Beats editor — Emphasis tab

- Add/remove emphasis rows
- **Color swatch** opens full hex picker (same UI as icon color)
- Warning shown if word is not found in beat text
- Timeline badge `E{n}` shows emphasis count per beat

## JSON

```json
{
  "card_side": "right",
  "card_width": 5.6,
  "card_height": 5.0,
  "emphasis": [
    {"word": "Python", "color": "#FFD700", "animation": "indicate"}
  ]
}
```

## Related

- [Layouts](layouts)
- [Beat types](beat-types)
- [Studio UI](studio-ui)
- [Animations](animations)
