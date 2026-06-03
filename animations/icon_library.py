"""Icon library for Manim scenes.

Sources (checked in order for beat icons):

1. **Beat folder** — ``Episode{N}/beats/beat{M}/icons/<id>.svg``
2. **Global cache** — ``assets/icons/cache/<prefix>/<name>.svg``
3. **Iconify API** — on-demand download

Usage::

    from icon_library import load_beat_icon, sync_beat_icons

    sync_beat_icons(episode=1, beat=1)   # download manifest → beat folder
    load_beat_icon(1, 1, "icon_python", scale=1.2, color=WHITE)
    load_icon("lucide:rocket", color=WHITE)   # global / alias
"""

from __future__ import annotations

import json
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from manim import Mobject

ROOT = Path(__file__).resolve().parent.parent
BACKGROUND_DIR = ROOT / "background"
ICONS_DIR = ROOT / "assets" / "icons"
CACHE_DIR = ICONS_DIR / "cache"

ICONIFY_API = "https://api.iconify.design/{prefix}/{name}.svg"
ICONIFY_SEARCH = "https://api.iconify.design/search?query={query}&limit={limit}"
USER_AGENT = "manimations-icon-library/1.0"

ICON_PATHS: dict[str, Path] = {
    "icon_python": BACKGROUND_DIR / "python.png",
    "img_python": BACKGROUND_DIR / "python.png",
}

ICON_ALIASES: dict[str, str] = {
    "icon_laptop": "lucide:laptop",
    "icon_editor": "lucide:square-code",
    "icon_file": "lucide:file",
    "icon_cross": "lucide:x",
    "icon_rocket": "lucide:rocket",
    "icon_heart": "lucide:heart",
    "icon_cursor": "lucide:text-cursor",
    "icon_arrow_down": "lucide:arrow-down",
    "icon_sparkles": "lucide:sparkles",
    "icon_snake_sleep": "lucide:moon",
    "icon_potato": "mdi:food-apple",
    "shape_question": "lucide:circle-help",
    "ui_checkmark": "lucide:check",
}

ICONIFY_REF = re.compile(r"^[a-z0-9-]+:[a-z0-9-]+$")

COLORFUL_ICONIFY_PREFIXES = frozenset(
    {
        "fa6-brands",
        "fa-brands",
        "fa7-brands",
        "devicon",
        "devicon-plain",
        "logos",
        "twemoji",
        "noto",
        "emojione",
        "fluent-emoji-flat",
        "fluent-emoji",
        "skill-icons",
        "simple-icons",
        "catppuccin",
        "material-icon-theme",
        "vscode-icons",
        "bxl",
        "cib",
        "ion",
        "akar-icons",
        "game-icons",
    }
)


def is_colorful_iconify_ref(ref: str) -> bool:
    if ":" not in ref:
        return False
    prefix = ref.split(":", 1)[0].lower()
    return prefix in COLORFUL_ICONIFY_PREFIXES or prefix.startswith("emoji")


def should_preserve_svg_colors(path: Path, ref: str = "") -> bool:
    """Keep original fills for brand / multi-color SVGs; mono stroke icons get tinted."""
    if ref.startswith("assets/") or ref.startswith("icons/"):
        return True
    if ref and is_colorful_iconify_ref(ref):
        return True
    try:
        text = path.read_text()
    except OSError:
        return False
    hex_fills = set(re.findall(r'fill="(#[0-9a-fA-F]{3,8})"', text))
    hex_fills -= {"#000", "#000000", "#fff", "#ffffff", "#FFFFFF"}
    if len(hex_fills) >= 2:
        return True
    if 'fill="none"' in text and "stroke=" in text:
        colored = [f for f in re.findall(r'fill="([^"]+)"', text) if f not in ("none", "currentColor", "transparent")]
        if not colored or (len(colored) == 1 and colored[0] in ("currentColor", "#000", "#000000")):
            return False
    if len(hex_fills) == 1:
        return True
    return False


def normalize_icon_color(color: str | None) -> str | None:
    """Return Manim tint color, or None to preserve SVG original colors."""
    if color is None:
        return None
    if isinstance(color, str) and color.upper() in ("ORIGINAL", "PRESERVE", ""):
        return None
    return color


def beat_dir(episode: int | str, beat: int | str) -> Path:
    ep = episode if str(episode).startswith("Episode") else f"Episode{episode}"
    bt = beat if str(beat).startswith("beat") else f"beat{beat}"
    return ROOT / ep / "beats" / bt


def beat_icons_dir(episode: int | str, beat: int | str) -> Path:
    return beat_dir(episode, beat) / "icons"


