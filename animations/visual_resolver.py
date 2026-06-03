"""Semantic visual resolver — maps beat context to concrete visual specs."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "animations"))
from icon_library import is_colorful_iconify_ref  # noqa: E402
CATALOG_PATH = ROOT / "assets" / "visual_catalog.json"
STYLE_PACKS_DIR = ROOT / "assets" / "style_packs"

ROLE_DEFAULTS: dict[str, str] = {
    "subject": "sparkles",
    "question": "question",
    "tool": "terminal",
    "actor": "computer",
    "process": "code",
    "punchline": "failure",
    "brand": "python",
    "emphasis": "sparkles",
}

TYPE_RULES: dict[str, dict[str, Any]] = {
    "question": {"left_concept": "question", "left_role": "question"},
    "statement": {"left_role": "subject"},
    "joke": {"left_role": "subject", "swap_role": "punchline"},
    "joke punchline": {"left_role": "subject", "swap_role": "punchline"},
    "explain": {"left_role": "tool"},
}


def _as_dict(value: Any, default: dict | None = None) -> dict:
    """Coerce GPT/script output into a dict (lists often arrive where dicts are expected)."""
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                return item
        return default or {}
    return default or {}


def _normalize_visuals(visuals: Any) -> dict:
    if visuals is None:
        return {}
    if isinstance(visuals, list):
        out: dict[str, dict] = {}
        if len(visuals) > 0:
            out["primary"] = _as_dict(visuals[0])
        if len(visuals) > 1:
            out["swap"] = _as_dict(visuals[1])
        if len(visuals) > 2:
            out["stack"] = [_as_dict(item) for item in visuals[2:]]
        return out
    if isinstance(visuals, dict):
        stack = visuals.get("stack")
        return {
            "primary": _as_dict(visuals.get("primary") or visuals.get("left")),
            "swap": _as_dict(visuals.get("swap") or visuals.get("left_swap"), default={}),
            "stack": stack if isinstance(stack, list) else None,
        }
    return {}


def _emphasis_trigger(beat: dict) -> str | None:
    emphasis = beat.get("emphasis")
    if not emphasis:
        return None
    if isinstance(emphasis, list):
        first = emphasis[0]
        if isinstance(first, dict):
            return first.get("word")
        if isinstance(first, str):
            return first
    return None


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def load_catalog() -> dict[str, dict]:
    return _load_json(CATALOG_PATH)


def load_style_pack(pack_id: str = "course_clean") -> dict:
    path = STYLE_PACKS_DIR / f"{pack_id}.json"
    if not path.exists():
        path = STYLE_PACKS_DIR / "course_clean.json"
    return _load_json(path)


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-zA-Z']+", text.lower())}


def score_concept(concept_id: str, entry: dict, tokens: set[str], beat_type: str) -> float:
    score = 0.0
    tags = set(entry.get("tags", []))
    synonyms = set(entry.get("synonyms", []))
    if concept_id in tokens:
        score += 10
    score += len(tokens & synonyms) * 4
    score += len(tokens & tags) * 2
    if beat_type in tags:
        score += 5
    return score


def infer_concept_from_text(text: str, beat_type: str = "statement", role: str = "subject") -> str:
    catalog = load_catalog()
    tokens = _tokenize(text)
    best_id = ROLE_DEFAULTS.get(role, "sparkles")
    best_score = 0.0
    for concept_id, entry in catalog.items():
        s = score_concept(concept_id, entry, tokens, beat_type)
        if s > best_score:
            best_score = s
            best_id = concept_id
    return best_id if best_score > 0 else ROLE_DEFAULTS.get(role, "sparkles")


def _pick_candidate(entry: dict, style_pack: dict) -> dict:
    exclude = set(style_pack.get("exclude_style_packs", []))
    prefer_kinds = style_pack.get("prefer_kinds", ["procedural", "brand", "iconify"])
    candidates = entry.get("candidates", [])
    filtered = [
        c
        for c in candidates
        if c.get("style_pack") is None or c.get("style_pack") not in exclude
    ]
    if not filtered:
        filtered = candidates
    for kind in prefer_kinds:
        for c in filtered:
            if c.get("kind") == kind:
                return dict(c)
    return dict(filtered[0]) if filtered else {"kind": "iconify", "ref": "lucide:sparkles", "scale": 1.2}


ICONIFY_REF = re.compile(r"^[a-z0-9-]+:[a-z0-9-]+$")

ICON_STACK_ORDER = {
    "icon_mobile": 0,
    "icon_web": 1,
    "icon_desktop": 2,
}


def _parse_manifest_icon(value: str) -> tuple[str, dict[str, Any]]:
    """Parse icons.json values like ``fe:mobile | color: WHITE | scale: 1.4``."""
    ref_part = (value or "").strip()
    meta: dict[str, Any] = {}
    if "|" in ref_part:
        chunks = [chunk.strip() for chunk in ref_part.split("|")]
        ref_part = chunks[0]
        for chunk in chunks[1:]:
            if ":" not in chunk:
                continue
            key, val = chunk.split(":", 1)
            key = key.strip().lower()
            val = val.strip()
            if key == "color":
                meta["color"] = val
            elif key == "scale":
                try:
                    meta["scale"] = float(val)
                except ValueError:
                    pass
            elif key == "trigger":
                meta["trigger"] = val
    return ref_part.strip(), meta


def _normalize_icons_manifest(manifest: dict[str, str]) -> dict[str, str]:
    """Strip ``| color: …`` suffixes so manifest values are plain Iconify refs."""
    out: dict[str, str] = {}
    for icon_id, raw in manifest.items():
        if not isinstance(raw, str):
            continue
        ref, _ = _parse_manifest_icon(raw)
        if ref:
            out[icon_id] = ref
    return out


def _normalize_card_content(beat: dict) -> dict:
    """Card layouts need card_lines — promote bg_lines when authors use the wrong field."""
    beat = dict(beat)
    layout = beat.get("layout", "")
    if "card" not in layout:
        return beat
    if not beat.get("card_lines") and beat.get("bg_lines"):
        beat["card_lines"] = list(beat["bg_lines"])
    if not beat.get("card_side"):
        if "card_left" in layout:
            beat["card_side"] = "left"
        elif "card_right" in layout:
            beat["card_side"] = "right"
    return beat


def _icon_stack_from_manifest(
    beat: dict, style_pack_id: str, *, manifest: dict[str, str] | None = None
) -> list[dict]:
    """Build stacked icon specs from beat icons manifest (mobile/web/desktop, etc.)."""
    manifest = manifest if manifest is not None else (beat.get("icons") or {})
    if not manifest:
        return []

    named = [icon_id for icon_id in manifest if icon_id.startswith("icon_")]
    skip_primary = len(named) >= 3 and any(
        icon_id not in ("icon_primary",) for icon_id in named
    )

    items: list[tuple[str, dict]] = []
    for icon_id, raw in manifest.items():
        if not isinstance(raw, str):
            continue
        if skip_primary and icon_id == "icon_primary":
            continue
        ref, meta = _parse_manifest_icon(raw)
        if not ICONIFY_REF.match(ref):
            continue
        concept = icon_id.removeprefix("icon_").removeprefix("shape_")
        trigger = meta.get("trigger") or concept
        slot = {"ref": ref, "icon_id": icon_id, "trigger": trigger, **meta}
        items.append(
            (
                icon_id,
                resolve_visual_slot(
                    slot,
                    concept=concept,
                    role="subject",
                    style_pack_id=style_pack_id,
                ),
            )
        )

    items.sort(key=lambda pair: (ICON_STACK_ORDER.get(pair[0], 50), pair[0]))
    specs = [spec for _, spec in items][:4]
    if len(specs) >= 2:
        return specs
    return []


def _infer_kind_from_ref(ref: str, icon_id: str = "") -> str:
    if ref.startswith("assets/") or ("/" in ref and ref.endswith(".svg")):
        return "brand"
    if ref == "shape_question":
        return "procedural"
    if ICONIFY_REF.match(ref):
        return "iconify"
    return "iconify"


def _catalog_candidate_for_slot(concept: str, slot: dict, style_pack: dict) -> dict:
    """Pick catalog asset; prefer iconify when the user chose a custom tint."""
    entry = load_catalog().get(concept) or {}
    candidates = entry.get("candidates") or []
    slot_color = slot.get("color")
    user_tint = bool(
        slot_color
        and isinstance(slot_color, str)
        and slot_color.upper() not in ("ORIGINAL", "PRESERVE")
    )
    if user_tint:
        for candidate in candidates:
            if candidate.get("kind") == "iconify" and candidate.get("ref"):
                return dict(candidate)
    return _pick_candidate(entry, style_pack)


def _resolve_slot_color(
    color: str | None,
    *,
    kind: str,
    ref: str,
    style_pack: dict,
) -> str | None:
    if isinstance(color, str) and color.upper() in ("ORIGINAL", "PRESERVE"):
        return None
    if color is not None:
        return color
    if kind == "iconify":
        if ref and is_colorful_iconify_ref(ref):
            return None
        return style_pack.get("default_icon_color", "#FFFFFF")
    if kind == "brand":
        return None
    return color


def _apply_slot_overrides(spec: dict, slot: dict) -> dict:
    spec = dict(spec)
    if slot.get("color") is not None:
        color = slot["color"]
        if isinstance(color, str) and color.upper() in ("ORIGINAL", "PRESERVE"):
            spec["color"] = None
        else:
            spec["color"] = color
    if slot.get("scale") is not None:
        spec["scale"] = float(slot["scale"])
    return spec


def resolve_visual_slot(
    slot: dict,
    *,
    concept: str,
    role: str,
    style_pack_id: str,
) -> dict:
    """Use explicit script ref/color when provided; otherwise fall back to catalog."""
    style_pack = load_style_pack(style_pack_id)
    slot = dict(_as_dict(slot))

    if not (slot.get("ref") or "").strip():
        candidate = _catalog_candidate_for_slot(concept, slot, style_pack)
        if candidate.get("ref"):
            slot.setdefault("ref", candidate["ref"])
            slot.setdefault("kind", candidate.get("kind", "iconify"))
            slot.setdefault("scale", candidate.get("scale", 1.2))

    ref = (slot.get("ref") or "").strip()
    if not ref:
        spec = resolve_concept(concept, style_pack_id=style_pack_id, role=role)
        return _apply_slot_overrides(spec, slot)

    if slot.get("kind") == "project" or ref.startswith("icons/"):
        kind = "project"
    elif ICONIFY_REF.match(ref):
        kind = "iconify"
    elif ref == "shape_question":
        kind = "procedural"
    else:
        kind = slot.get("kind") or _infer_kind_from_ref(ref, slot.get("icon_id", ""))

    color = _resolve_slot_color(
        slot.get("color"),
        kind=kind,
        ref=ref,
        style_pack=style_pack,
    )
    spec = {
        "concept": concept,
        "role": role,
        "kind": kind,
        "ref": ref,
        "scale": float(slot.get("scale", 1.2)),
        "color": color,
        **{k: slot[k] for k in ("trigger", "icon_id") if slot.get(k)},
    }
    return _apply_slot_overrides(spec, slot)


def resolve_concept(
    concept: str,
    *,
    style_pack_id: str = "course_clean",
    role: str = "subject",
) -> dict:
    catalog = load_catalog()
    style_pack = load_style_pack(style_pack_id)
    entry = catalog.get(concept) or catalog.get(ROLE_DEFAULTS.get(role, "sparkles"), {})
    candidate = _pick_candidate(entry, style_pack)
    color = candidate.get("color")
    ref = candidate.get("ref", "")
    if color is None and candidate.get("kind") == "iconify":
        if ref and is_colorful_iconify_ref(ref):
            color = None
        else:
            color = style_pack.get("default_icon_color", "#FFFFFF")
    elif color is None and candidate.get("kind") == "brand":
        color = None
    return {
        "concept": concept,
        "role": role,
        "kind": candidate.get("kind", "iconify"),
        "ref": candidate.get("ref", "lucide:sparkles"),
        "scale": candidate.get("scale", 1.2),
        "color": color,
    }


def resolve_beat_visuals(beat: dict, style_pack_id: str | None = None) -> dict:
    """Resolve all visuals for a beat dict. Mutates and returns beat with resolved visuals."""
    pack = style_pack_id or beat.get("style_pack", "course_clean")
    beat = _normalize_card_content(beat)
    raw_icons = dict(beat.get("icons") or {})
    if raw_icons:
        beat = dict(beat)
        beat["icons"] = _normalize_icons_manifest(raw_icons)
    beat_type = beat.get("type", "statement").lower()
    rules = TYPE_RULES.get(beat_type, TYPE_RULES["statement"])

    all_text = " ".join(
        [
            beat.get("label", ""),
            " ".join(beat.get("card_lines", [])),
            " ".join(beat.get("bg_lines", [])),
            beat.get("punchline_line", ""),
        ]
    )

    visuals_in = _normalize_visuals(beat.get("visuals"))
    stack_in = visuals_in.get("stack")
    if isinstance(stack_in, list) and stack_in:
        stack_specs = [
            resolve_visual_slot(
                _as_dict(item),
                concept=_as_dict(item).get("concept", f"stack_{i}"),
                role="subject",
                style_pack_id=pack,
            )
            for i, item in enumerate(stack_in)
        ]
    else:
        stack_specs = _icon_stack_from_manifest(beat, pack, manifest=raw_icons)

    resolved: dict[str, dict | list] = {}
    if stack_specs:
        resolved["stack"] = stack_specs

    # Primary panel visual (single icon when no stack)
    primary = visuals_in.get("primary") or {}
    concept = primary.get("concept")
    role = primary.get("role") or rules.get("left_role", "subject")
    if not concept:
        concept = rules.get("left_concept") or infer_concept_from_text(all_text, beat_type, role)
    if not stack_specs:
        resolved["primary"] = resolve_visual_slot(
            primary,
            concept=concept,
            role=role,
            style_pack_id=pack,
        )

    # Optional swap (punchline)
    swap = visuals_in.get("swap")
    if swap or rules.get("swap_role") or beat.get("punchline_line"):
        swap = swap or {}
        swap_role = swap.get("role") or rules.get("swap_role", "punchline")
        swap_concept = swap.get("concept") or infer_concept_from_text(
            beat.get("punchline_line", all_text), beat_type, swap_role
        )
        trigger = swap.get("trigger") or swap.get("trigger_word") or _emphasis_trigger(beat)
        resolved["swap"] = {
            **resolve_visual_slot(
                swap,
                concept=swap_concept,
                role=swap_role,
                style_pack_id=pack,
            ),
            "trigger": trigger,
        }

    beat = dict(beat)
    beat["visuals_resolved"] = resolved
    beat["style_pack"] = pack
    if beat.get("card_lines") and "card" in beat.get("layout", ""):
        beat.pop("bg_lines", None)
    return beat


def resolve_project(project: dict) -> dict:
    """Resolve visuals for every beat in a project."""
    pack = project.get("style_pack", "course_clean")
    beats = [resolve_beat_visuals(b, pack) for b in project.get("beats", [])]
    out = dict(project)
    out["beats"] = beats
    return out


def build_icons_manifest(beat: dict) -> dict[str, str]:
    """Extract iconify refs needed for a beat into icons.json format."""
    if beat.get("icons"):
        return dict(beat["icons"])
    manifest: dict[str, str] = {}
    for slot, spec in (beat.get("visuals_resolved") or {}).items():
        if not isinstance(spec, dict) or spec.get("kind") != "iconify":
            continue
        concept = spec.get("concept", slot)
        icon_id = f"icon_{concept}"
        manifest[icon_id] = spec["ref"]
    return manifest
