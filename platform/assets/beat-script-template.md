# Beat Script Template — Manimations Studio

**Author:** Divyanshu Singh  
**Full option reference:** `/docs` in browser · `platform/assets/docs/` · Beat editor UI

Use this file in the **Beat script** tab. Studio **parses** every section into beat JSON — rendering is a **separate async step** (preview auto-starts after Generate; use **Re-render** to refresh).

---

## How to use

1. Select a **theme** before creating your project (background, typography, palette).
2. Click **View template** or **Download** in the Beat script tab.
3. Copy the **STARTER SCRIPT** block below (from episode meta through your beats).
4. Paste into the Beat script editor.
5. Fill in placeholders — one `### BEAT` block per idea (~5–8 seconds each).
6. **Icons:** describe what you want + color — GPT picks the Iconify icon when you click **Generate**. Or paste explicit refs (`fa6-brands:flutter`).
7. Click **Generate from script** — saves beats; preview render runs in the background. Use **Use AI author** only for rough narration → full script.

**Rules**

- Episode meta goes at the **top** (once).
- Every beat needs: TYPE, LAYOUT, CONTENT, ICONS, HOLD.
- Card beats: add CARD section + `TEXT (card, black)` → card on left or right per LAYOUT.
- **Multi-icon beats:** list up to **4 icons** — grid in icon panel; optional **word-sync** when `trigger:` is set (see ICON REVEAL).
- Question beats (single icon): `text_right_icon_left` + `TEXT (white, on BG)` — no card.
- Card + multi-icon: use `card_left_icon_right` or `card_right_icon_left` + `TEXT (card, black)`.
- Joke beats: setup lines in TEXT, last line as punchline; **exactly 2 icons** (primary + swap); EMPHASIS wiggle on punchline word.
- Camera beats: set `CAMERA: moving` (meta + beat) and add CAMERA hooks; always end with `cam_restore: exit`.
- Icon panel side: `card_right_*` / `text_right_*` → icons on **left**. `card_left_*` / `text_left_*` → icons on **right**.
- **Icon entrance:** optional `ICON_ENTRANCE:` per beat — `fade_in`, `pop_in`, `slide_from_left`, `slide_from_right`, `draw_on`, `pulse`.
- **Continue beat:** optional `CONTINUE: yes` — skip black transition into the next beat.

### Icon patterns at a glance

| Pattern | Icons | Layout | ICON REVEAL | When |
|---------|-------|--------|-------------|------|
| Single brand | 1 | `card_right_icon_left` | — | One logo + card |
| Joke swap | 2 | `card_right_icon_left` | — | Primary → swap at punchline |
| Multi grid | 2–4 | `card_left_icon_right` | `together` | All icons after text |
| Word-sync list | 2–4 | `card_left_icon_right` | `on_word` + `trigger:` | Icon per spoken word |
| Question (no card) | 1 | `text_right_icon_left` | — | White text + one icon |

**Important:** trigger words (e.g. `mobile`, `web`, `desktop`) must appear in your **TEXT** lines.

---

## STARTER SCRIPT — copy from here ↓

