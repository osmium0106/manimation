"""Interpret JSON beat specs into Manim animations."""

from __future__ import annotations

import sys
from pathlib import Path

from manim import *

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "animations"))

from beat_helpers import (  # noqa: E402
    BeatScene,
    MovingBeatScene,
    CODE_BORDER,
    CODE_ERROR_HIGHLIGHT,
    CODE_ERROR_HIGHLIGHT_OPACITY,
    CODE_HIGHLIGHT_OPACITY,
    CODE_RUN_GREEN,
    normalize_code_lines,
    sanitize_code_demo_beat,
)
from beat_types import CODE_DEMO, COMPARE, LIST, apply_type_defaults, normalize_beat_type  # noqa: E402
from icon_grid import layout_icons_in_panel  # noqa: E402
from icon_triggers import line_has_trigger, resolve_icon_reveal_mode  # noqa: E402
from visual_library import load_visual  # noqa: E402
from visual_resolver import resolve_beat_visuals  # noqa: E402

from theme_loader import normalize_theme  # noqa: E402

MANIM_ROOT = ROOT
BG_PATH = MANIM_ROOT / "background" / "orange_theme_BG.png"


def _apply_bg(scene, theme=None):
    overscale = 1.25 if isinstance(scene, MovingBeatScene) else 1.0
    scene.setup_background(overscale=overscale, theme=theme)


def _normalize_text(text: str) -> str:
    return text.replace(" ", "")


def _word_in_text(text_mob, word: str) -> bool:
    text_mob = _line_text_mob(text_mob)
    text = text_mob.text if hasattr(text_mob, "text") else str(text_mob)
    return _normalize_text(word) in _normalize_text(text) or word in text


def _line_text_mob(line_mob):
    """Body Text submob for a code row (indent + body VGroup or plain line)."""
    if hasattr(line_mob, "text"):
        return line_mob
    if isinstance(line_mob, VGroup):
        for sub in line_mob.submobjects:
            if hasattr(sub, "text") and str(sub.text).strip():
                return sub
    return line_mob


def _find_word(mob, word: str):
    mob = _line_text_mob(mob)
    text = mob.text
    compact_word = _normalize_text(word)
    start = text.find(compact_word)
    if start < 0:
        return mob
    return mob[start : start + len(compact_word)]


def _emphasis_manim_color(em: dict):
    """Resolve emphasis color (named or hex) to a Manim color."""
    raw = em.get("color")
    if not raw:
        return None
    from visual_library import _resolve_color

    resolved = _resolve_color(str(raw))
    if resolved is not None:
        return resolved
    if isinstance(raw, str) and raw.startswith("#"):
        from manim import ManimColor

        return ManimColor(raw)
    return None


def _apply_emphasis_on_line(scene, line_mob, em: dict) -> None:
    """Apply word color + animation when *word* appears on *line_mob*."""
    from manim import Indicate, Wiggle, YELLOW

    word = em.get("word")
    if not word or not _word_in_text(line_mob, word):
        return
    part = _find_word(line_mob, word)
    tint = _emphasis_manim_color(em)
    if tint is not None:
        _apply_word_color(line_mob, word, tint)
    anim = em.get("animation")
    indicate_color = tint if tint is not None else YELLOW
    if anim == "wiggle":
        scene.play(Wiggle(part), run_time=0.6)
    elif anim == "indicate":
        scene.play(Indicate(part, color=indicate_color), run_time=0.55)


def _apply_word_color(text_mob, word: str, color) -> None:
    """Color an emphasized word (uses submobject slice — visible unlike set_color_by_t2c)."""
    if not _word_in_text(text_mob, word):
        return
    _find_word(text_mob, word).set_color(color)


def _camera_step(beat: dict, hook: str) -> dict | None:
    for step in beat.get("camera") or []:
        if step.get("hook") == hook:
            return step
    return None


