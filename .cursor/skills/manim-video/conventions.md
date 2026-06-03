# Project conventions (manimations repo)

Manim Community Edition **v0.20.1** only. Do not use ManimGL or 3b1b/manim APIs.

**Manimations Studio** (Divyanshu Singh): see `platform/assets/docs/` or `/docs` in browser — header book icon. Beat editor tabs: Content, Icon, Emphasis, Camera.

## Repo layout

| Path | Purpose |
|------|---------|
| `animations/*.py` | One scene class per file |
| `background/` | PNG backgrounds and icons |
| `media/videos/` | Rendered output |
| `.cursor/skills/manim-video/` | Agent skill + Manim docs |

## Scene template

```python
from manim import *

class MyScene(Scene):
    def construct(self):
        # orange BG → beat methods → TypeWithCursor for text
        self.wait(1)
```

Use plain `Scene` by default. **No camera zoom** unless the user explicitly asks.

## Visual style (AI course videos)

### Visual style (default theme: `builtin_orange`)

These values are the **built-in default theme** in Manimations Studio. Custom themes override background, typography, and palette at render time.

- **Background:** `background/orange_theme_BG.png` (default; image, GIF, or looping video per theme)
- **50/50 split:** left half = visual/animation, right half = white card (with margin)
- Alternate card to **left** on some beats for variety
- **No card:** short questions — white text directly on orange BG (right half)
- **Labels:** yellow, top edge (`to_edge(UP)`)
- **Text on cards:** black, left-aligned inside card
- **One accent color only:** yellow for labels/highlights

### Text animation
- Use **`TypeWithCursor`** with yellow cursor for all text (not `Write`)
- Code: `TypeWithCursor` on `Text(..., font="Courier New")` — or **`code_demo`** beat type in Studio (full code card + output panel)
- After typing: optional `Blink(cursor, blinks=2)`

### Other animations

| Content | Animation |
|---------|-----------|
| White card | `GrowFromCenter` |
| PNG/images | `FadeIn` |
| List items | `LaggedStart(FadeIn(...))` |
| Shape morph | `ReplacementTransform` (e.g. circle→square) |
| Exit beat | `fade_clear(...)` |
| Emphasis | `Indicate`, `Wiggle` |

## Text → Manim

When user gives narration or beats, follow [text-to-manim.md](text-to-manim.md) (from [manim-video-generator](https://github.com/rohitg00/manim-video-generator)).

Golden implementation: `animations/intro_python_hello_world.py`

## Quality flags

| Flag | Use |
|------|-----|
| `-ql` | Fast validation (480p15) |
| `-qh` | Final export (1080p60) |

```bash
.cursor/skills/manim-video/scripts/validate.sh animations/my_scene.py MyScene
manim -qh animations/my_scene.py MyScene
```

## Common pitfalls

- `DrawBorderThenFill` is for vectors, not PNG `ImageMobject`
- Do not use camera zoom on every beat
- Do not mix random text colors on the same card
- All `self.play()` inside `construct()`