```
CAMERA:      moving          # none | moving
THEME:       builtin_orange  # theme id from theme library
STYLE_PACK:  course_clean    # course_clean | playful (usually from theme)
NAME:        Your Episode Title


### BEAT 1 — short_slug_name

TYPE:       statement          # statement | question | joke punchline | explain | recap
DURATION:   ~6s
LAYOUT:     card_right_icon_left
ICON_ENTRANCE: fade_in        # fade_in | pop_in | slide_from_left | slide_from_right | draw_on | pulse
CAMERA:     moving             # moving | none

─── TIMELINE ───
| t (s) | Element           | Action                              |
|-------|-------------------|-------------------------------------|
| 0.0   | LABEL             | anim_type, white cursor             |
| 0.3   | ui_card (empty)   | anim_grow_card @ right              |
| 0.7   | line 1            | anim_type                           |
| 1.5   | line 2            | anim_type                           |
| 2.5   | icon_primary      | anim_fade_in @ left                 |
| 4.0   | HOLD              | wait_med 1.2s                       |
| 5.0   | ALL               | anim_fade_all                       |

─── CONTENT ───
LABEL:
Your Yellow Heading Here

TEXT (card, black):
First line of card text
Second line of card text
Optional third line

─── ICONS ───
icon_primary: sparkles celebration icon | color: WHITE
# icon_swap: screaming panicked emoji face | color: WHITE   # optional 2nd icon for punchline

─── CARD ───
SIDE: right | SIZE: 5.6 × 5.0

─── EMPHASIS ───
word: keyword | color: YELLOW | animation: indicate

─── CAMERA ───
cam_focus_right: after_line_1
cam_focus_left: after_icon
cam_restore: exit

HOLD: 1.2s
EXIT: anim_fade_all


### BEAT 2 — what_can_you_build

TYPE:       question
DURATION:   ~5s
LAYOUT:     card_left_icon_right
ICON GRID:  triple_top
ICON REVEAL: on_word
CAMERA:     none

─── TIMELINE ───
| t (s) | Element           | Action                              |
|-------|-------------------|-------------------------------------|
| 0.0   | LABEL             | anim_type                           |
| 0.3   | ui_card (empty)   | anim_grow_card @ left               |
| 0.7   | line 1            | anim_type                           |
| 1.5   | line 2            | anim_type — icon on each word       |
| 1.6   | icon_mobile       | anim_fade_in on "mobile"            |
| 1.9   | icon_web          | anim_fade_in on "web"               |
| 2.2   | icon_desktop      | anim_fade_in on "desktop"           |
| 3.5   | HOLD              | wait_med 1.2s                       |

─── CONTENT ───
LABEL:
What Can You Build?

TEXT (card, black):
Flutter allows you to build apps for
mobile, web, and desktop!

─── ICONS ───
icon_mobile: fe:mobile | color: WHITE | trigger: mobile
icon_web: streamline:web-solid | color: WHITE | trigger: web
icon_desktop: boxicons:desktop-filled | color: WHITE | trigger: desktop

─── CARD ───
SIDE: left | SIZE: 5.6 × 5.0

HOLD: 1.2s
EXIT: anim_fade_all


### BEAT 3 — another_beat_slug

TYPE:       question
DURATION:   ~5s
LAYOUT:     text_right_icon_left
CAMERA:     moving

─── TIMELINE ───
| t (s) | Element           | Action                              |
|-------|-------------------|-------------------------------------|
| 0.0   | LABEL             | anim_type                           |
| 0.3   | shape_question    | anim_fade_in @ left                 |
| 0.8   | line 1            | anim_type @ right                   |
| 2.0   | line 2            | anim_type                           |
| 3.0   | HOLD              | wait_med 1.2s                       |

─── CONTENT ───
LABEL:
Your Question Label

TEXT (white, on BG):
First question line
Second question line?

─── ICONS ───
shape_question: large question mark help circle | color: WHITE | scale: 1.8

─── EMPHASIS ───
word: keyword | color: YELLOW | animation: indicate

─── CAMERA ───
cam_focus_left: after_icon
cam_focus_right: after_line_1
cam_restore: exit

HOLD: 1.2s
EXIT: anim_fade_all
```

---

## ICONS section — describe + color (GPT picks the icon)

Each line:

```
icon_id: description or fa6-brands:ref | color: WHITE | scale: 1.2 | trigger: word
```

| Part | Meaning |
|------|---------|
| **icon_id** | Local name (`icon_python`, `icon_mobile`, `shape_question`) |
| **description** | Plain English — GPT searches Iconify (or paste `prefix:name` ref) |
| **color** | `WHITE`, `BLUE`, `#3776AB`, etc. |
| **scale** | Optional (default 1.2) |
| **trigger** | Optional — word in TEXT that reveals this icon (`trigger: mobile`) |

**Slot order**

| Icons listed | Behavior |
|--------------|----------|
| 1 | Single icon — fills icon panel |
| 2 (joke) | 1st = primary, 2nd = swap at punchline |
| 2–4 (multi) | Grid in icon panel; optional word-sync with `trigger:` |

**Examples (you write these — no Iconify lookup needed)**

```
icon_python: Python programming language logo | color: #3776AB
icon_scream: screaming panicked emoji face | color: WHITE
icon_terminal: command line terminal | color: WHITE
shape_question: question mark help circle | color: WHITE | scale: 1.8
icon_mobile: mobile phone icon | color: WHITE
icon_web: web browser globe icon | color: WHITE
icon_desktop: desktop computer icon | color: WHITE
```

**Advanced (explicit Iconify + triggers):**