def beat_manifest(episode: int | str, beat: int | str) -> Path:
    return beat_dir(episode, beat) / "icons.json"


def read_beat_manifest(episode: int | str, beat: int | str) -> dict[str, str]:
    path = beat_manifest(episode, beat)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _parse_ref(icon_ref: str) -> tuple[str, str | None]:
    if icon_ref in ICON_PATHS:
        return "local", icon_ref
    if icon_ref in ICON_ALIASES:
        return "iconify", ICON_ALIASES[icon_ref]
    if ICONIFY_REF.match(icon_ref):
        return "iconify", icon_ref
    legacy = ICONS_DIR / f"{icon_ref.removeprefix('icon_')}.svg"
    if legacy.exists():
        return "local", str(legacy)
    raise KeyError(
        f"Unknown icon '{icon_ref}'. "
        f"Use an alias, an Iconify ref like 'lucide:laptop', or register in ICON_PATHS."
    )


def _cache_path(prefix: str, name: str) -> Path:
    return CACHE_DIR / prefix / f"{name}.svg"


def iconify_ref_exists(prefix: str, name: str) -> bool:
    url = ICONIFY_API.format(prefix=prefix, name=name)
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except urllib.error.HTTPError:
        return False


def search_iconify(query: str, *, limit: int = 16) -> list[str]:
    """Search Iconify for icon refs matching plain-text query."""
    q = urllib.parse.quote(query.strip())
    if not q:
        return []
    url = ICONIFY_SEARCH.format(query=q, limit=limit)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError):
        return []
    icons = data.get("icons") or []
    return [ref for ref in icons if isinstance(ref, str) and ICONIFY_REF.match(ref)]


PREFERRED_PREFIXES = (
    "lucide",
    "fa6-brands",
    "devicon",
    "twemoji",
    "noto",
    "mdi",
    "fluent-emoji-flat",
)


def _rank_iconify_ref(ref: str) -> int:
    prefix = ref.split(":", 1)[0]
    try:
        return PREFERRED_PREFIXES.index(prefix)
    except ValueError:
        return len(PREFERRED_PREFIXES)


def _search_queries_for_ref(ref: str, description: str = "") -> list[str]:
    prefix, name = ref.split(":", 1)
    queries: list[str] = []
    if description.strip():
        queries.append(description.strip())
    readable = name.replace("-", " ").replace("_", " ")
    queries.append(readable)
    queries.append(f"{prefix} {readable}")
    for word in re.findall(r"[a-zA-Z']+", f"{description} {readable}"):
        if len(word) > 2 and word.lower() not in {"icon", "the", "and", "for"}:
            queries.append(word)
    seen: set[str] = set()
    out: list[str] = []
    for q in queries:
        key = q.lower()
        if key not in seen:
            seen.add(key)
            out.append(q)
    return out


def ensure_iconify_ref(ref: str, description: str = "") -> str:
    """Return a fetchable Iconify ref, searching alternatives if the ref 404s."""
    if not ICONIFY_REF.match(ref):
        return ref
    prefix, name = ref.split(":", 1)
    if iconify_ref_exists(prefix, name):
        return ref

    tried: set[str] = {ref}
    for query in _search_queries_for_ref(ref, description):
        found: list[str] = []
        for candidate in search_iconify(query):
            if candidate in tried:
                continue
            tried.add(candidate)
            p, n = candidate.split(":", 1)
            if iconify_ref_exists(p, n):
                found.append(candidate)
        if found:
            found.sort(key=_rank_iconify_ref)
            return found[0]

    raise KeyError(
        f"Iconify icon not found: {ref}. "
        f"Tried similar searches for: {description or name!r}"
    )


def fetch_iconify_svg(
    prefix: str,
    name: str,
    *,
    force: bool = False,
    description: str = "",
) -> Path:
    ref = ensure_iconify_ref(f"{prefix}:{name}", description)
    prefix, name = ref.split(":", 1)
    path = _cache_path(prefix, name)
    if path.exists() and not force:
        return path

    url = ICONIFY_API.format(prefix=prefix, name=name)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except urllib.error.HTTPError as exc:
        raise KeyError(f"Iconify icon not found: {prefix}:{name} ({exc.code})") from exc

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _svg_to_mobject(path: Path, scale: float, color: str | None, *, ref: str = "") -> "Mobject":
    from manim import SVGMobject

    mob = SVGMobject(str(path))
    tint = normalize_icon_color(color)
    if tint is not None and not should_preserve_svg_colors(path, ref):
        style_svg_mobject(mob, tint)
    mob.scale(scale)
    return mob


