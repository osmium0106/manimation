"""Shared layout, typing, and camera helpers for course beats."""

from __future__ import annotations

import re
from pathlib import Path

from manim import *
from manim.utils.rate_functions import smooth
from manim.utils import rate_functions

MANIM_ROOT = Path(__file__).resolve().parent.parent
BG_PATH = str(MANIM_ROOT / "background" / "orange_theme_BG.png")
LABEL_TOP_BUFF = 0.9
LABEL_CONTENT_GAP = 0.25
PANEL_FRAME_WIDTH = 7.5
ICON_PANEL_PAD_X = 0.35
ICON_PANEL_PAD_Y = 0.25
CARD_PAD_X = 0.45
CARD_PAD_Y = 0.35
CONTENT_MARGIN_X = 0.45
CONTENT_MARGIN_Y = 0.25
CODE_OUTPUT_FRACTION = 0.20

# Carbon / One Dark-inspired code window palette
CODE_BG = "#282c34"
CODE_BG_DEEP = "#21252b"
CODE_BORDER = "#3e4451"
CODE_TEXT = "#abb2bf"
CODE_KEYWORD = "#c678dd"
CODE_FUNC = "#e06c75"
CODE_STRING = "#98c379"
CODE_NUMBER = "#d19a66"
CODE_CURSOR = "#528bff"
CODE_DOT_COLORS = ("#ff5f56", "#ffbd2e", "#27c93f")
CODE_HIGHLIGHT = "#528bff"
CODE_HIGHLIGHT_OPACITY = 0.18
CODE_ERROR_HIGHLIGHT = "#e06c75"
CODE_ERROR_HIGHLIGHT_OPACITY = 0.28
CODE_RUN_GREEN = "#98c379"
CODE_RUN_GREEN_DARK = "#6e9455"
PYTHON_KEYWORDS = frozenset(
    {
        "and",
        "as",
        "assert",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "False",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "None",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "True",
        "try",
        "while",
        "with",
        "yield",
    }
)


def normalize_code_lines(lines: list[str] | None) -> list[str]:
    """Preserve indentation; expand tabs to 4 spaces."""
    if not lines:
        return []
    out: list[str] = []
    for raw in lines:
        text = str(raw).expandtabs(4).rstrip()
        out.append(text)
    return out


def _extract_error_metadata_from_line(raw: str) -> dict | None:
    """Detect error JSON/dict strings accidentally placed in code_lines."""
    s = str(raw).strip()
    if not s or ("error_message" not in s and "error_line" not in s):
        return None
    if not (s.startswith("{") or s.startswith("'") or "error_message" in s):
        return None

    import ast

    try:
        obj = ast.literal_eval(s)
        if isinstance(obj, dict):
            msg = obj.get("error_message") or obj.get("error")
            line = obj.get("error_line")
            return {
                "error_message": str(msg).strip() if msg else None,
                "error_line": int(line) if line is not None else None,
            }
    except (ValueError, SyntaxError, TypeError):
        pass

    msg_m = re.search(r"""error_message['"]?\s*:\s*['"](.+?)['"]""", s)
    line_m = re.search(r"""error_line['"]?\s*:\s*(\d+)""", s)
    if msg_m or line_m:
        return {
            "error_message": msg_m.group(1).strip() if msg_m else None,
            "error_line": int(line_m.group(1)) if line_m else None,
        }
    return None


def sanitize_code_demo_beat(beat: dict) -> dict:
    """Strip error metadata from code_lines; keep code_error_* fields on the beat."""
    out = dict(beat)
    lines = normalize_code_lines(out.get("code_lines"))
    cleaned: list[str] = []
    for ln in lines:
        meta = _extract_error_metadata_from_line(ln)
        if meta:
            if meta.get("error_message") and not out.get("code_error_message"):
                out["code_error_message"] = meta["error_message"]
            if meta.get("error_line") is not None and out.get("code_error_line") is None:
                out["code_error_line"] = int(meta["error_line"])
            continue
        cleaned.append(ln)
    out["code_lines"] = cleaned
    result = (out.get("code_result") or "success").lower()
    if result == "error" and not out.get("code_error_message"):
        out["code_error_message"] = out.get("code_output") or "Error"
    return out


def _safe_code_text(text: str) -> str:
    """Manim Text needs at least one character to layout."""
    return text if text else " "


def _display_code_line(raw: str) -> str:
    """Legacy helper — prefer _code_line_parts for layout rows."""
    expanded = str(raw).expandtabs(4).rstrip()
    if not expanded.strip():
        return " "
    leading = len(expanded) - len(expanded.lstrip(" "))
    body = expanded.lstrip(" ")
    return (" " * leading) + body