```
icon_python: fa6-brands:python | color: #3776AB
icon_mobile: fe:mobile | color: WHITE | trigger: mobile
icon_web: streamline:web-solid | color: WHITE | trigger: web
icon_desktop: boxicons:desktop-filled | color: WHITE | trigger: desktop
```

Icons download from Iconify at render time after GPT resolves your description.

---

## ICON GRID (multi-icon panel, max 4)

When **2–4 icons** appear together, they are placed in an **invisible grid** inside the **icon panel** (half the frame below the heading — not the full page). No grid lines are drawn.

| Icons | Default | Layout |
|-------|---------|--------|
| 1 | `single` | 100% × 100% |
| 2 | `horizontal` | 50% × 100% side by side |
| 2 | `vertical` | 100% × 50% stacked |
| 3 | `triple_top` | 2 top + 1 bottom (full width) |
| 3 | `triple_bottom` | 1 top (full width) + 2 bottom |
| 4 | `quad` | 2×2 grid |

Optional per beat (auto if omitted):

```
ICON GRID:  auto            # pick from icon count (default)
ICON GRID:  horizontal
ICON GRID:  vertical
ICON GRID:  triple_top
ICON GRID:  triple_bottom
ICON GRID:  quad
```

**Joke beats:** use exactly **2 icons** — primary shows first, swap at punchline (no grid). **3+ icons** use the grid.

---

## ICON REVEAL (word-synced icons)

Icons can appear **when their word is typed** instead of all at once.

| Mode | Behavior |
|------|----------|
| `auto` (default) | Word-sync when any icon has `trigger:`; others at end |
| `on_word` | Icons with `trigger` fade in as the word is typed |
| `together` | All icons after text (ignore trigger timing) |

```
ICON REVEAL:  on_word

─── ICONS ───
icon_mobile: fe:mobile | color: WHITE | trigger: mobile
icon_web: streamline:web-solid | color: WHITE | trigger: web
icon_desktop: boxicons:desktop-filled | color: WHITE | trigger: desktop
```

**Trigger defaults:** `icon_mobile` → word `mobile` (from icon_id if `trigger:` omitted).

**3–4 icon word-sync:** camera restores to **full frame** so card + icon grid stay visible during sync. Use `CAMERA: moving` at episode level for MovingBeatScene; static beats are already full frame.

**Batch vs word-sync:**

| `ICON REVEAL` | Result |
|---------------|--------|
| `together` | All icons fade in after text (ignore trigger timing) |
| `on_word` | Each `trigger:` icon appears when that word is typed |
| `auto` (default) | Word-sync if any icon has `trigger:`; others at end |

---

## ICON ENTRANCE (how icons appear)

Per-beat animation when icons are revealed in batch (not word-sync). Also editable in the **Beats** tab.

```
ICON_ENTRANCE: pop_in
```

| Value | Effect |
|-------|--------|
| `fade_in` | **Default** — gentle FadeIn |
| `pop_in` | GrowFromCenter from near-zero |
| `slide_from_left` | Slide in from left panel edge |
| `slide_from_right` | Slide in from right panel edge |
| `draw_on` | Stroke draws on (Create) |
| `pulse` | Fade in + subtle scale pulse |

Word-sync icons (`ICON REVEAL: on_word`) use per-word timing; `ICON_ENTRANCE` applies to primary/batch/`together` reveals.

---

## CONTINUE (skip beat transition)

Keep the scene visible into the next beat — no black sweep between them:

```
CONTINUE:   yes
```

Use for multi-part jokes or continuous explanations split across beats. Set in **Beats** editor or JSON: `"continue_beat": true`.

---

## LAYOUT presets

| Layout ID | When to use |
|-----------|-------------|
| `card_right_icon_left` | **Default** — white card right, icon(s) left |
| `card_left_icon_right` | Card left, icon(s) right |
| `text_right_icon_left` | Single icon — white text on orange, no card |
| `text_left_icon_right` | White text left, icon(s) right |
| `card_right_only` | Card only, no icon |
| `card_left_only` | Card only, no icon |
| `dual_card` | Cards both sides (compare beats) |
| `code_full_card` | Full-width code editor + output panel (`code_demo`) |

**Icon panel side:** icons go on the side **opposite** the card — `card_left_*` → icons **right**, `card_right_*` → icons **left**.

---

## TYPE guide

