"""Beat type registry — layouts, visuals, camera defaults, script snippets."""

from __future__ import annotations

from typing import Any

# Normalized beat type ids
STATEMENT = "statement"
QUESTION = "question"
JOKE = "joke"
CODE_DEMO = "code_demo"
LIST = "list"
COMPARE = "compare"
RECAP = "recap"
EXPLAIN = "explain"

BEAT_TYPE_ALIASES: dict[str, str] = {
    "joke punchline": JOKE,
    "joke_punchline": JOKE,
    "code": CODE_DEMO,
    "code demo": CODE_DEMO,
    "checklist": LIST,
    "recap": RECAP,
}


def normalize_beat_type(raw: str | None) -> str:
    key = (raw or STATEMENT).strip().lower()
    return BEAT_TYPE_ALIASES.get(key, key.replace(" ", "_"))


def _region(
    rid: str,
    label: str,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    kind: str = "panel",
) -> dict[str, Any]:
    return {"id": rid, "label": label, "x": x, "y": y, "w": w, "h": h, "kind": kind}


BEAT_TYPES: dict[str, dict[str, Any]] = {
    STATEMENT: {
        "id": STATEMENT,
        "label": "Statement",
        "description": "White card + single icon — default lesson beat.",
        "layout": "card_right_icon_left",
        "visuals": ["icon_primary"],
        "regions": [
            _region("label", "Label", 0.05, 0.02, 0.9, 0.11, kind="label"),
            _region("icon", "Icon", 0.05, 0.16, 0.42, 0.78, kind="icon"),
            _region("card", "Card", 0.53, 0.16, 0.42, 0.78, kind="card"),
        ],
        "camera_defaults": [
            {"hook": "after_line_2", "action": "cam_focus_right"},
            {"hook": "after_icon", "action": "cam_focus_left"},
            {"hook": "exit", "action": "cam_restore"},
        ],
        "script_template": """### BEAT N — slug_name

TYPE:       statement
LAYOUT:     card_right_icon_left
CAMERA:     moving

─── CONTENT ───
LABEL:
Your heading

TEXT (card, black):
First line
Second line

─── ICONS ───
icon_primary: sparkles icon | color: WHITE

─── CAMERA ───
cam_focus_right: after_line_2
cam_focus_left: after_icon
cam_restore: exit

HOLD: 1.2s
""",
    },
    QUESTION: {
        "id": QUESTION,
        "label": "Question",
        "description": "Single icon + white text on orange (no card).",
        "layout": "text_right_icon_left",
        "visuals": ["shape_question"],
        "regions": [
            _region("label", "Label", 0.05, 0.02, 0.9, 0.11, kind="label"),
            _region("icon", "Icon", 0.05, 0.16, 0.42, 0.78, kind="icon"),
            _region("text", "BG text", 0.53, 0.16, 0.42, 0.78, kind="text"),
        ],
        "camera_defaults": [
            {"hook": "after_icon", "action": "cam_focus_left"},
            {"hook": "after_line_1", "action": "cam_focus_right"},
            {"hook": "exit", "action": "cam_restore"},
        ],
        "script_template": """### BEAT N — slug_name

TYPE:       question
LAYOUT:     text_right_icon_left
CAMERA:     moving

─── CONTENT ───
LABEL:
Your question

TEXT (white, on BG):
First line?
Second line?

─── ICONS ───
shape_question: question mark help circle | color: WHITE | scale: 1.8

─── CAMERA ───
cam_focus_left: after_icon
cam_focus_right: after_line_1
cam_restore: exit

HOLD: 1.2s
""",
    },
    JOKE: {
        "id": JOKE,
        "label": "Joke / punchline",
        "description": "Setup lines + punchline with icon swap and wiggle.",
        "layout": "card_right_icon_left",
        "visuals": ["icon_primary", "icon_swap"],
        "regions": [
            _region("label", "Label", 0.05, 0.02, 0.9, 0.11, kind="label"),
            _region("icon", "Icon (+ swap)", 0.05, 0.16, 0.42, 0.78, kind="icon"),
            _region("card", "Card + punchline", 0.53, 0.16, 0.42, 0.78, kind="card"),
        ],
        "camera_defaults": [
            {"hook": "after_line_2", "action": "cam_focus_right"},
            {"hook": "after_icon", "action": "cam_focus_left"},
            {"hook": "punchline", "action": "cam_focus_card"},
            {"hook": "exit", "action": "cam_restore"},
        ],
        "script_template": """### BEAT N — slug_name

TYPE:       joke punchline
LAYOUT:     card_right_icon_left
CAMERA:     moving

─── CONTENT ───
LABEL:
Your heading

TEXT (card, black):
Setup line one
Setup line two
Punchline line

─── ICONS ───
icon_primary: friendly icon | color: WHITE
icon_swap: funny reaction icon | color: WHITE

─── EMPHASIS ───
word: punchword | color: RED | animation: wiggle

─── CAMERA ───
cam_focus_right: after_line_2
cam_focus_left: after_icon
cam_focus_card: punchline
cam_restore: exit

HOLD: 1.2s
""",
    },
    CODE_DEMO: {
        "id": CODE_DEMO,
        "label": "Code demo",
        "description": "Label + full-width code card (80% code, 20% output). No execution.",
        "layout": "code_full_card",
        "visuals": [],
        "regions": [
            _region("label", "Label", 0.05, 0.02, 0.9, 0.11, kind="label"),
            _region("code", "Code editor (80%)", 0.05, 0.16, 0.9, 0.58, kind="code"),
            _region("output", "Output (20%)", 0.05, 0.76, 0.9, 0.18, kind="output"),
        ],
        "camera_defaults": [
            {"hook": "after_run", "action": "cam_focus_card"},
            {"hook": "after_code", "action": "cam_focus_card"},
            {"hook": "after_output", "action": "cam_focus_card"},
            {"hook": "exit", "action": "cam_restore"},
        ],
        "script_template": """### BEAT N — run_code

TYPE:       code_demo
LAYOUT:     code_full_card
CAMERA:     moving

─── CONTENT ───
LABEL:
Run Your Code

─── CODE ───
language: python
result: success
output: |
  Hello, World!
lines:
  print("Hello, World!")

# Error example (optional):
# result: error
# error_line: 2
# error: NameError: name 'x' is not defined
# lines:
#   x = 1
#   print(y)

─── CAMERA ───
cam_focus_card: after_run
cam_focus_card: after_code
cam_focus_card: after_output
cam_restore: exit

HOLD: 1.5s
""",
    },
    LIST: {
        "id": LIST,
        "label": "List / checklist",
        "description": "Card with checklist lines and optional icon.",
        "layout": "card_right_icon_left",
        "visuals": ["icon_primary"],
        "regions": [
            _region("label", "Label", 0.05, 0.02, 0.9, 0.11, kind="label"),
            _region("icon", "Icon", 0.05, 0.16, 0.42, 0.78, kind="icon"),
            _region("list", "Checklist card", 0.53, 0.16, 0.42, 0.78, kind="card"),
        ],
        "camera_defaults": [
            {"hook": "after_line_1", "action": "cam_focus_card"},
            {"hook": "after_line_2", "action": "cam_focus_card"},
            {"hook": "after_icon", "action": "cam_focus_card"},
            {"hook": "exit", "action": "cam_restore"},
        ],
        "script_template": """### BEAT N — recap_list

TYPE:       list
LAYOUT:     card_right_icon_left
CAMERA:     moving

─── CONTENT ───
LABEL:
Key points

LIST (card, checks):
Point one
Point two
Point three

─── ICONS ───
icon_primary: checklist icon | color: WHITE

─── CAMERA ───
cam_focus_card: after_line_1
cam_focus_card: after_line_2
cam_focus_card: after_icon
cam_restore: exit

HOLD: 1.2s
""",
    },
    COMPARE: {
        "id": COMPARE,
        "label": "Compare",
        "description": "Two panels — good vs bad, before vs after.",
        "layout": "dual_card",
        "visuals": [],
        "regions": [
            _region("label", "Label", 0.05, 0.02, 0.9, 0.11, kind="label"),
            _region("left", "Left card", 0.05, 0.16, 0.42, 0.78, kind="card"),
            _region("right", "Right card", 0.53, 0.16, 0.42, 0.78, kind="card"),
        ],
        "camera_defaults": [
            {"hook": "after_line_1", "action": "cam_focus_left"},
            {"hook": "after_line_2", "action": "cam_focus_right"},
            {"hook": "exit", "action": "cam_restore"},
        ],
        "script_template": """### BEAT N — compare

TYPE:       compare
LAYOUT:     dual_card
CAMERA:     moving

─── CONTENT ───
LABEL:
Compare

TEXT (left card):
Wrong way

TEXT (right card):
Right way

─── CAMERA ───
cam_focus_left: after_line_1
cam_focus_right: after_line_2
cam_restore: exit

HOLD: 1.2s
""",
    },
    RECAP: {
        "id": RECAP,
        "label": "Recap",
        "description": "Summary statement with celebratory icon.",
        "layout": "card_right_icon_left",
        "visuals": ["icon_sparkles"],
        "regions": [
            _region("label", "Label", 0.05, 0.02, 0.9, 0.11, kind="label"),
            _region("icon", "Icon", 0.05, 0.16, 0.42, 0.78, kind="icon"),
            _region("card", "Summary", 0.53, 0.16, 0.42, 0.78, kind="card"),
        ],
        "camera_defaults": [
            {"hook": "after_icon", "action": "cam_focus_left"},
            {"hook": "exit", "action": "cam_restore"},
        ],
        "script_template": """### BEAT N — recap

TYPE:       recap
LAYOUT:     card_right_icon_left

─── CONTENT ───
LABEL:
Quick recap

TEXT (card, black):
You learned X
You learned Y

─── ICONS ───
icon_sparkles: celebration sparkles | color: WHITE

HOLD: 1.2s
""",
    },
    EXPLAIN: {
        "id": EXPLAIN,
        "label": "Explain / tool",
        "description": "Concept card with terminal or tool icon.",
        "layout": "card_right_icon_left",
        "visuals": ["icon_terminal"],
        "regions": [
            _region("label", "Label", 0.05, 0.02, 0.9, 0.11, kind="label"),
            _region("icon", "Tool icon", 0.05, 0.16, 0.42, 0.78, kind="icon"),
            _region("card", "Explanation", 0.53, 0.16, 0.42, 0.78, kind="card"),
        ],
        "camera_defaults": [
            {"hook": "after_line_1", "action": "cam_focus_right"},
            {"hook": "after_icon", "action": "cam_focus_left"},
            {"hook": "exit", "action": "cam_restore"},
        ],
        "script_template": """### BEAT N — explain

TYPE:       explain
LAYOUT:     card_right_icon_left
CAMERA:     moving

─── CONTENT ───
LABEL:
How it works

TEXT (card, black):
Step explanation line one
Line two

─── ICONS ───
icon_terminal: terminal icon | color: WHITE

─── CAMERA ───
cam_focus_right: after_line_1
cam_focus_left: after_icon
cam_restore: exit

HOLD: 1.2s
""",
    },
}