def _run_camera(scene, beat: dict, hook: str, *, label, card=None, card_side="right", run_time=None):
    if not isinstance(scene, MovingBeatScene):
        return
    step = _camera_step(beat, hook)
    if not step:
        return
    action = step.get("action", "")
    rt = run_time or float(step.get("run_time", 0.9))
    if action == "cam_focus_left":
        scene.cam_focus_left(label, run_time=rt)
    elif action == "cam_focus_right":
        scene.cam_focus_right(label, run_time=rt)
    elif action == "cam_focus_card" and card is not None:
        scene.cam_focus_card(card, run_time=rt)
    elif action == "cam_restore":
        scene.cam_restore(run_time=rt)
    elif action == "cam_restore_fast":
        scene.cam_restore(run_time=0.5)


def _icon_side(layout: str) -> str:
    if "icon_right" in layout:
        return "right"
    if "icon_left" in layout:
        return "left"
    if "card_left" in layout:
        return "right"
    if "card_right" in layout:
        return "left"
    if "text_left" in layout:
        return "right"
    if "text_right" in layout:
        return "left"
    return "left"


def _card_side(layout: str, beat: dict) -> str:
    if beat.get("card_side"):
        return beat["card_side"]
    if "card_left" in layout:
        return "left"
    if "card_right" in layout:
        return "right"
    return "right"


def _bg_text_side(layout: str) -> str:
    if "text_right" in layout:
        return "right"
    if "text_left" in layout:
        return "left"
    return "right"


def _load_icon_panel(scene, beat: dict, label, icon_side: str, *, hide_for_sync: bool = False):
    """Load primary or multi-icon panel using invisible grid cells."""
    visuals = beat.get("visuals_resolved") or {}
    panel = scene.icon_panel_bounds(icon_side, label)
    grid_mode = beat.get("icon_grid")

    stack_specs = visuals.get("stack")
    if isinstance(stack_specs, list) and stack_specs:
        specs = stack_specs[:4]
        mobs = [load_visual(scene, spec) for spec in specs]
        group = layout_icons_in_panel(mobs, panel, mode=grid_mode)
        if hide_for_sync:
            for mob in mobs:
                mob.set_opacity(0)
            scene.add(*mobs)
            return group, mobs, specs
        return group, mobs, specs

    primary_spec = visuals.get("primary")
    swap_spec = visuals.get("swap")
    primary_mob = load_visual(scene, primary_spec) if primary_spec else None
    swap_mob = load_visual(scene, swap_spec) if swap_spec else None

    if primary_mob and swap_mob:
        layout_icons_in_panel([primary_mob], panel, mode="single")
        return primary_mob, [primary_mob, swap_mob], []

    if primary_mob:
        layout_icons_in_panel([primary_mob], panel, mode="single")
        return primary_mob, [primary_mob], []

    return None, [], []


def _build_trigger_map(stack_specs: list[dict], stack_mobs: list) -> tuple[dict[str, Mobject], list]:
    """Map trigger word → icon; return icons without triggers for batch reveal."""
    triggered: dict[str, Mobject] = {}
    untriggered: list = []
    for spec, mob in zip(stack_specs, stack_mobs):
        word = (spec.get("trigger") or "").strip().lower()
        if word:
            triggered[word] = mob
        else:
            untriggered.append(mob)
    return triggered, untriggered


def _ensure_full_frame_for_word_sync(scene, stack_count: int, reveal_mode: str) -> None:
    """Zoom out to full frame so card + icon grid are visible during word sync."""
    if reveal_mode != "on_word" or stack_count < 3:
        return
    if isinstance(scene, MovingBeatScene):
        scene.cam_restore(run_time=0.55)


def _cam_focus_icon(scene, label, icon_side: str, *, run_time: float = 0.9) -> None:
    if not isinstance(scene, MovingBeatScene):
        return
    if icon_side == "right":
        scene.cam_focus_right(label, run_time=run_time)
    else:
        scene.cam_focus_left(label, run_time=run_time)


def _stage_icon_for_entrance(scene, mob, entrance: str) -> None:
    """Keep icon off the scene until the entrance animation (hidden during camera pan)."""
    if mob is None:
        return
    if mob in scene.mobjects:
        scene.remove(mob)


