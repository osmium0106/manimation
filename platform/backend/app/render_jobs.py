"""Background Manim render jobs with on-disk status for polling."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal

JobKind = Literal["preview", "export"]
ProgressCallback = Callable[[int, str], None]
RenderFn = Callable[[ProgressCallback | None], None]

_locks: dict[str, threading.Lock] = {}
_registry_lock = threading.Lock()

_STATUS_FILES: dict[JobKind, str] = {
    "preview": ".render_status.json",
    "export": ".export_status.json",
}


def _status_path(renders_dir: Path, kind: JobKind) -> Path:
    return renders_dir / _STATUS_FILES[kind]


def _lock_key(project_id: str, kind: JobKind) -> str:
    return f"{project_id}:{kind}"


def _project_lock(project_id: str, kind: JobKind) -> threading.Lock:
    key = _lock_key(project_id, kind)
    with _registry_lock:
        lock = _locks.get(key)
        if lock is None:
            lock = threading.Lock()
            _locks[key] = lock
        return lock


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_status(renders_dir: Path, kind: JobKind = "preview") -> dict:
    path = _status_path(renders_dir, kind)
    if not path.exists():
        return {"status": "idle"}
    try:
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"status": "idle"}


def write_status(renders_dir: Path, kind: JobKind, payload: dict) -> None:
    renders_dir.mkdir(parents=True, exist_ok=True)
    _status_path(renders_dir, kind).write_text(json.dumps(payload, indent=2))


def update_status(renders_dir: Path, kind: JobKind, **fields: object) -> None:
    current = read_status(renders_dir, kind)
    current.update(fields)
    write_status(renders_dir, kind, current)


def start_render_job(
    project_id: str,
    kind: JobKind,
    renders_dir: Path,
    render_fn: RenderFn,
    *,
    track_progress: bool = False,
) -> dict:
    """Run render_fn in a background thread; return current job status."""
    lock = _project_lock(project_id, kind)
    if not lock.acquire(blocking=False):
        current = read_status(renders_dir, kind)
        if current.get("status") == "rendering":
            return current
        lock.acquire()

    initial: dict = {
        "status": "rendering",
        "started_at": _now_iso(),
        "error": None,
    }
    if track_progress:
        initial["progress"] = 0
        initial["phase"] = "Starting Manim"
    write_status(renders_dir, kind, initial)

    def _run() -> None:
        def progress_cb(percent: int, phase: str) -> None:
            if track_progress:
                update_status(
                    renders_dir,
                    kind,
                    progress=max(0, min(100, percent)),
                    phase=phase,
                )

        try:
            render_fn(progress_cb if track_progress else None)
            done: dict = {
                "status": "done",
                "finished_at": _now_iso(),
                "error": None,
            }
            if track_progress:
                done["progress"] = 100
                done["phase"] = "Complete"
            write_status(renders_dir, kind, done)
        except Exception as exc:
            failed: dict = {
                "status": "error",
                "finished_at": _now_iso(),
                "error": str(exc),
            }
            if track_progress:
                failed["phase"] = "Failed"
            write_status(renders_dir, kind, failed)
        finally:
            lock.release()

    thread_name = f"{kind}-render-{project_id}"
    threading.Thread(target=_run, daemon=True, name=thread_name).start()
    return read_status(renders_dir, kind)