class BeatLayoutMixin:
    def setup_background(self, overscale: float = 1.0):
        bg = ImageMobject(BG_PATH)
        bg.scale_to_fit_width(config.frame_width * overscale)
        bg.move_to(ORIGIN)
        self.add(bg)

    def left_center(self):
        return LEFT * (config.frame_width / 4)

    def right_center(self):
        return RIGHT * (config.frame_width / 4)

    def top_label(self, text):
        lbl = Text(text, font_size=48, color=WHITE, weight=BOLD)
        lbl.to_edge(UP, buff=LABEL_TOP_BUFF)
        return lbl

    def content_center_y(self, label: Mobject) -> float:
        frame_bottom = -config.frame_height / 2
        content_top = label.get_bottom()[1] - LABEL_CONTENT_GAP
        return (content_top + frame_bottom) / 2

    def panel_anchor(self, side: str, label: Mobject) -> np.ndarray:
        x = self.right_center()[0] if side == "right" else self.left_center()[0]
        y = self.content_center_y(label)
        return np.array([x, y, 0.0])

    def icon_panel_bounds(self, side: str, label: Mobject) -> dict:
        """Axis-aligned bounds for the icon half-panel below the label."""
        anchor = self.panel_anchor(side, label)
        width = config.frame_width / 2 - 2 * ICON_PANEL_PAD_X
        frame_bottom = -config.frame_height / 2
        content_top = label.get_bottom()[1] - LABEL_CONTENT_GAP
        height = content_top - frame_bottom - 2 * ICON_PANEL_PAD_Y
        return {
            "center": anchor,
            "width": width,
            "height": height,
            "left": anchor[0] - width / 2,
            "bottom": anchor[1] - height / 2,
        }

    def on_card(self, text, font_size=28):
        return Text(text, font_size=font_size, color=BLACK, weight=BOLD)

    def card_lines(self, *lines, font_size=28, max_width=None):
        group = VGroup(*[self.on_card(line, font_size=font_size) for line in lines])
        if max_width is not None:
            for line in group:
                if line.width > max_width:
                    line.scale(max_width / line.width)
        group.arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        return group

    def place_card_content(self, content: Mobject, card: Mobject, pad_x=CARD_PAD_X, pad_y=CARD_PAD_Y):
        """Fit text block inside card with inner padding."""
        max_w = card.width - 2 * pad_x
        max_h = card.height - 2 * pad_y

        if isinstance(content, VGroup):
            for mob in content:
                if mob.width > max_w:
                    mob.scale(max_w / mob.width)
            content.arrange(DOWN, buff=0.22, aligned_edge=LEFT)

        if content.width > max_w:
            content.scale(max_w / content.width)
        if content.height > max_h:
            content.scale(max_h / content.height)

        content.move_to(card.get_center())
        content.align_to(card.get_left() + RIGHT * pad_x, LEFT)
        return content

    def card_text_in(self, card: Mobject, *lines, font_size=28):
        """Build card lines sized and padded to stay inside the card."""
        max_w = card.width - 2 * CARD_PAD_X
        group = self.card_lines(*lines, font_size=font_size, max_width=max_w)
        return self.place_card_content(group, card)

    def place_card_line(self, line: Mobject, card: Mobject, *, centered=False):
        """Position a single line inside card with horizontal padding."""
        max_w = card.width - 2 * CARD_PAD_X
        if line.width > max_w:
            line.scale(max_w / line.width)
        line.align_to(card.get_left() + RIGHT * CARD_PAD_X, LEFT)
        if centered:
            line.move_to([line.get_center()[0], card.get_center()[1], 0])
        return line

    def on_bg(self, text, font_size=36):
        return Text(text, font_size=font_size, color=WHITE, weight=BOLD)

    def bg_lines(self, *lines, font_size=36):
        group = VGroup(*[self.on_bg(line, font_size=font_size) for line in lines])
        group.arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        return group

    def shape_question(self, radius=0.8):
        circle = Circle(radius=radius, color=WHITE, stroke_width=3)
        mark = Text("?", font_size=90, color=YELLOW, weight=BOLD)
        mark.move_to(circle.get_center())
        return VGroup(circle, mark)

    def content_region_bounds(self, label: Mobject) -> dict:
        """Full-width content area below the label (margins preserved)."""
        frame_left = -config.frame_width / 2 + CONTENT_MARGIN_X
        frame_right = config.frame_width / 2 - CONTENT_MARGIN_X
        frame_bottom = -config.frame_height / 2 + CONTENT_MARGIN_Y
        content_top = label.get_bottom()[1] - LABEL_CONTENT_GAP
        width = frame_right - frame_left
        height = content_top - frame_bottom
        center_x = (frame_left + frame_right) / 2
        center_y = (content_top + frame_bottom) / 2
        return {
            "left": frame_left,
            "right": frame_right,
            "bottom": frame_bottom,
            "top": content_top,
            "width": width,
            "height": height,
            "center_x": center_x,
            "center_y": center_y,
        }

    def empty_code_terminal_card(self, label: Mobject):
        """Single full-width dark code window with 80/20 code/output split."""
        bounds = self.content_region_bounds(label)
        w, h = bounds["width"], bounds["height"]
        title_h = min(0.42, h * 0.08)

        outer = RoundedRectangle(
            width=w,
            height=h,
            corner_radius=0.18,
            fill_color=CODE_BG,
            fill_opacity=1,
            stroke_color=CODE_BORDER,
            stroke_width=1.5,
        )
        outer.move_to([bounds["center_x"], bounds["center_y"], 0])

        title_bar = RoundedRectangle(
            width=w - 0.04,
            height=title_h,
            corner_radius=0.16,
            fill_color=CODE_BG_DEEP,
            fill_opacity=1,
            stroke_width=0,
        )
        title_bar.move_to(outer.get_top() + DOWN * (title_h / 2 + 0.02))

        dots = VGroup(
            *[
                Dot(radius=0.045, color=color).move_to(
                    title_bar.get_left() + RIGHT * (0.28 + i * 0.17) + DOWN * 0.02
                )
                for i, color in enumerate(CODE_DOT_COLORS)
            ]
        )

        output_h = h * CODE_OUTPUT_FRACTION
        split_y = outer.get_bottom()[1] + output_h

        output_panel = RoundedRectangle(
            width=w - 0.06,
            height=output_h - 0.04,
            corner_radius=0.14,
            fill_color=CODE_BG_DEEP,
            fill_opacity=1,
            stroke_width=0,
        )
        output_panel.move_to(
            [
                outer.get_center()[0],
                outer.get_bottom()[1] + output_h / 2,
                0,
            ]
        )

        divider = Line(
            outer.get_left() + RIGHT * 0.1,
            outer.get_right() + LEFT * 0.1,
            color=CODE_BORDER,
            stroke_width=1.0,
        )
        divider.move_to([outer.get_center()[0], split_y, 0])

        run_btn = self.code_run_button()
        run_btn.move_to(title_bar.get_right() + LEFT * 0.32 + DOWN * 0.02)

        terminal = VGroup(outer, title_bar, output_panel, divider, dots, run_btn)
        code_area_top = title_bar.get_bottom()[1] - 0.14
        return terminal, outer, split_y, output_h, code_area_top, run_btn, title_bar

    def create_code_viewport_masks(
        self,
        card: Mobject,
        title_bar: Mobject,
        split_y: float,
        *,
        corner_radius: float = 0.18,
        side_inset: float = 0.08,
    ) -> VGroup:
        """Thin edge strips that hide scrolled code — never cover the label or duplicate the title bar."""
        clip_w = max(card.width - 0.04, 0.5)
        cx = card.get_center()[0]
        viewport_top = title_bar.get_bottom()[1] - 0.04

        strip_h = 0.14
        top_strip = Rectangle(
            width=clip_w,
            height=strip_h,
            fill_color=CODE_BG,
            fill_opacity=1,
            stroke_width=0,
        )
        top_strip.move_to([cx, viewport_top + strip_h / 2 - 0.02, 0])

        divider_h = 0.06
        divider_mask = Rectangle(
            width=clip_w,
            height=divider_h,
            fill_color=CODE_BG_DEEP,
            fill_opacity=1,
            stroke_width=0,
        )
        divider_mask.move_to([cx, split_y - divider_h / 2 - 0.02, 0])

        return VGroup(top_strip, divider_mask)

    def bring_code_chrome_to_front(
        self,
        terminal: VGroup,
        run_btn: Mobject,
        label: Mobject | None = None,
        *extra,
    ) -> None:
        """Keep terminal chrome and controls above code + viewport masks."""
        outer = terminal[0]
        title_bar = terminal[1]
        output_panel = terminal[2]
        divider = terminal[3]
        dots = terminal[4]

        # Full card fill must stay behind code — raising it hides all typed text.
        outer.set_z_index(0)
        output_panel.set_z_index(6)
        divider.set_z_index(11)
        title_bar.set_z_index(11)
        dots.set_z_index(12)
        run_btn.set_z_index(12)
        if label is not None:
            label.set_z_index(20)

        for mob in (output_panel, divider, title_bar, dots, run_btn, label, *extra):
            if mob is not None:
                self.bring_to_front(mob)

    def code_run_button(self) -> VGroup:
        """Green play / run button for the code window title bar."""
        bg = Circle(radius=0.11, fill_color=CODE_RUN_GREEN, fill_opacity=1, stroke_width=0)
        tri = Triangle(color=WHITE, fill_opacity=1, stroke_width=0).scale(0.085)
        tri.rotate(-PI / 2)
        tri.move_to(bg.get_center() + RIGHT * 0.015)
        return VGroup(bg, tri)

    def code_line_highlight(
        self,
        line_mob: Mobject,
        *,
        error: bool = False,
        pad_x: float = 0.08,
        pad_y: float = 0.04,
    ) -> RoundedRectangle:
        color = CODE_ERROR_HIGHLIGHT if error else CODE_HIGHLIGHT
        opacity = CODE_ERROR_HIGHLIGHT_OPACITY if error else CODE_HIGHLIGHT_OPACITY
        width = max(line_mob.width + 2 * pad_x, 0.2)
        height = max(line_mob.height + 2 * pad_y, 0.12)
        rect = RoundedRectangle(
            width=width,
            height=height,
            corner_radius=0.04,
            fill_color=color,
            fill_opacity=opacity,
            stroke_width=0,
        )
        rect.move_to(line_mob)
        if line_mob.get_all_points().size:
            rect.set_z_index((line_mob.z_index if line_mob.z_index else 0) - 1)
        return rect

    def place_code_line_highlight(self, line_mob: Mobject, highlight: Mobject) -> None:
        """Draw highlight behind syntax-colored code text."""
        line_mob.set_z_index(2)
        highlight.set_z_index(1)
        self.add(highlight, line_mob)
        self.bring_to_front(line_mob)

    def animate_run_button_click(self, run_btn: Mobject, *, run_time: float = 0.38):
        """Visible press + ripple click on the run button."""
        self.bring_to_front(run_btn)
        center = run_btn.get_center()
        ripple = Circle(
            radius=0.11,
            color=WHITE,
            stroke_width=2.5,
            fill_opacity=0,
        ).move_to(center)
        ripple.set_z_index(run_btn.z_index + 1 if run_btn.z_index else 3)
        self.add(ripple)

        btn_bg = run_btn[0] if isinstance(run_btn, VGroup) and len(run_btn) > 0 else run_btn
        self.play(
            run_btn.animate.scale(0.78),
            btn_bg.animate.set_fill(CODE_RUN_GREEN_DARK),
            ripple.animate.scale(2.2).set_stroke(width=0.8, opacity=0.15),
            run_time=run_time * 0.35,
            rate_func=rate_functions.ease_in_quad,
        )
        self.play(
            run_btn.animate.scale(1.05),
            btn_bg.animate.set_fill(CODE_RUN_GREEN),
            run_time=run_time * 0.28,
            rate_func=rate_functions.ease_out_quad,
        )
        self.play(
            run_btn.animate.scale(1.0),
            FadeOut(ripple),
            run_time=run_time * 0.25,
        )

    def fast_shake(self, mob: Mobject, *, shakes: int = 5, amplitude: float = 0.06):
        origin = mob.get_center().copy()
        for i in range(shakes):
            direction = RIGHT if i % 2 == 0 else LEFT
            self.play(
                mob.animate.shift(direction * amplitude),
                run_time=0.045,
                rate_func=linear,
            )
        self.play(mob.animate.move_to(origin), run_time=0.05)

    def _python_line_t2c(self, text: str) -> dict[str, str]:
        """Build Manim Text t2c map for a single code line."""
        t2c: dict[str, str] = {}
        covered = [False] * len(text)

        def mark(span: str, color: str) -> None:
            start = 0
            while True:
                idx = text.find(span, start)
                if idx < 0:
                    break
                if not any(covered[idx : idx + len(span)]):
                    t2c[span] = color
                    for i in range(idx, idx + len(span)):
                        covered[i] = True
                start = idx + 1

        for m in re.finditer(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', text):
            mark(m.group(), CODE_STRING)
        for m in re.finditer(r"\b\d+\.?\d*\b", text):
            mark(m.group(), CODE_NUMBER)
        for m in re.finditer(r"\b[A-Za-z_]\w*(?=\s*\()", text):
            mark(m.group(), CODE_FUNC)
        for m in re.finditer(r"\b[A-Za-z_]\w*\b", text):
            word = m.group()
            if word in PYTHON_KEYWORDS:
                mark(word, CODE_KEYWORD)
        return t2c

    def code_line(self, text: str, font_size: int = 22, *, highlight: bool = True):
        source = _safe_code_text(text.expandtabs(4))
        if highlight:
            return Text(
                source,
                font="Courier New",
                font_size=font_size,
                color=CODE_TEXT,
                t2c=self._python_line_t2c(source) if source.strip() else {},
            )
        return Text(source, font="Courier New", font_size=font_size, color=CODE_TEXT)

    def _code_space_width(self, font_size: int = 22) -> float:
        # Manim Text(" ") has zero width; Courier New is monospace so use "m".
        return Text("m", font="Courier New", font_size=font_size).width

    def make_code_line_row(self, raw: str, font_size: int = 22) -> tuple[Mobject, Mobject | None, Mobject, bool]:
        """Return (row, indent_pad|None, body_mob, is_blank)."""
        expanded = str(raw).expandtabs(4).rstrip()
        if not expanded.strip():
            spacer = self.code_line("pass", font_size=font_size)
            spacer.set_opacity(0)
            return spacer, None, spacer, True

        leading = len(expanded) - len(expanded.lstrip(" "))
        body = expanded.lstrip(" ")
        body_mob = self.code_line(body, font_size=font_size)
        if leading > 0:
            pad_w = leading * self._code_space_width(font_size)
            indent_pad = Rectangle(
                width=max(pad_w, 0.01),
                height=max(body_mob.height, 0.12),
                fill_opacity=0,
                stroke_width=0,
            )
            row = VGroup(indent_pad, body_mob).arrange(RIGHT, buff=0, aligned_edge=DOWN)
            return row, indent_pad, body_mob, False
        return body_mob, None, body_mob, False

    def prepare_code_editor(
        self,
        card: Mobject,
        split_y: float,
        *,
        title_bar: Mobject | None = None,
        output_panel: Mobject | None = None,
        pad_x: float = 0.38,
        code_area_top: float | None = None,
        font_size: int = 22,
        line_buff: float = 0.12,
    ) -> dict:
        anchor = card.get_left() + RIGHT * pad_x
        code_top = code_area_top if code_area_top is not None else card.get_top()[1] - 0.22
        if title_bar is not None:
            viewport_top = title_bar.get_bottom()[1] - 0.04
        else:
            viewport_top = code_top - 0.02
        if output_panel is not None:
            code_floor = max(output_panel.get_top()[1] + 0.24, split_y + 0.28)
        else:
            code_floor = split_y + 0.34
        code_viewport_height = max(viewport_top - code_floor, 0.5)
        card_top = card.get_top()[1]
        return {
            "code_group": VGroup(),
            "line_rows": [],
            "anchor": anchor,
            "code_top": code_top,
            "viewport_top": viewport_top,
            "viewport_bottom": split_y + 0.12,
            "code_floor": code_floor,
            "code_viewport_height": code_viewport_height,
            "split_y": split_y,
            "card_top": card_top,
            "window_top": viewport_top - 0.04,
            "window_bottom": code_floor,
            "max_width": card.width - 2 * pad_x,
            "font_size": font_size,
            "line_buff": line_buff,
            "scroll_offset": 0.0,
            "home_first_top": None,
        }

    def _code_line_step(self, editor: dict) -> float:
        group: VGroup = editor["code_group"]
        if group.submobjects:
            return group[-1].height + float(editor["line_buff"])
        return 0.34

    def _clamp_code_scroll_dy(
        self,
        editor: dict,
        dy: float,
        *,
        mode: str = "default",
    ) -> float:
        """Limit vertical scroll. Write/check modes allow lines to leave through the top."""
        group: VGroup = editor["code_group"]
        if not group.submobjects or abs(dy) < 1e-9:
            return 0.0
        vtop = float(editor["viewport_top"])
        vbottom = float(editor.get("code_floor", editor["viewport_bottom"]))
        new_top = group.get_top()[1] + dy
        new_bottom = group.get_bottom()[1] + dy

        if mode in ("write", "check"):
            if dy < 0 and new_bottom < vbottom:
                dy = vbottom - group.get_bottom()[1]
            return dy

        if dy > 0 and new_top > vtop:
            dy = vtop - group.get_top()[1]
        if dy < 0 and new_bottom < vbottom:
            dy = vbottom - group.get_bottom()[1]
        return dy

    def _scroll_code_group_by(
        self,
        editor: dict,
        dy: float,
        *,
        run_time: float = 0.32,
        clamp: bool | str = True,
    ) -> None:
        if clamp is False:
            pass
        elif clamp is True:
            dy = self._clamp_code_scroll_dy(editor, dy, mode="default")
        else:
            dy = self._clamp_code_scroll_dy(editor, dy, mode=str(clamp))
        if abs(dy) < 1e-6:
            return
        group: VGroup = editor["code_group"]
        self.play(group.animate.shift(UP * dy), run_time=run_time, rate_func=smooth)
        editor["scroll_offset"] = float(editor.get("scroll_offset", 0.0)) + dy

    def _position_code_row(self, editor: dict, row: Mobject) -> None:
        group: VGroup = editor["code_group"]
        anchor = editor["anchor"]
        code_top = float(editor["code_top"])
        line_buff = float(editor["line_buff"])
        max_w = float(editor["max_width"])

        if len(group) == 0:
            row.align_to([0, code_top, 0], UP)
            row.align_to(anchor, LEFT)
        else:
            row.next_to(group[-1], DOWN, buff=line_buff, aligned_edge=LEFT)
            row.align_to(anchor, LEFT)

        if row.width > max_w:
            row.scale_to_fit_width(max_w)

    def _scroll_before_write_row(
        self,
        editor: dict,
        row: Mobject,
        *,
        run_time: float = 0.38,
        chunk_lines: float = 3.5,
    ) -> None:
        """Scroll up in 3–4 line chunks so the line being typed stays above the output panel."""
        floor = float(editor["code_floor"])
        if row.get_bottom()[1] >= floor:
            return
        needed = floor - row.get_bottom()[1]
        line_step = self._code_line_step(editor)
        dy = max(needed, chunk_lines * line_step)
        self._scroll_code_group_by(editor, dy, run_time=run_time, clamp="write")

    def reveal_code_line(
        self,
        editor: dict,
        raw: str,
        *,
        type_body: bool = True,
    ) -> Mobject:
        """Add one code line beneath prior lines; scroll first if needed, then type."""
        font_size = int(editor["font_size"])
        row, indent, body, is_blank = self.make_code_line_row(raw, font_size=font_size)
        group: VGroup = editor["code_group"]

        self._position_code_row(editor, row)
        self._scroll_before_write_row(editor, row)
        self._position_code_row(editor, row)

        group.add(row)
        self.add(group)
        row.set_z_index(2)
        if editor.get("home_first_top") is None and len(group) == 1:
            editor["home_first_top"] = group[0].get_top()[1]

        if is_blank:
            editor["line_rows"].append(row)
            return row

        if type_body and body is not None and getattr(body, "text", ""):
            self.type_code_text(body, time_per_char=0.032)
        else:
            self.play(FadeIn(row), run_time=0.12)

        editor["line_rows"].append(row)
        return row

    def clear_code_from_output_zone(
        self,
        editor: dict,
        output_panel: Mobject,
        *,
        run_time: float = 0.32,
        pad: float = 0.1,
    ) -> None:
        """Scroll code up so no lines sit inside the output panel area."""
        group: VGroup = editor["code_group"]
        if not group.submobjects:
            return
        floor = output_panel.get_top()[1] + pad
        lowest = group.get_bottom()[1]
        if lowest < floor:
            dy = floor - lowest
            self._scroll_code_group_by(editor, dy, run_time=run_time, clamp=False)

    def scroll_code_editor_home(
        self,
        editor: dict,
        *,
        run_time: float = 0.5,
    ) -> None:
        """Scroll back to the first line after all code has been written."""
        group: VGroup = editor["code_group"]
        if not group.submobjects:
            return
        home_top = editor.get("home_first_top")
        if home_top is None:
            home_top = float(editor["code_top"])
        dy = float(home_top) - group[0].get_top()[1]
        if abs(dy) < 1e-4:
            editor["scroll_offset"] = 0.0
            return
        self._scroll_code_group_by(editor, dy, run_time=run_time, clamp=False)
        editor["scroll_offset"] = 0.0

    def scroll_code_editor_to_line(
        self,
        editor: dict,
        line_mob: Mobject,
        *,
        run_time: float = 0.22,
        margin: float = 0.12,
    ) -> None:
        """Scroll the code panel so the active line stays inside the editor window."""
        top = float(editor["window_top"]) - margin
        floor = float(editor["code_floor"])
        cy = line_mob.get_center()[1]

        if cy < floor:
            dy = floor - cy + line_mob.height * 0.35
            self._scroll_code_group_by(editor, dy, run_time=run_time, clamp="check")
        elif cy > top:
            dy = cy - top
            self._scroll_code_group_by(editor, -dy, run_time=run_time, clamp="check")

    def code_lines_group(self, *lines, font_size: int = 22, max_width: float | None = None):
        group = VGroup(*[self.code_line(line, font_size=font_size) for line in lines])
        group.arrange(DOWN, buff=0.16, aligned_edge=LEFT)
        if max_width is not None and group.width > max_width:
            group.scale(max_width / group.width)
        return group

    def place_code_in_editor(
        self,
        content: Mobject,
        card: Mobject,
        split_y: float,
        pad_x: float = 0.35,
        pad_y: float = 0.22,
        code_area_top: float | None = None,
    ):
        max_w = card.width - 2 * pad_x
        code_top = code_area_top if code_area_top is not None else card.get_top()[1] - pad_y
        code_bottom = split_y + 0.1
        max_h = code_top - code_bottom
        if content.width > max_w:
            content.scale(max_w / content.width)
        if content.height > max_h:
            content.scale(max_h / content.height)
        content.align_to(card.get_left() + RIGHT * pad_x, LEFT)
        content.align_to([0, code_top, 0], UP)
        return content

    def code_output_banner(
        self,
        text: str,
        card: Mobject,
        split_y: float,
        *,
        success: bool = True,
        font_size: int = 19,
    ):
        label_color = CODE_FUNC
        value_color = CODE_NUMBER if success else CODE_FUNC
        lines = [ln for ln in text.splitlines() if ln.strip()] or [
            text.strip() or ("Ran successfully" if success else "Error")
        ]

        label_text = "Output:" if success else "Error:"
        label = Text(label_text, font="Courier New", font_size=font_size, color=label_color)
        body = VGroup(
            *[
                Text(
                    ln,
                    font="Courier New",
                    font_size=font_size,
                    color=value_color,
                )
                for ln in lines[:3]
            ]
        )
        body.arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        content = VGroup(label, body).arrange(DOWN, buff=0.12, aligned_edge=LEFT)

        pad_x, pad_y = 0.38, 0.14
        max_w = card.width - 2 * pad_x
        if content.width > max_w:
            content.scale(max_w / content.width)

        output_bottom = card.get_bottom()[1] + pad_y
        content.move_to([card.get_center()[0], (split_y + output_bottom) / 2, 0])
        content.align_to(card.get_left() + RIGHT * pad_x, LEFT)
        return content, body

    def present_code_output(
        self,
        text: str,
        card: Mobject,
        split_y: float,
        *,
        success: bool = True,
        type_error: bool = False,
    ) -> tuple[Mobject, Mobject]:
        """Show output in the output panel — fade in for success, type for errors."""
        output_group, output_body = self.code_output_banner(
            text,
            card,
            split_y,
            success=success,
        )
        if success or not type_error:
            self.play(FadeIn(output_group, shift=UP * 0.06), run_time=0.45)
            return output_group, output_body

        label = output_group[0]
        self.add(label)
        self.play(FadeIn(label), run_time=0.1)
        for line_mob in output_body:
            self.add(line_mob)
            self.type_code_text(line_mob, time_per_char=0.028)
        return output_group, output_body

    def type_code_text(self, text_mob, time_per_char=0.04, cursor_color=CODE_CURSOR):
        self.type_text(text_mob, time_per_char=time_per_char, cursor_color=cursor_color)

    def list_check_line(self, text: str, font_size: int = 28):
        mark = Text("✓", font_size=font_size + 4, color=YELLOW, weight=BOLD)
        body = self.on_card(text, font_size=font_size)
        row = VGroup(mark, body).arrange(RIGHT, buff=0.18, aligned_edge=DOWN)
        return row

    def list_lines_group(self, *lines, font_size: int = 28, max_width: float | None = None):
        group = VGroup(*[self.list_check_line(line, font_size=font_size) for line in lines])
        group.arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        if max_width is not None:
            for row in group:
                if row.width > max_width:
                    row.scale(max_width / row.width)
        return group

    def empty_card(self, side="right", width=5.6, height=5.0, label=None):
        card = RoundedRectangle(
            width=width,
            height=height,
            corner_radius=0.22,
            fill_color=WHITE,
            fill_opacity=0.96,
            stroke_color=GREY_B,
            stroke_width=1.5,
        )
        if label is not None:
            card.move_to(self.panel_anchor(side, label))
        else:
            anchor = self.right_center() if side == "right" else self.left_center()
            card.move_to(anchor)
        return card

    def typing_cursor_for(self, text_mob, cursor_color=YELLOW):
        return Rectangle(
            width=0.06,
            height=max(0.3, text_mob.height * 1.05),
            fill_color=cursor_color,
            fill_opacity=1,
            stroke_width=0,
        )

    def type_text(self, text_mob, time_per_char=0.05, cursor_color=YELLOW):
        cursor = self.typing_cursor_for(text_mob, cursor_color=cursor_color)
        if len(text_mob) > 0:
            cursor.move_to(text_mob[0])
        else:
            cursor.move_to(text_mob.get_left())
        self.play(
            TypeWithCursor(text_mob, cursor, time_per_char=time_per_char, leave_cursor_on=False),
            run_time=max(0.4, len(text_mob.text) * time_per_char),
        )

    def type_line_with_icon_triggers(
        self,
        template_mob,
        trigger_map: dict[str, Mobject],
        *,
        time_per_char=0.05,
        cursor_color=YELLOW,
        revealed: set[str] | None = None,
    ) -> set[str]:
        """Type a line left-to-right; FadeIn icons when trigger words are typed."""
        from icon_triggers import split_line_by_triggers

        revealed = set(revealed or [])
        segments = split_line_by_triggers(template_mob.text, list(trigger_map.keys()))
        font_size = getattr(template_mob, "font_size", None) or 28
        color = BLACK
        try:
            color = template_mob.get_color()
        except Exception:
            pass

        y = template_mob.get_center()[1]
        x = template_mob.get_left()[0]

        for seg_text, trigger_key in segments:
            if seg_text:
                seg = Text(str(seg_text), font_size=font_size, color=color, weight=BOLD)
                seg.move_to([x + seg.width / 2, y, 0])
                self.type_text(seg, time_per_char=time_per_char, cursor_color=cursor_color)
                x = seg.get_right()[0]

            if trigger_key:
                key = trigger_key.lower()
                if key not in revealed and key in trigger_map:
                    icon = trigger_map[key]
                    icon.set_opacity(1)
                    self.play(FadeIn(icon, scale=1.02), run_time=0.35)
                    revealed.add(key)

        return revealed

    def fade_clear(self, *mobjects, run_time=0.55):
        on_scene = set(self.mobjects)
        targets: list[Mobject] = []
        seen: set[int] = set()
        for m in mobjects:
            if m is None or not isinstance(m, Mobject):
                continue
            for mob in m.get_family():
                mob_id = id(mob)
                if mob_id in seen:
                    continue
                if mob in on_scene:
                    targets.append(mob)
                    seen.add(mob_id)
        if targets:
            self.play(*[FadeOut(m) for m in targets], run_time=run_time, rate_func=smooth)
            remaining = [m for m in targets if m in self.mobjects]
            if remaining:
                self.remove(*remaining)

    def sweep_foreground(self, run_time=0.3):
        """Remove every mobject except the background (catches detached emphasis slices)."""
        if len(self.mobjects) <= 1:
            return
        strays = [m for m in list(self.mobjects)[1:] if m in self.mobjects]
        if not strays:
            return
        if run_time <= 0.01:
            self.remove(*strays)
            return
        self.play(*[FadeOut(m) for m in strays], run_time=run_time, rate_func=smooth)
        remaining = [m for m in strays if m in self.mobjects]
        if remaining:
            self.remove(*remaining)

    def beat_transition(self, run_time=0.8, hold=0.15):
        """Pause between beats — keeps orange background visible (no black flash)."""
        if hasattr(self, "cam_restore"):
            self.cam_restore(run_time=min(run_time, 0.5))
        if hold > 0:
            self.wait(hold)


class BeatScene(BeatLayoutMixin, Scene):
    def setup_background(self):
        super().setup_background(overscale=1.0)


class MovingBeatScene(BeatLayoutMixin, MovingCameraScene):
    """MovingCameraScene with beat layout + cam_* helpers."""

    def setup_background(self):
        super().setup_background(overscale=1.25)

    def cam_restore(self, run_time=0.8):
        self.play(
            self.camera.frame.animate.set(width=config.frame_width)
            .set(height=config.frame_height)
            .move_to(ORIGIN),
            run_time=run_time,
            rate_func=smooth,
        )

    def cam_focus_point(self, point, width=PANEL_FRAME_WIDTH, run_time=1.0):
        height = config.frame_height * (width / config.frame_width)
        self.play(
            self.camera.frame.animate.set(width=width).set(height=height).move_to(point),
            run_time=run_time,
            rate_func=smooth,
        )

    def cam_focus_left(self, label, run_time=1.0):
        self.cam_focus_point(self.panel_anchor("left", label), run_time=run_time)

    def cam_focus_right(self, label, run_time=1.0):
        self.cam_focus_point(self.panel_anchor("right", label), run_time=run_time)

    def cam_focus_card(self, card, run_time=1.0):
        self.play(self.camera.auto_zoom(card, margin=0.5), run_time=run_time, rate_func=smooth)

    def cam_focus_mobject(self, mob, margin=0.4, run_time=0.9):
        self.play(self.camera.auto_zoom(mob, margin=margin), run_time=run_time, rate_func=smooth)
