# Icon reveal

Controls **when** icons appear relative to typed text — all at once or synced to specific words.

## Modes

| Mode | Behavior |
|------|----------|
| `auto` (default) | Word-sync when any icon has `trigger:`; others at end |
| `on_word` | Icons with `trigger` fade in as the word is typed |
| `together` | All icons after text (ignore trigger timing) |

## Script syntax

```
ICON REVEAL:  on_word

─── ICONS ───
icon_mobile: mobile phone icon | color: WHITE | trigger: mobile
icon_web: web browser globe | color: WHITE | trigger: web
icon_desktop: desktop computer | color: WHITE | trigger: desktop
```

**Trigger words must appear in your TEXT lines** — e.g. `mobile, web, and desktop!` on line 2.

## Trigger defaults

If `trigger:` is omitted, Studio derives from icon_id:

- `icon_mobile` → word `mobile`
- `icon_web` → word `web`

## Batch vs word-sync

| `ICON REVEAL` | Result |
|---------------|--------|
| `together` | All icons fade in after text |
| `on_word` | Each `trigger:` icon on that word |
| `auto` | Word-sync if any trigger set; others at end |

## Timeline animation

Word-sync uses `anim_fade_in_on_word` in the timeline — icon FadeIn when the trigger word is typed.

## Multi-icon + camera

With **3–4 icons** and word-sync, camera restores to **full frame** so card + grid stay visible. Requires `CAMERA: moving` at episode level for MovingBeatScene.

## JSON

```json
{
  "icon_reveal": "on_word",
  "visuals": {
    "stack": [
      {"ref": "fe:mobile", "trigger": "mobile", "color": "WHITE"},
      {"ref": "streamline:web-solid", "trigger": "web", "color": "WHITE"}
    ]
  }
}
```

## Related

- [Icon entrances](icon-entrances) — **how** icons animate (batch reveal)
- [Icon grid](icon-grid)
- [Icons](icons)
