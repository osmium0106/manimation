"""Compile project beats into a self-contained Manim .py scene file."""

from __future__ import annotations

import json
import re
from pathlib import Path

MANIM_ROOT = Path(__file__).resolve().parents[3]


def starter_scene_code(theme: dict | None = None) -> str:
    """Blank Manim scene template for writing from scratch."""
    theme_payload = json.dumps(theme or {}, indent=4, ensure_ascii=False)
    open_q, close_q = _json_block(theme_payload)
    return f'''"""Custom Manim scene — edit freely and click Apply & Re-render."""

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
MANIM_ROOT = Path({str(MANIM_ROOT)!r})
sys.path.insert(0, str(MANIM_ROOT / "animations"))

from manim import *
from beat_helpers import BeatScene
from theme_loader import normalize_theme, resolve_manim_color


THEME = normalize_theme(json.loads({open_q}
{theme_payload.rstrip()}
{close_q}))


class GeneratedScene(BeatScene):
    def construct(self):
        self.set_theme(THEME)
        self.setup_background()

        label = self.top_label("Hello from Manim")
        card = self.empty_card(side="right", width=5.6, height=4.0, label=label)
        line = self.on_card("Edit this code and re-render.")
        self.place_card_content(line, card)

        spec = self._typo("heading")
        cursor = resolve_manim_color(spec.get("cursor") or spec["color"])
        self.type_text(label, time_per_char=0.05, cursor_color=cursor)
        self.play(GrowFromCenter(card), run_time=0.4)
        self.type_text(line, time_per_char=0.05)
        self.wait(1.2)
        self.fade_clear(label, card, line)
'''


def _slug(label: str, index: int) -> str:
    clean = str(label).splitlines()[0]
    slug = re.sub(r"[^\w]+", "_", clean.lower()).strip("_") or f"beat_{index + 1}"
    return slug[:40]


def _comment_label(label: str) -> str:
    """Single-line safe text for Python comments."""
    line = str(label).splitlines()[0].strip()
    return re.sub(r"\s+", " ", line) or "Beat"


def _sanitize_beat(beat: dict) -> dict:
    """Normalize beat fields before embedding in generated Python."""
    out = dict(beat)
    label = out.get("label")
    if label is not None and "\n" in str(label):
        out["label"] = str(label).splitlines()[0].strip() or "Beat"
    return out


def _json_block(payload: str) -> tuple[str, str]:
    """Pick triple-quote delimiters that do not appear inside the JSON payload."""
    if '"""' not in payload:
        return '"""', '"""'
    if "'''" not in payload:
        return "'''", "'''"
    raise ValueError("Beat JSON contains both triple-double and triple-single quotes")


def _embed_json_call(func: str, payload: str) -> list[str]:
    """Emit a function call with a readable multi-line JSON string argument."""
    open_q, close_q = _json_block(payload)
    return [
        f"{func}({open_q}",
        payload.rstrip(),
        f"{close_q})",
    ]


def _beat_constant(index: int, beat: dict) -> tuple[str, list[str]]:
    """Return (variable_name, source lines) for one beat."""
    beat = _sanitize_beat(beat)
    label = beat.get("label", f"Beat {index + 1}")
    slug = _slug(label, index)
    var = f"BEAT_{index + 1}_{slug}".upper()
    if not var[0].isalpha():
        var = f"B_{var}"
    payload = json.dumps(beat, indent=4, ensure_ascii=False)
    lines = [f"# Beat {index + 1} — {_comment_label(label)}"]
    lines.extend(_embed_json_call(f"{var} = load_beat_json", payload))
    return var, lines


def _format_python(source: str) -> str:
    try:
        import black

        return black.format_str(source, mode=black.Mode(line_length=88))
    except Exception:
        return source


def generate_scene_code(project: dict, *, theme: dict | None = None) -> str:
    """Emit a standalone .py file with embedded beats and a construct loop."""
    project_id = project.get("id", "project")
    project_name = project.get("name", project_id)
    use_camera = project.get("use_camera", False)
    beats = project.get("beats", [])

    if not beats:
        return starter_scene_code(theme)

    beat_vars: list[str] = []
    beat_lines: list[str] = []
    for i, beat in enumerate(beats):
        var, lines = _beat_constant(i, beat)
        beat_vars.append(var)
        if beat_lines:
            beat_lines.append("")
        beat_lines.extend(lines)

    scene_base = "MovingBeatScene" if use_camera else "BeatScene"
    beats_list = ",\n    ".join(beat_vars)
    theme_payload = json.dumps(theme or {}, indent=4, ensure_ascii=False)
    theme_open, theme_close = _json_block(theme_payload)

    header = f'''"""Auto-generated scene for {project_name} ({len(beats)} beat(s)).

Beat specs are embedded below. Manim renders this file directly.
Re-generate from beats (From beats) after editing the beat script.
"""

import json
import sys
from pathlib import Path

MANIM_ROOT = Path({str(MANIM_ROOT)!r})
sys.path.insert(0, str(MANIM_ROOT / "animations"))

from beat_interpreter import run_beat_from_spec, _apply_bg  # noqa: E402
from beat_helpers import BeatScene, MovingBeatScene  # noqa: E402
from beat_json import load_beat_json  # noqa: E402
from theme_loader import normalize_theme  # noqa: E402

USE_CAMERA = {use_camera}
THEME = normalize_theme(json.loads({theme_open}
{theme_payload.rstrip()}
{theme_close}))


'''

    body = "\n".join(beat_lines)
    footer = f"""

BEATS = [
    {beats_list},
]


class GeneratedScene({scene_base}):
    def construct(self):
        self.project_dir = Path(__file__).resolve().parent
        self.set_theme(THEME)
        _apply_bg(self, THEME)
        for i, beat in enumerate(BEATS):
            run_beat_from_spec(self, beat, use_camera=USE_CAMERA)
            if i < len(BEATS) - 1:
                nxt = BEATS[i + 1]
                if nxt.get("continue_beat"):
                    self.wait(0.12)
                else:
                    self.beat_transition()
"""

    return _format_python(header + body + footer)


def compile_scene(project: dict, output_path: Path, *, theme: dict | None = None) -> Path:
    """Write generated_scene.py with embedded beats and per-beat render loop."""
    output_path.write_text(generate_scene_code(project, theme=theme))
    return output_path


def detect_scene_class(source: str) -> str:
    """Find the Scene subclass name in Python source."""
    match = re.search(
        r"class\s+(\w+)\s*\(\s*(?:MovingCameraScene|BeatScene|MovingBeatScene|Scene)",
        source,
    )
    if match:
        return match.group(1)
    return "GeneratedScene"


def patch_scene_code(source: str) -> str:
    """Upgrade legacy generated scenes to use lenient beat JSON loading."""
    if "load_beat_json(" in source:
        return source
    if "json.loads(" not in source or "BEAT_" not in source:
        return source
    if "from beat_json import load_beat_json" not in source:
        marker = "from beat_helpers import"
        if marker in source:
            source = source.replace(
                marker,
                "from beat_json import load_beat_json  # noqa: E402\n" + marker,
                1,
            )
        else:
            insert_at = source.find("\n\n")
            if insert_at >= 0:
                source = (
                    source[:insert_at]
                    + "\nfrom beat_json import load_beat_json  # noqa: E402"
                    + source[insert_at:]
                )
    return source.replace("json.loads(", "load_beat_json(")
