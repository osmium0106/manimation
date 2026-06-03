"""Unified visual loader — procedural, brand, and iconify assets."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "animations"))

from icon_library import (  # noqa: E402
    fetch_iconify_svg,
    is_colorful_iconify_ref,
    normalize_icon_color,
    should_preserve_svg_colors,
    style_svg_mobject,
)

if TYPE_CHECKING:
    from manim import Mobject


def _manim():
    from manim import Mobject, SVGMobject, WHITE

    return Mobject, SVGMobject, WHITE


def _resolve_color(color: str | None):
    if color is None:
        return None
    from manim import BLUE, GREEN, ORANGE, PINK, PURPLE, RED, TEAL, WHITE, YELLOW

    named = {
        "WHITE": WHITE,
        "BLACK": "#000000",
        "GRAY": "#9ca3af",
        "SILVER": "#c0c0c0",
        "BLUE": BLUE,
        "RED": RED,
        "YELLOW": YELLOW,
        "GREEN": GREEN,
        "ORANGE": ORANGE,
        "PURPLE": PURPLE,
        "PINK": PINK,
        "CYAN": "#22d3ee",
        "TEAL": TEAL,
        "GOLD": "#ffd700",
        "AMBER": "#fbbf24",
        "ROSE": "#fb7185",
        "FUCHSIA": "#e879f9",
        "VIOLET": "#8b5cf6",
        "INDIGO": "#6366f1",
        "SKY": "#38bdf8",
        "LIME": "#a3e635",
        "EMERALD": "#34d399",
    }
    if isinstance(color, str) and color.upper() in named:
        return named[color.upper()]
    return color


def _svg_mob(path: Path, scale: float, color: str | None, *, ref: str = "") -> "Mobject":
    _, SVGMobject, _ = _manim()
    mob = SVGMobject(str(path))
    tint = normalize_icon_color(color)
    if tint is not None and not should_preserve_svg_colors(path, ref):
        resolved = _resolve_color(tint)
        if resolved is not None:
            style_svg_mobject(mob, resolved)
    mob.scale(scale)
    return mob


def load_procedural(scene, ref: str, scale: float = 1.0) -> "Mobject":
    if ref == "shape_question":
        return scene.shape_question(radius=0.8 * scale)
    raise KeyError(f"Unknown procedural visual: {ref}")


def load_brand(ref: str, scale: float = 1.0) -> "Mobject":
    path = ROOT / ref if not ref.startswith("/") else Path(ref)
    if not path.exists():
        raise FileNotFoundError(f"Brand asset not found: {path}")
    return _svg_mob(path, scale, color=None)


def load_project_icon(scene, ref: str, scale: float = 1.0, color: str | None = None) -> "Mobject":
    """Load SVG/PNG from the project icons folder (scene.project_dir)."""
    base = getattr(scene, "project_dir", None)
    if base is None:
        raise FileNotFoundError("Scene has no project_dir — cannot load project icon")
    path = Path(base) / ref
    if not path.is_file():
        raise FileNotFoundError(f"Project icon not found: {path}")
    if path.suffix.lower() == ".png":
        from manim import ImageMobject

        mob = ImageMobject(str(path))
        mob.scale(scale)
        return mob
    return _svg_mob(path, scale, color, ref=ref)


def load_iconify(ref: str, scale: float = 1.0, color: str | None = None) -> "Mobject":
    _, _, WHITE = _manim()
    prefix, name = ref.split(":", 1)
    svg_path = fetch_iconify_svg(prefix, name)
    tint = normalize_icon_color(color)
    if tint is None or should_preserve_svg_colors(svg_path, ref):
        return _svg_mob(svg_path, scale, None, ref=ref)
    resolved = _resolve_color(tint)
    return _svg_mob(svg_path, scale, resolved if resolved is not None else WHITE, ref=ref)


def load_visual(scene, spec: dict) -> "Mobject":
    """Load a resolved visual spec into a Manim mobject."""
    _, _, WHITE = _manim()
    kind = spec.get("kind", "iconify")
    ref = spec.get("ref", "lucide:sparkles")
    scale = float(spec.get("scale", 1.2))
    color = spec.get("color")
    if isinstance(color, str) and color.upper() in ("ORIGINAL", "PRESERVE"):
        color = None
    elif color is None and kind == "iconify" and not is_colorful_iconify_ref(ref):
        color = WHITE
    elif color == "WHITE":
        color = WHITE

    if kind == "procedural":
        return load_procedural(scene, ref, scale)
    if kind == "brand":
        return load_brand(ref, scale)
    if kind == "project" or ref.startswith("icons/"):
        return load_project_icon(scene, ref, scale, color)
    return load_iconify(ref, scale, color)


def prefetch_beat_visuals(beat: dict) -> list[Path]:
    """Download/cache all iconify assets for a beat."""
    saved: list[Path] = []
    resolved = beat.get("visuals_resolved") or {}
    slots: list = []
    stack = resolved.get("stack")
    if isinstance(stack, list):
        slots.extend(stack)
    for slot_name in ("primary", "swap"):
        spec = resolved.get(slot_name)
        if isinstance(spec, dict):
            slots.append(spec)
    for spec in slots:
        if not isinstance(spec, dict) or spec.get("kind") != "iconify":
            continue
        ref = spec.get("ref", "")
        if ":" not in ref:
            continue
        prefix, name = ref.split(":", 1)
        desc = spec.get("description") or spec.get("concept") or "icon"
        saved.append(fetch_iconify_svg(prefix, name, description=str(desc)))
    return saved