def get_beat_type(type_id: str) -> dict[str, Any]:
    return BEAT_TYPES.get(normalize_beat_type(type_id), BEAT_TYPES[STATEMENT])


def apply_type_defaults(beat: dict) -> dict:
    """Fill layout and merge default camera hooks when beat omits them."""
    beat = dict(beat)
    tid = normalize_beat_type(beat.get("type"))
    spec = get_beat_type(tid)
    beat["type"] = tid
    if not beat.get("layout"):
        beat["layout"] = spec["layout"]
    if tid == CODE_DEMO and not beat.get("code_lines"):
        beat.setdefault("code_lines", ['print("Hello, World!")'])
        beat.setdefault("code_output", "Hello, World!")
        beat.setdefault("code_result", "success")
    existing_hooks = {s.get("hook") for s in beat.get("camera") or [] if isinstance(s, dict)}
    merged = list(beat.get("camera") or [])
    for step in spec.get("camera_defaults", []):
        hook = step.get("hook")
        if hook and hook not in existing_hooks:
            merged.append({**step, "run_time": 0.9})
            existing_hooks.add(hook)
    if merged:
        beat["camera"] = merged
    return beat


def list_beat_types() -> list[dict[str, Any]]:
    """Public metadata for Studio API (preview + picker)."""
    out = []
    for spec in BEAT_TYPES.values():
        out.append(
            {
                "id": spec["id"],
                "label": spec["label"],
                "description": spec["description"],
                "layout": spec["layout"],
                "visuals": spec.get("visuals", []),
                "regions": spec.get("regions", []),
                "script_template": spec.get("script_template", ""),
                "camera_defaults": spec.get("camera_defaults", []),
            }
        )
    return out
