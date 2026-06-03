"""Parse Manim CLI output into render progress percentages."""

from __future__ import annotations

import re
from pathlib import Path

_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_ANIM_DONE = re.compile(r"Animation\s+(\d+)\s*:\s*Partial")
_ANIM_TQDM = re.compile(r"Animation\s+(\d+):.*?(\d+)%.*?(\d+)/(\d+)")
_COMBINE = re.compile(r"Combining|Writing.*Movie|concatenat", re.I)
_FILE_READY = re.compile(r"File ready at|Rendered ", re.I)
_SCENE_LOAD = re.compile(r"Rendering|Reading|Writing.*Scene|scene_file", re.I)


def _clean_line(line: str) -> str:
    return _ANSI.sub("", line).replace("\r", " ").strip()


class ManimProgressParser:
    def __init__(self, estimated_total: int = 24):
        self.estimated_total = max(estimated_total, 1)
        self.completed = 0
        self.max_index = 0
        self.phase = "Starting Manim"

    @classmethod
    def from_scene(cls, scene_file: Path) -> ManimProgressParser:
        try:
            text = scene_file.read_text()
        except OSError:
            return cls(24)
        plays = len(re.findall(r"self\.(?:play|wait)\(", text))
        beat_calls = len(re.findall(r"run_\w+_beat\(", text))
        code_demo = text.count("code_demo")
        est = plays + beat_calls * 12 + code_demo * 40
        return cls(max(est, 12))

    def feed(self, line: str) -> tuple[int, str] | None:
        line = _clean_line(line)
        if not line:
            return None

        if _SCENE_LOAD.search(line) and "Partial" not in line:
            self.phase = "Loading scene"
            return max(3, min(8, self._percent()[0])), self.phase

        match = _ANIM_DONE.search(line)
        if match:
            idx = int(match.group(1))
            self.completed = max(self.completed, idx + 1)
            self.max_index = max(self.max_index, idx)
            self.phase = f"Animation {idx + 1}"
            return self._percent()

        match = _ANIM_TQDM.search(line)
        if match:
            idx = int(match.group(1))
            pct_inner = int(match.group(2))
            cur, total = int(match.group(3)), max(int(match.group(4)), 1)
            self.max_index = max(self.max_index, idx)
            self.estimated_total = max(
                self.estimated_total,
                self.max_index + 1,
                self.completed + 3,
            )
            frac = (self.completed + (cur / total)) / self.estimated_total
            self.phase = f"Animation {idx + 1} ({pct_inner}%)"
            return min(95, max(5, int(frac * 92))), self.phase

        if _COMBINE.search(line):
            self.phase = "Combining video"
            return 96, self.phase

        if _FILE_READY.search(line):
            self.phase = "Finalizing"
            return 100, self.phase

        return None

    def _percent(self) -> tuple[int, str]:
        self.estimated_total = max(
            self.estimated_total,
            self.max_index + 1,
            self.completed + 2,
        )
        pct = min(94, max(5, int((self.completed / self.estimated_total) * 92)))
        return pct, self.phase
