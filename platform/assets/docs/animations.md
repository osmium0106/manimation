# Animation IDs

Timeline animation reference for beat scripts and hand-authored Manim.

## Text & cards

| ID | Manim | Use for |
|----|-------|---------|
| `anim_type` | `TypeWithCursor` | **Default** — labels, card lines, BG text |
| `anim_grow_card` | `GrowFromCenter` | Empty card only (never with text inside) |

## Icons

| ID | Manim | Use for |
|----|-------|---------|
| `anim_fade_in` | `FadeIn` | Icons — batch reveal |
| `anim_fade_in_on_word` | `FadeIn` per trigger | Icon when trigger word typed |
| `anim_fade_out` | `FadeOut` | Single element |
| `anim_swap_icon` | `FadeOut` + `FadeIn` | Joke icon swap at same anchor |

## Emphasis & exit

| ID | Manim | Use for |
|----|-------|---------|
| `anim_indicate` | `Indicate` | Highlight word (yellow) |
| `anim_word_red` | `set_color(RED)` | Before wiggle on punchline |
| `anim_wiggle` | `Wiggle` | Joke word + matching icon |
| `anim_fade_all` | `FadeOut` group | End of beat |

## Other

| ID | Manim | Use for |
|----|-------|---------|
| `anim_transform` | `ReplacementTransform` | Shape morphs |
| `anim_lagged_in` | `LaggedStart(FadeIn)` | List items |

## Timing helpers

| ID | Duration |
|----|----------|
| `wait_short` | 0.4s |
| `wait_med` | 1.2s |
| `hold` | You set — narration pause before exit (e.g. `HOLD: 1.2s`) |

## Text animation rules

| Element | Animation | Cursor color |
|---------|-----------|--------------|
| Label (yellow) | `anim_type` | White |
| Card lines (black) | `anim_type` | Yellow |
| BG text (white) | `anim_type` | Yellow |
| Code | `anim_type_slow` | Yellow + optional blink |

**Never** pre-add text to the scene before `TypeWithCursor`.

## Icon entrances (batch)

Separate from timeline IDs — set via `ICON_ENTRANCE:` or Beats editor. See [Icon entrances](icon-entrances).

## Related

- [Beat script format](beat-script)
- [Cards & emphasis](cards-emphasis)
- [Camera](camera)