# Minimum stroke widths for tinted Iconify / mono SVG icons (scene units).
ICON_MIN_STROKE = 5.6  # 2× prior 2.8 — readable on orange course backgrounds
ICON_MIN_STROKE_FILLED = 3.0  # 2× prior 1.5 when icon uses fill + stroke


def style_svg_mobject(mob: "Mobject", color) -> None:
    """Tint monochrome stroke icons; skip when SVG keeps its own palette."""
    for sm in mob.get_family():
        fill_op = sm.get_fill_opacity()
        stroke_w = float(sm.get_stroke_width() or 0)
        if fill_op is not None and fill_op > 0.01:
            sm.set_fill(color, opacity=1)
            if stroke_w > 0:
                sm.set_stroke(
                    color,
                    width=max(stroke_w * 2, ICON_MIN_STROKE_FILLED),
                    opacity=1,
                )
        elif stroke_w > 0:
            sm.set_fill(color, opacity=0)
            sm.set_stroke(
                color,
                width=max(stroke_w * 2, ICON_MIN_STROKE),
                opacity=1,
            )


def save_beat_icon(
    episode: int | str,
    beat: int | str,
    icon_id: str,
    iconify_ref: str,
    *,
    force: bool = False,
) -> Path:
    """Download from Iconify and save to Episode{N}/beats/beat{M}/icons/."""
    prefix, name = iconify_ref.split(":", 1)
    src = fetch_iconify_svg(prefix, name, force=force)
    dest_dir = beat_icons_dir(episode, beat)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{icon_id}.svg"
    shutil.copy2(src, dest)
    return dest


def sync_beat_icons(episode: int | str, beat: int | str, *, force: bool = False) -> list[Path]:
    """Sync all icons listed in the beat's icons.json manifest."""
    manifest = read_beat_manifest(episode, beat)
    if not manifest:
        raise FileNotFoundError(f"No icons.json at {beat_manifest(episode, beat)}")
    saved: list[Path] = []
    for icon_id, iconify_ref in manifest.items():
        saved.append(save_beat_icon(episode, beat, icon_id, iconify_ref, force=force))
    return saved


def load_beat_icon(
    episode: int | str,
    beat: int | str,
    icon_id: str,
    scale: float = 1.0,
    color: str | None = None,
) -> "Mobject":
    path = beat_icons_dir(episode, beat) / f"{icon_id}.svg"
    if not path.exists():
        manifest = read_beat_manifest(episode, beat)
        if icon_id in manifest:
            save_beat_icon(episode, beat, icon_id, manifest[icon_id])
            path = beat_icons_dir(episode, beat) / f"{icon_id}.svg"
        else:
            raise FileNotFoundError(
                f"Beat icon '{icon_id}' not found at {path}. "
                f"Add it to {beat_manifest(episode, beat)} and run sync_beat_icons()."
            )
    ref = read_beat_manifest(episode, beat).get(icon_id, icon_id)
    tint = normalize_icon_color(color)
    if tint is None and color is None:
        if isinstance(ref, str) and (is_colorful_iconify_ref(ref) or ref.startswith("assets/")):
            pass
        else:
            from manim import WHITE

            tint = WHITE
    return _svg_to_mobject(path, scale, tint, ref=ref if isinstance(ref, str) else "")


def prefetch(*icon_refs: str, force: bool = False) -> list[Path]:
    saved: list[Path] = []
    for ref in icon_refs:
        kind, value = _parse_ref(ref)
        if kind == "local":
            path = ICON_PATHS.get(value) if value in ICON_PATHS else Path(value)
            if path.exists():
                saved.append(path)
            continue
        prefix, name = value.split(":", 1)
        saved.append(fetch_iconify_svg(prefix, name, force=force))
    return saved


def prefetch_all(force: bool = False) -> list[Path]:
    return prefetch(*ICON_ALIASES.keys(), force=force)


def list_aliases() -> dict[str, str]:
    return dict(ICON_ALIASES)


def load_icon(
    icon_ref: str,
    scale: float = 1.0,
    color: str | None = None,
) -> "Mobject":
    from manim import WHITE, ImageMobject

    if color is None:
        color = WHITE
    kind, value = _parse_ref(icon_ref)

    if kind == "local":
        path = ICON_PATHS[value] if value in ICON_PATHS else Path(value)
        if path.suffix.lower() == ".png":
            mob = ImageMobject(str(path))
            mob.scale(scale)
            return mob
        return _svg_to_mobject(path, scale, color)

    prefix, name = value.split(":", 1)
    svg_path = fetch_iconify_svg(prefix, name)
    tint = normalize_icon_color(color)
    if tint is None and not should_preserve_svg_colors(svg_path, value):
        from manim import WHITE
        tint = WHITE
    return _svg_to_mobject(svg_path, scale, tint, ref=value)
