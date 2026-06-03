"""Local filesystem project storage with snapshot history for revert."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DATA_DIR = Path(
    os.environ.get("MANIMATIONS_DATA_DIR", Path.home() / "manimations-studio")
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectStore:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = Path(data_dir or DEFAULT_DATA_DIR)
        self.projects_dir = self.data_dir / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, project_id: str) -> Path:
        return self.projects_dir / project_id

    def list_projects(self) -> list[dict]:
        out = []
        for d in sorted(self.projects_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if not d.is_dir():
                continue
            meta_path = d / "project.json"
            if meta_path.exists():
                meta = json.loads(meta_path.read_text())
                preview = d / "renders" / "latest.mp4"
                out.append(
                    {
                        "id": d.name,
                        "name": meta.get("name", d.name),
                        "updated_at": meta.get("updated_at"),
                        "created_at": meta.get("created_at"),
                        "beat_count": len(meta.get("beats", [])),
                        "theme_id": meta.get("theme_id", "builtin_orange"),
                        "has_preview": preview.exists(),
                    }
                )
        return out

    def delete_project(self, project_id: str) -> None:
        pdir = self._project_dir(project_id)
        if not pdir.exists():
            raise FileNotFoundError(f"Project not found: {project_id}")
        shutil.rmtree(pdir)

    def create_project(self, name: str = "Untitled", *, theme_id: str = "builtin_orange") -> dict:
        project_id = str(uuid.uuid4())[:8]
        pdir = self._project_dir(project_id)
        pdir.mkdir(parents=True)
        (pdir / "history").mkdir()
        (pdir / "renders").mkdir()
        project = {
            "id": project_id,
            "name": name,
            "theme_id": theme_id,
            "style_pack": "course_clean",
            "use_camera": False,
            "beats": [],
            "chat": [],
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        self.save_project(project, snapshot=False)
        return project

    def load_project(self, project_id: str) -> dict:
        path = self._project_dir(project_id) / "project.json"
        if not path.exists():
            raise FileNotFoundError(f"Project not found: {project_id}")
        project = json.loads(path.read_text())
        if not project.get("theme_id"):
            project["theme_id"] = "builtin_orange"
        return project

    def save_project(self, project: dict, *, snapshot: bool = True) -> dict:
        project_id = project["id"]
        project["updated_at"] = _now_iso()
        pdir = self._project_dir(project_id)
        pdir.mkdir(parents=True, exist_ok=True)

        if snapshot and (pdir / "project.json").exists():
            self.create_snapshot(project_id, label="auto-save")

        path = pdir / "project.json"
        path.write_text(json.dumps(project, indent=2))
        return project

    def create_snapshot(self, project_id: str, label: str = "snapshot") -> dict:
        project = self.load_project(project_id)
        snap_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        snap = {
            "id": snap_id,
            "label": label,
            "created_at": _now_iso(),
            "project": project,
        }
        snap_path = self._project_dir(project_id) / "history" / f"{snap_id}.json"
        snap_path.write_text(json.dumps(snap, indent=2))
        self._trim_history(project_id, keep=30)
        return {"id": snap_id, "label": label, "created_at": snap["created_at"]}

    def _trim_history(self, project_id: str, keep: int = 30) -> None:
        hist = self._project_dir(project_id) / "history"
        files = sorted(hist.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in files[keep:]:
            f.unlink(missing_ok=True)

    def list_snapshots(self, project_id: str) -> list[dict]:
        hist = self._project_dir(project_id) / "history"
        if not hist.exists():
            return []
        snaps = []
        for f in sorted(hist.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            data = json.loads(f.read_text())
            snaps.append(
                {
                    "id": data["id"],
                    "label": data.get("label", "snapshot"),
                    "created_at": data.get("created_at"),
                }
            )
        return snaps

    def revert(self, project_id: str, snapshot_id: str) -> dict:
        snap_path = self._project_dir(project_id) / "history" / f"{snapshot_id}.json"
        if not snap_path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_id}")
        snap = json.loads(snap_path.read_text())
        project = snap["project"]
        # Save current state before revert
        current = self.load_project(project_id)
        pre = {
            "id": f"pre_revert_{snapshot_id}",
            "label": "before-revert",
            "created_at": _now_iso(),
            "project": current,
        }
        (self._project_dir(project_id) / "history" / f"{pre['id']}.json").write_text(
            json.dumps(pre, indent=2)
        )
        project["updated_at"] = _now_iso()
        path = self._project_dir(project_id) / "project.json"
        path.write_text(json.dumps(project, indent=2))
        return project

    def render_path(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "renders" / "latest.mp4"

    def export_path(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "renders" / "export_1080p60.mp4"

    def scene_path(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "generated_scene.py"

    def write_scene(self, project_id: str, code: str) -> Path:
        path = self.scene_path(project_id)
        path.write_text(code)
        return path