| TYPE | Pattern |
|------|---------|
| `statement` | Card + icon(s), normal reveal |
| `question` | Single icon: `text_right_icon_left`, no card. Multi-icon + card: `card_left_icon_right` |
| `joke` / `joke punchline` | Setup lines + separate punchline; **2 icons** (primary + swap) + wiggle |
| `explain` | Card + tool icon (terminal, code) |
| `recap` | Summary card, optional multi-icon grid |
| `list` | Checklist card + optional icon — use `LIST (card, checks):` |
| `compare` | Two cards (`dual_card`) — good vs bad, before vs after |
| `code_demo` | Full-width code card — use `─── CODE ───` block (no ICONS required) |

---

## CODE section (`code_demo` beats)

Use with `TYPE: code_demo` and `LAYOUT: code_full_card`.

```
─── CODE ───
language: python
result: success          # success | error
output: |
  Hello, World!
lines:
  print("Hello, World!")
  print("Done")
```

Error example:

```
─── CODE ───
language: python
result: error
error_line: 2
error: NameError: name 'y' is not defined
output: |
  NameError: name 'y' is not defined
lines:
  x = 1
  print(y)
```

---

## ANIMATION IDs (timeline)

| ID | Use |
|----|-----|
| `anim_type` | TypeWithCursor (all text) |
| `anim_grow_card` | GrowFromCenter empty card |
| `anim_fade_in` / `anim_fade_out` | Icons / elements (batch) |
| `anim_fade_in_on_word` | Icon when trigger word is typed |
| `anim_swap_icon` | FadeOut + FadeIn same anchor |
| `anim_word_red` + `anim_wiggle` | Joke emphasis |
| `anim_indicate` | Highlight word (YELLOW) |
| `anim_fade_all` | End of beat |

---

## CAMERA IDs (when CAMERA: moving)

| ID | Hook |
|----|------|
| `cam_focus_left` | `after_icon` |
| `cam_focus_right` | `after_line_1`, `after_line_2`, … |
| `cam_focus_card` | `punchline` |
| `cam_restore` | **`exit`** (required every beat) |

---

## CARD sizes

| SIZE | Use |
|------|-----|
| 5.6 × 5.0 | 4–5 lines + punchline |
| 5.6 × 4.6 | 3–4 lines |
| 5.6 × 3.8 | 2–3 short lines |
| 5.0 × 2.8 | 1–2 lines |

---

## FILLED EXAMPLES (reference)

### BEAT 1 — welcome_to_python (joke + icon swap)

```
### BEAT 1 — welcome_to_python

TYPE:       statement | joke punchline
DURATION:   ~6s
LAYOUT:     card_right_icon_left
CAMERA:     moving

─── CONTENT ───
LABEL:
Welcome to Python for AI

TEXT (card, black):
Today, we meet Python…
the programming language
that helps humans
talk to computers.
Without screaming too much.

─── ICONS ───
icon_python: Python programming language brand logo | color: #3776AB
icon_scream: screaming panicked emoji face | color: WHITE

─── CARD ───
SIDE: right | SIZE: 5.6 × 5.0

─── EMPHASIS ───
word: screaming | color: RED | animation: wiggle

─── CAMERA ───
cam_focus_right: after_line_2
cam_focus_left: after_icon
cam_focus_card: punchline
cam_restore: exit

HOLD: 1.2s
```

### BEAT 2 — what_can_you_build (multi-icon + card left)

```
### BEAT 2 — what_can_you_build

TYPE:       question
LAYOUT:     card_left_icon_right
ICON GRID:  triple_top
ICON REVEAL: on_word
CAMERA:     none

─── CONTENT ───
LABEL:
What Can You Build?

TEXT (card, black):
Flutter allows you to build apps for
mobile, web, and desktop!

─── ICONS ───
icon_mobile: fe:mobile | color: WHITE | trigger: mobile
icon_web: streamline:web-solid | color: WHITE | trigger: web
icon_desktop: boxicons:desktop-filled | color: WHITE | trigger: desktop

─── CARD ───
SIDE: left | SIZE: 5.6 × 5.0

HOLD: 1.2s
```

Icons on the **right** (2+1 grid). Each fades in when its word is typed on line 2. Use `ICON REVEAL: together` to show all three icons at once after text instead.

### BEAT 2b — what_is_python (question, no card, single icon)

