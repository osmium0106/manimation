"""Export project beats to beat-script markdown."""

from __future__ import annotations

import json
from typing import Any


def _lines_block(title: str, lines: list[str]) -> str:
    if not lines:
        return ""
    body = "\n".join(f"  {line}" for line in lines)
    return f"─── {title} ───\n{body}\n"


def beat_to_script_block(beat: dict, index: int) -> str:
    slug = beat.get("label", f"beat_{index}").lower().replace(" ", "_")[:40]
    slug = "".join(c if c.isalnum() or c == "_" else "_" for c in slug)
    lines = [
        f"### BEAT {index} — {slug}",
        f"TYPE:       {beat.get('type', 'statement')}",
        f"LAYOUT:     {beat.get('layout', 'card_right_icon_left')}",
    ]
    if beat.get("use_camera"):
        lines.append("CAMERA:     yes")
    if beat.get("hold") is not None:
        lines.append(f"HOLD:       {beat.get('hold')}")
    if beat.get("icon_entrance"):
        lines.append(f"ICON_ENTRANCE: {beat.get('icon_entrance')}")
    if beat.get("continue_beat"):
        lines.append("CONTINUE:   yes")

    lines.append("")
    lines.append(f'LABEL:      {beat.get("label", "Beat")}')

    if beat.get("card_lines"):
        lines.append(_lines_block("CONTENT", beat["card_lines"]).rstrip())
    if beat.get("bg_lines"):
        lines.append(_lines_block("CONTENT (white, on BG)", beat["bg_lines"]).rstrip())
    if beat.get("list_lines"):
        lines.append(_lines_block("LIST", beat["list_lines"]).rstrip())
    if beat.get("left_lines") or beat.get("right_lines"):
        if beat.get("left_lines"):
            lines.append(_lines_block("TEXT (left card)", beat["left_lines"]).rstrip())
        if beat.get("right_lines"):
            lines.append(_lines_block("TEXT (right card)", beat["right_lines"]).rstrip())
    if beat.get("punchline_line"):
        lines.append(f"PUNCHLINE:  {beat['punchline_line']}")

    emphasis = beat.get("emphasis") or []
    if emphasis:
        lines.append("")
        lines.append("─── EMPHASIS ───")
        for em in emphasis:
            if not isinstance(em, dict) or not em.get("word"):
                continue
            color = em.get("color", "YELLOW")
            animation = em.get("animation", "indicate")
            lines.append(f"word: {em['word']} | color: {color} | animation: {animation}")

    camera = beat.get("camera") or []
    if camera:
        lines.append("")
        lines.append("─── CAMERA ───")
        for step in camera:
            if not isinstance(step, dict):
                continue
            action = step.get("action")
            hook = step.get("hook")
            if action and hook:
                lines.append(f"{action}: {hook}")

    if beat.get("code_lines"):
        lines.append("─── CODE ───")
        if beat.get("code_language"):
            lines.append(f"language: {beat['code_language']}")
        if beat.get("code_result"):
            lines.append(f"result: {beat['code_result']}")
        if beat.get("code_output"):
            lines.append(f"output: {beat['code_output']}")
        lines.append("lines:")
        for cl in beat["code_lines"]:
            lines.append(f"  {cl}")

    visuals = beat.get("visuals") or {}
    primary = visuals.get("primary")
    if primary:
        lines.append("")
        lines.append("─── VISUALS ───")
        if isinstance(primary, dict):
            if primary.get("ref"):
                lines.append(f"primary: {primary['ref']}")
            elif primary.get("concept"):
                lines.append(f"primary: {primary['concept']}")
            elif primary.get("description"):
                lines.append(f"primary: {primary['description']}")
            if primary.get("color"):
                lines.append(f"icon_color: {primary['color']}")
        swap = visuals.get("swap")
        if isinstance(swap, dict):
            if swap.get("ref"):
                lines.append(f"swap: {swap['ref']}")
            elif swap.get("concept"):
                lines.append(f"swap: {swap['concept']}")
    stack = (beat.get("visuals_resolved") or {}).get("stack") or visuals.get("stack")
    if isinstance(stack, list):
        for i, spec in enumerate(stack[:4], 1):
            ref = spec.get("ref") or spec.get("concept") or spec.get("description")
            if ref:
                trigger = spec.get("trigger")
                suffix = f" | trigger: {trigger}" if trigger else ""
                lines.append(f"icon_{i}: {ref}{suffix}")

    return "\n".join(lines)


def beats_to_script(project: dict) -> str:
    """Serialize project beats to beat-script markdown."""
    header = [
        f"# {project.get('name', 'Untitled')}",
        f"NAME:       {project.get('name', 'Untitled')}",
        f"THEME:      {project.get('theme_id', 'builtin_orange')}",
        f"STYLE_PACK: {project.get('style_pack', 'course_clean')}",
        f"CAMERA:     {'moving' if project.get('use_camera') else 'static'}",
    ]
    brief = project.get("style_brief")
    if brief:
        header.append(f"BRIEF:      {brief}")
    header.append("")

    blocks = [beat_to_script_block(b, i + 1) for i, b in enumerate(project.get("beats") or [])]
    return "\n".join(header) + "\n\n".join(blocks) + ("\n" if blocks else "")