def _focus_icon_then_entrance(
    scene,
    beat: dict,
    icon_panel,
    *,
    icon_side: str,
    label,
    card=None,
    card_side: str = "right",
    has_camera_spec: bool,
    cam_on: bool,
    beat_type: str,
    entrance: str,
    entrance_run_time: float = 0.45,
) -> None:
    """Pan/zoom to the icon panel first, then play the icon entrance animation."""
    if icon_panel is None:
        return
    _stage_icon_for_entrance(scene, icon_panel, entrance)
    if has_camera_spec:
        _run_camera(scene, beat, "after_icon", label=label, card=card, card_side=card_side)
    elif cam_on:
        if beat_type == LIST and card is not None and isinstance(scene, MovingBeatScene):
            scene.cam_focus_card(card, run_time=0.85)
        else:
            _cam_focus_icon(scene, label, icon_side)
    scene.play_icon_entrance(icon_panel, entrance, run_time=entrance_run_time)


def _beat_uses_camera(beat: dict, project_default: bool) -> bool:
    if "use_camera" in beat:
        return bool(beat["use_camera"])
    return project_default


def _begin_beat(scene: BeatScene, use_camera: bool) -> None:
    """Ensure each beat starts from a clean frame and default camera."""
    scene.sweep_foreground(run_time=0)
    if isinstance(scene, MovingBeatScene) and use_camera:
        frame = scene.camera.frame
        if (
            abs(frame.width - config.frame_width) > 0.05
            or abs(frame.height - config.frame_height) > 0.05
            or np.linalg.norm(frame.get_center()[:2]) > 0.05
        ):
            scene.cam_restore(run_time=0.35)