```
### BEAT 2 — what_is_python

TYPE:       question
LAYOUT:     text_right_icon_left
CAMERA:     moving

─── CONTENT ───
LABEL:
Big Question

TEXT (white, on BG):
So first…
what exactly is Python?

─── ICONS ───
shape_question: large question mark help circle | color: WHITE | scale: 1.8

─── EMPHASIS ───
word: Python | color: YELLOW | animation: indicate

─── CAMERA ───
cam_focus_left: after_icon
cam_focus_right: after_line_1
cam_restore: exit

HOLD: 1.2s
```

### BEAT 3 — simple_answer (statement + indicate)

```
### BEAT 3 — simple_answer

TYPE:       statement
LAYOUT:     card_right_icon_left
CAMERA:     moving

─── CONTENT ───
LABEL:
Simple Answer

TEXT (card, black):
Python is a programming language.
We write instructions,
and the computer follows them.
Usually.

─── ICONS ───
icon_terminal: command line terminal icon | color: WHITE

─── EMPHASIS ───
word: programming language | color: YELLOW | animation: indicate
word: Usually | color: RED | animation: wiggle

─── CARD ───
SIDE: right | SIZE: 5.6 × 4.6

─── CAMERA ───
cam_focus_card: after_line_1
cam_focus_left: after_icon
cam_restore: exit

HOLD: 1.2s
```

---

## Fields checklist (per beat)

| Section | Required? | Notes |
|---------|-----------|-------|
| `### BEAT N — slug` | Yes | Unique slug per beat |
| TYPE | Yes | statement, question, joke, code_demo, list, compare, explain, recap |
| LAYOUT | Yes | See layout table (incl. `code_full_card`) |
| ICON GRID | If 2–4 icons together | auto, horizontal, vertical, triple_top, triple_bottom, quad |
| ICON REVEAL | Optional | auto, on_word, together |
| ICON_ENTRANCE | Optional | fade_in, pop_in, slide_from_left, slide_from_right, draw_on, pulse |
| CONTINUE | Optional | yes — no fade transition to next beat |
| CONTENT / LABEL | Yes | Yellow top heading |
| CONTENT / TEXT | Yes | `TEXT (card, black)`, `TEXT (white, on BG)`, `LIST (card, checks):`, or `─── CODE ───` |
| ICONS | Usually | 1–4 icons — skip for `code_demo` |
| CARD | If card layout | SIDE + SIZE |
| EMPHASIS | If highlight word | word, color, animation |
| CAMERA | If moving | hooks + cam_restore exit |
| HOLD | Yes | Pause before exit (e.g. 1.2s) |

---

## JSON alternative (advanced)

```json
{
  "name": "Python Foundation Intro",
  "theme_id": "builtin_orange",
  "style_pack": "course_clean",
  "use_camera": true,
  "beats": [
    {
      "label": "Run Your Code",
      "type": "code_demo",
      "layout": "code_full_card",
      "code_lines": ["print('Hello, World!')"],
      "code_output": "Hello, World!",
      "code_result": "success"
    },
    {
      "label": "What Can You Build?",
      "type": "question",
      "layout": "card_left_icon_right",
      "icon_grid": "triple_top",
      "icon_reveal": "on_word",
      "card_lines": ["Flutter allows you to build apps for", "mobile, web, and desktop!"],
      "card_side": "left",
      "icons": {
        "icon_mobile": "fe:mobile",
        "icon_web": "streamline:web-solid",
        "icon_desktop": "boxicons:desktop-filled"
      },
      "visuals": {
        "stack": [
          {"ref": "fe:mobile", "trigger": "mobile", "color": "WHITE"},
          {"ref": "streamline:web-solid", "trigger": "web", "color": "WHITE"},
          {"ref": "boxicons:desktop-filled", "trigger": "desktop", "color": "WHITE"}
        ]
      },
      "hold": 1.2
    },
    {
      "label": "Welcome to Python for AI",
      "type": "joke punchline",
      "layout": "card_right_icon_left",
      "card_lines": ["Today, we meet Python…", "the programming language", "that helps humans", "talk to computers."],
      "punchline_line": "Without screaming too much.",
      "visuals": {
        "primary": {"concept": "python", "description": "Python programming language brand logo", "color": "#3776AB"},
        "swap": {"concept": "frustration", "description": "screaming panicked emoji face", "trigger": "screaming", "color": "WHITE"}
      },
      "emphasis": [{"word": "screaming", "color": "RED", "animation": "wiggle"}],
      "hold": 1.2
    }
  ]
}
```

Visual concepts (catalog fallback if GPT unavailable): python, question, terminal, computer, code, ai, frustration, failure, success, sparkles
