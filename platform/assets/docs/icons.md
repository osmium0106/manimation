# Icons

How to specify icons in beat scripts, the Beats editor, and JSON.

## ICONS section (beat script)

Each line:

```
icon_id: description or fa6-brands:ref | color: WHITE | scale: 1.2 | trigger: word
```

| Part | Meaning |
|------|---------|
| **icon_id** | Local name (`icon_python`, `shape_question`) |
| **description** | Plain English — GPT searches Iconify |
| **color** | `WHITE`, `#3776AB`, hex, or `ORIGINAL` for full-color icons |
| **scale** | Optional (default 1.2) |
| **trigger** | Optional — word in TEXT that reveals this icon |

## Slot order

| Icons listed | Behavior |
|--------------|----------|
| 1 | Single icon — fills icon panel |
| 2 (joke) | 1st = primary, 2nd = swap at punchline |
| 2–4 (multi) | Grid in icon panel; optional word-sync |

## Examples

Describe + color (GPT picks Iconify):

```
icon_python: Python programming language logo | color: #3776AB
icon_scream: screaming panicked emoji face | color: WHITE
shape_question: large question mark help circle | color: WHITE | scale: 1.8
```

Explicit Iconify refs:

```
icon_python: fa6-brands:python | color: #3776AB
icon_mobile: fe:mobile | color: WHITE | trigger: mobile
```

Icons download from Iconify at render time. Cached under `assets/icons/cache/`.

## Beats editor — Icon tab

1. Select a beat in the timeline
2. Open the **Icon** tab (full-height picker)
3. Search catalog concepts or Iconify (`python`, `terminal`, …)
4. Upload custom **SVG or PNG** via the upload button in the search row
5. Click the **color swatch** for full hex picker (saturation, hue, RGB)
   - Lucide/mono icons: white outline + your tint
   - Colorful icons (emoji, brands): use **ORIGINAL** or pick a tint

## Visual catalog

- File: `assets/visual_catalog.json`
- API: `GET /api/visual-catalog`
- Search: `GET /api/icons/search?q=python`

## Validation

`validate-beats` warns if icons fail to resolve before render. Fix in Beats tab or paste explicit refs.

## Related

- [Icon grid](icon-grid)
- [Icon reveal](icon-reveal)
- [Icon entrances](icon-entrances)
- [Studio UI](studio-ui)