def run_code_demo_beat(scene: BeatScene, beat: dict, *, use_camera: bool = False) -> None:
    """Label + dark code window: run click → line-by-line highlight → output or error."""
    beat = sanitize_code_demo_beat(beat)
    label_text = beat.get("label", "Run code")
    label = scene.top_label(label_text)
    cam_on = _beat_uses_camera(beat, use_camera)
    has_camera_spec = bool(beat.get("camera"))

    code_lines = normalize_code_lines(beat.get("code_lines") or ['print("Hello, World!")'])
    output_text = beat.get("code_output", "")
    result = (beat.get("code_result") or "success").lower()
    success = result != "error"
    error_line = beat.get("code_error_line")
    if error_line is not None:
        error_line = int(error_line)
    elif not success:
        error_line = len(code_lines)

    scene.type_text(label, time_per_char=0.045, cursor_color=YELLOW)

    terminal, card, split_y, _, code_area_top, run_btn, title_bar = scene.empty_code_terminal_card(label)
    scene.play(GrowFromCenter(terminal), run_time=0.45)
    output_panel = terminal[2]

    pad_x = 0.38
    editor = scene.prepare_code_editor(
        card,
        split_y,
        title_bar=title_bar,
        output_panel=output_panel,
        pad_x=pad_x,
        code_area_top=code_area_top,
    )
    code_group = editor["code_group"]
    viewport_masks = scene.create_code_viewport_masks(card, title_bar, split_y)
    scene.add(code_group, viewport_masks)
    code_group.set_z_index(1)
    viewport_masks.set_z_index(3)
    scene.bring_code_chrome_to_front(terminal, run_btn, label)
    scene.wait(0.2)

    scene.play(Circumscribe(run_btn, color=WHITE, fade_out=True, time_width=0.4), run_time=0.32)
    scene.animate_run_button_click(run_btn)
    if has_camera_spec:
        _run_camera(scene, beat, "after_run", label=label, card=card)
    elif cam_on and isinstance(scene, MovingBeatScene):
        scene.cam_focus_card(card, run_time=0.85)

    active_highlight = None
    stopped_on_error = False
    output_shown = False
    line_rows: list = []
    output_body = None

    for raw in code_lines:
        is_blank = not str(raw).strip()
        row = scene.reveal_code_line(editor, raw, type_body=not is_blank)
        line_rows.append(row)

    scene.bring_code_chrome_to_front(terminal, run_btn, label)
    scene.scroll_code_editor_home(editor, run_time=0.5)
    scene.wait(0.3)

    for i, raw in enumerate(code_lines):
        row = line_rows[i]
        if not str(raw).strip():
            continue

        if active_highlight is not None:
            scene.remove(active_highlight)
            active_highlight = None

        scene.scroll_code_editor_to_line(editor, row, run_time=0.22)
        scene.wait(0.05)

        is_error = not success and (i + 1) == error_line
        target_opacity = CODE_ERROR_HIGHLIGHT_OPACITY if is_error else CODE_HIGHLIGHT_OPACITY
        hl = scene.code_line_highlight(row, error=is_error)
        hl.set_fill_opacity(0)
        active_highlight = hl
        scene.place_code_line_highlight(row, hl)
        scene.play(hl.animate.set_fill_opacity(target_opacity), run_time=0.1)
        scene.wait(0.12)

        hook = f"after_line_{i + 1}"
        if has_camera_spec:
            _run_camera(scene, beat, hook, label=label, card=card)
        elif cam_on and i == 0 and isinstance(scene, MovingBeatScene):
            scene.cam_focus_card(card, run_time=0.75)

        if is_error:
            stopped_on_error = True
            scene.play(
                hl.animate.set_fill(CODE_ERROR_HIGHLIGHT).set_fill_opacity(CODE_ERROR_HIGHLIGHT_OPACITY + 0.12),
                run_time=0.1,
            )
            error_display = beat.get("code_error_message") or output_text or "Error"
            scene.clear_code_from_output_zone(editor, output_panel)
            output_group, output_body = scene.present_code_output(
                error_display,
                card,
                split_y,
                success=False,
                type_error=True,
            )
            output_group.set_z_index(11)
            scene.bring_code_chrome_to_front(terminal, run_btn, label, output_group)
            scene.fast_shake(terminal)
            scene.play(Wiggle(output_body), run_time=0.35)
            output_shown = True
            break

        scene.play(hl.animate.set_fill_opacity(0), run_time=0.1)
        scene.remove(hl)
        active_highlight = None

    if active_highlight is not None and not stopped_on_error:
        scene.play(active_highlight.animate.set_fill_opacity(0), run_time=0.08)
        scene.remove(active_highlight)

    if has_camera_spec:
        _run_camera(scene, beat, "after_code", label=label, card=card)
    elif cam_on and isinstance(scene, MovingBeatScene):
        scene.cam_focus_card(card, run_time=0.85)

    if success:
        display = output_text or "Ran successfully"
        scene.clear_code_from_output_zone(editor, output_panel)
        output_group, output_body = scene.present_code_output(
            display,
            card,
            split_y,
            success=True,
        )
        output_group.set_z_index(11)
        scene.bring_code_chrome_to_front(terminal, run_btn, label, output_group)
    elif not output_shown:
        display = beat.get("code_error_message") or output_text or "Error"
        scene.clear_code_from_output_zone(editor, output_panel)
        output_group, output_body = scene.present_code_output(
            display,
            card,
            split_y,
            success=False,
            type_error=True,
        )
        output_group.set_z_index(11)
        scene.bring_code_chrome_to_front(terminal, run_btn, label, output_group)
        scene.play(Wiggle(output_body), run_time=0.35)
    else:
        scene.bring_code_chrome_to_front(terminal, run_btn, label)

    if has_camera_spec:
        _run_camera(scene, beat, "after_output", label=label, card=card)

    for em in beat.get("emphasis") or []:
        for line_mob in line_rows:
            _apply_emphasis_on_line(scene, line_mob, em)

    scene.wait(float(beat.get("hold", 1.5)))

    if has_camera_spec:
        _run_camera(scene, beat, "exit", label=label, card=card)
    elif cam_on and isinstance(scene, MovingBeatScene):
        scene.cam_restore(run_time=0.7)

    if not beat.get("continue_beat"):
        scene.sweep_foreground(run_time=0.55)


