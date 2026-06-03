# Icon entrances

Controls **how** icons animate when they appear in batch — primary icon, `together` reveal, or joke primary before swap.

> Word-sync icons (`ICON REVEAL: on_word`) use per-word FadeIn timing. `ICON_ENTRANCE` applies to batch reveals.

When **moving camera** is on, the frame pans to the icon panel **before** the entrance animation runs.

## All options

| Value | Effect |
|-------|--------|
| `fade_in` | **Default** — FadeIn with slight scale |
| `pop_in` | Scale from small with FadeIn |
| `slide_from_left` | Enters from the left panel edge |
| `slide_from_right` | Enters from the right panel edge |
| `pulse` | FadeIn then subtle scale pulse |
| `none` | Instant — no entrance animation |
| `draw_on` | Treated as `fade_in` (Lucide/SVG-safe) |

## Beat script

```
ICON_ENTRANCE: pop_in
```

Place after `LAYOUT` in the beat header block.

## Beats editor

Select beat → **Icon** tab → **Icon entrance** dropdown. The icon picker fills the tab with catalog search, Iconify results, SVG/PNG upload, and hex color.

## JSON

```json
{
  "icon_entrance": "slide_from_left"
}
```

## When each works best

| Entrance | Good for |
|----------|----------|
| `fade_in` | General purpose, subtle |
| `pop_in` | Brand logos, celebrations |
| `slide_from_left` / `slide_from_right` | Icons entering from their panel side |
| `pulse` | Attention on a single important icon |
| `none` | Cut immediately to final icon state |

## Related

- [Icon reveal](icon-reveal) — **when** icons appear
- [Icons](icons) — colors and catalog
- [Camera](camera) — pan before entrance
- [Animations](animations)