def run_compare_beat(scene: BeatScene, beat: dict, *, use_camera: bool = False) -> None:
    """Dual card layout — left vs right comparison."""
    label_text = beat.get("label", "Compare")
    label = scene.top_label(label_text)
    cam_on = _beat_uses_camera(beat, use_camera)
    has_camera_spec = bool(beat.get("camera"))

    left_lines = beat.get("left_lines") or beat.get("card_lines") or ["Before"]
    right_lines = beat.get("right_lines") or beat.get("bg_lines") or ["After"]

    left_card = scene.empty_card(side="left", label=label)
    right_card = scene.empty_card(side="right", label=label)

    scene.type_text(label, time_per_char=0.045, cursor_color=YELLOW)
    scene.play(GrowFromCenter(left_card), GrowFromCenter(right_card), run_time=0.4)

    left_group = scene.card_text_in(left_card, *left_lines)
    right_group = scene.card_text_in(right_card, *right_lines)

    for i, line in enumerate(left_group):
        scene.type_text(line, time_per_char=0.05)
        if has_camera_spec:
            _run_camera(scene, beat, "after_line_1" if i == 0 else f"after_line_{i + 1}", label=label, card=left_card, card_side="left")
        elif cam_on and i == 0 and isinstance(scene, MovingBeatScene):
            scene.cam_focus_left(label, run_time=0.85)

    for i, line in enumerate(right_group):
        scene.type_text(line, time_per_char=0.05)
        hook = "after_line_2" if i == 0 else f"after_line_{len(left_group) + i + 1}"
        if has_camera_spec:
            _run_camera(scene, beat, hook, label=label, card=right_card, card_side="right")
        elif cam_on and i == 0 and isinstance(scene, MovingBeatScene):
            scene.cam_focus_right(label, run_time=0.85)

    scene.wait(float(beat.get("hold", 1.2)))

    if has_camera_spec:
        _run_camera(scene, beat, "exit", label=label, card=right_card)
    elif cam_on and isinstance(scene, MovingBeatScene):
        scene.cam_restore(run_time=0.7)

    if not beat.get("continue_beat"):
        scene.sweep_foreground(run_time=0.55)


def run_panel_beat(scene: BeatScene, beat: dict, *, use_camera: bool = False) -> None:
    """Standard card/icon panel beat (statement, question, joke, list, recap, explain)."""
    layout = beat.get("layout", "card_right_icon_left")
    label_text = beat.get("label", "Beat")
    label = scene.top_label(label_text)
    cam_on = _beat_uses_camera(beat, use_camera)
    has_camera_spec = bool(beat.get("camera"))

    card = None
    card_lines_mobs = []
    bg_lines_mobs = None
    punchline_mob = None

    has_card = "card" in layout or beat.get("card_lines") or beat.get("list_lines")
    card_side = _card_side(layout, beat)
    icon_side = _icon_side(layout)

    # Card layouts: treat bg_lines as card content when card_lines missing.
    card_lines = beat.get("card_lines")
    if has_card and not card_lines and beat.get("bg_lines"):
        card_lines = beat["bg_lines"]

    beat_type = normalize_beat_type(beat.get("type"))
    list_lines = beat.get("list_lines")

    if has_card and (card_lines or list_lines):
        card = scene.empty_card(
            side=card_side,
            width=float(beat.get("card_width", 5.6)),
            height=float(beat.get("card_height", 5.0)),
            label=label,
        )
        all_lines = list(list_lines or card_lines or [])
        if beat.get("punchline_line") and beat["punchline_line"] not in all_lines:
            all_lines.append(beat["punchline_line"])

        if beat_type == LIST or list_lines:
            source = list_lines or all_lines
            lines_group = scene.list_lines_group(*source, max_width=card.width - 2 * 0.45)
            for row in lines_group:
                row[1].set_opacity(0)
        else:
            lines_group = scene.card_lines(*all_lines, max_width=card.width - 2 * 0.45)

        scene.place_card_content(lines_group, card)

        punchline = beat.get("punchline_line")
        if punchline and punchline in all_lines:
            pi = all_lines.index(punchline)
            card_lines_mobs = [lines_group[i] for i in range(len(all_lines)) if i != pi]
            punchline_mob = lines_group[pi]
        else:
            card_lines_mobs = list(lines_group)
            punchline_mob = None
    elif beat.get("bg_lines"):
        bg_side = _bg_text_side(layout)
        bg_lines_mobs = scene.bg_text_in(bg_side, label, *beat["bg_lines"])

    stack_specs = (beat.get("visuals_resolved") or {}).get("stack") or []
    icon_reveal = resolve_icon_reveal_mode(beat, stack_specs)
    use_word_sync = icon_reveal == "on_word" and bool(stack_specs)
    has_icon_triggers = any(s.get("trigger") for s in stack_specs)

    icon_panel, icon_mobs, _ = _load_icon_panel(
        scene,
        beat,
        label,
        icon_side,
        hide_for_sync=use_word_sync and has_icon_triggers,
    )
    primary_mob = icon_mobs[0] if len(icon_mobs) == 1 else icon_panel
    swap_mob = icon_mobs[1] if len(icon_mobs) > 1 and not isinstance(icon_panel, VGroup) else None
    stack_mobs = icon_mobs if isinstance(icon_panel, VGroup) else []

    trigger_map: dict[str, Mobject] = {}
    untriggered_icons: list = []
    revealed_words: set[str] = set()
    if use_word_sync and has_icon_triggers and stack_mobs:
        trigger_map, untriggered_icons = _build_trigger_map(stack_specs, stack_mobs)
        _ensure_full_frame_for_word_sync(scene, len(stack_specs), icon_reveal)

    batch_icon_reveal = icon_panel and not (use_word_sync and has_icon_triggers)

    scene.type_text(label, time_per_char=0.045, cursor_color=YELLOW)

    primary_shown = False
    if batch_icon_reveal and bg_lines_mobs is not None:
        entrance = beat.get("icon_entrance") or "fade_in"
        _focus_icon_then_entrance(
            scene,
            beat,
            icon_panel,
            icon_side=icon_side,
            label=label,
            card=card,
            card_side=card_side,
            has_camera_spec=has_camera_spec,
            cam_on=cam_on,
            beat_type=beat_type,
            entrance=entrance,
        )
        primary_shown = True
        scene.wait(0.4)

    if card:
        scene.play(GrowFromCenter(card), run_time=0.4)

    trigger_words = list(trigger_map.keys())
    typed: list = []
    is_list_beat = beat_type == LIST or bool(list_lines)
    if card_lines_mobs:
        for i, line in enumerate(card_lines_mobs):
            if is_list_beat and isinstance(line, VGroup) and len(line) >= 2:
                check, text = line[0], line[1]
                scene.play(FadeIn(check, scale=1.1), run_time=0.25)
                scene.type_text(text, time_per_char=0.05)
                typed.append(line)
            elif trigger_map and line_has_trigger(line.text, trigger_words):
                revealed_words = scene.type_line_with_icon_triggers(
                    line,
                    trigger_map,
                    time_per_char=0.05,
                    cursor_color=YELLOW,
                    revealed=revealed_words,
                )
            else:
                scene.type_text(line, time_per_char=0.05)
            typed.append(line)
            for em in beat.get("emphasis") or []:
                _apply_emphasis_on_line(scene, line, em)
            hook = f"after_line_{i + 1}"
            if has_camera_spec:
                _run_camera(scene, beat, hook, label=label, card=card, card_side=card_side)
            elif cam_on and card is not None and isinstance(scene, MovingBeatScene):
                if beat_type == LIST:
                    scene.cam_focus_card(card, run_time=0.85)
                elif i == 1:
                    fn = scene.cam_focus_right if card_side == "right" else scene.cam_focus_left
                    fn(label, run_time=0.9)

    if bg_lines_mobs is not None:
        for i, line in enumerate(bg_lines_mobs):
            if trigger_map and line_has_trigger(line.text, trigger_words):
                revealed_words = scene.type_line_with_icon_triggers(
                    line,
                    trigger_map,
                    time_per_char=0.05,
                    cursor_color=WHITE,
                    revealed=revealed_words,
                )
            else:
                scene.type_text(line, time_per_char=0.05)
            hook = f"after_line_{i + 1}"
            if has_camera_spec:
                _run_camera(scene, beat, hook, label=label, card=card, card_side=card_side)
            elif cam_on and i == 0 and isinstance(scene, MovingBeatScene):
                scene.cam_focus_right(label, run_time=0.9)
            if beat.get("emphasis"):
                for em in beat["emphasis"]:
                    _apply_emphasis_on_line(scene, line, em)

    if batch_icon_reveal and not primary_shown:
        entrance = beat.get("icon_entrance") or "fade_in"
        _focus_icon_then_entrance(
            scene,
            beat,
            icon_panel,
            icon_side=icon_side,
            label=label,
            card=card,
            card_side=card_side,
            has_camera_spec=has_camera_spec,
            cam_on=cam_on,
            beat_type=beat_type,
            entrance=entrance,
        )
    elif use_word_sync and has_icon_triggers:
        still_hidden = [
            m
            for m in (*untriggered_icons, *trigger_map.values())
            if (m.get_opacity() if m.get_opacity() is not None else 1.0) < 0.5
        ]
        if still_hidden:
            scene.play(*[FadeIn(mob) for mob in still_hidden], run_time=0.4)
        if has_camera_spec:
            _run_camera(scene, beat, "after_icon", label=label, card=card, card_side=card_side)
        elif cam_on and len(stack_specs) >= 3 and isinstance(scene, MovingBeatScene):
            scene.cam_restore(run_time=0.5)

    # Punchline sequence
    if punchline_mob and card:
        if typed:
            scene.play(*[FadeOut(m) for m in typed], run_time=0.4)
        scene.place_card_line(punchline_mob, card, centered=True)
        if primary_mob and swap_mob:
            scene.play(FadeOut(primary_mob), FadeIn(swap_mob), run_time=0.4)
        elif stack_mobs and swap_mob:
            scene.play(FadeOut(icon_panel), FadeIn(swap_mob), run_time=0.4)
        if has_camera_spec:
            _run_camera(scene, beat, "punchline", label=label, card=card, card_side=card_side)
        elif cam_on and isinstance(scene, MovingBeatScene):
            scene.cam_focus_card(card, run_time=0.9)
        scene.type_text(punchline_mob, time_per_char=0.05)
        for em in beat.get("emphasis") or []:
            word = em.get("word")
            if word and _word_in_text(punchline_mob, word):
                part = _find_word(punchline_mob, word)
                tint = _emphasis_manim_color(em)
                if tint is not None:
                    _apply_word_color(punchline_mob, word, tint)
                if em.get("animation") == "wiggle":
                    extras = [Wiggle(part)]
                    if swap_mob:
                        extras.append(Wiggle(swap_mob))
                    scene.play(*extras, run_time=0.6)
                elif em.get("animation") == "indicate":
                    indicate_color = tint if tint is not None else YELLOW
                    scene.play(Indicate(part, color=indicate_color), run_time=0.55)
    elif punchline_mob:
        scene.type_text(punchline_mob, time_per_char=0.05)

    scene.wait(float(beat.get("hold", 1.2)))

    if has_camera_spec:
        _run_camera(scene, beat, "exit", label=label, card=card, card_side=card_side)
    elif cam_on and isinstance(scene, MovingBeatScene):
        scene.cam_restore(run_time=0.7)

    # One unified fade: card, card text, icons, and detached emphasis slices together.
    if not beat.get("continue_beat"):
        scene.sweep_foreground(run_time=0.55)


def run_beat_from_spec(scene: BeatScene, beat: dict, *, use_camera: bool = False) -> None:
    beat = apply_type_defaults(resolve_beat_visuals(dict(beat)))
    _begin_beat(scene, use_camera)
    beat_type = normalize_beat_type(beat.get("type"))
    layout = beat.get("layout", "")

    if beat_type == CODE_DEMO or layout in ("code_full_card", "code_in_card", "code_left_card_right"):
        run_code_demo_beat(scene, beat, use_camera=use_camera)
        return
    if beat_type == COMPARE or layout == "dual_card":
        run_compare_beat(scene, beat, use_camera=use_camera)
        return

    run_panel_beat(scene, beat, use_camera=use_camera)


def make_scene_class(project: dict, use_camera: bool = False):
    """Dynamically build a Manim Scene class from a project dict."""

    class GeneratedScene(MovingBeatScene if use_camera else BeatScene):
        def construct(self):
            _apply_bg(self)
            beats = project.get("beats", [])
            for i, beat in enumerate(beats):
                run_beat_from_spec(self, beat, use_camera=use_camera)
                if i < len(beats) - 1:
                    self.beat_transition()

    GeneratedScene.__name__ = project.get("scene_class", "GeneratedScene")
    return GeneratedScene
