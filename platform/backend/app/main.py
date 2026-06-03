"""FastAPI backend for Manimations Studio."""

from __future__ import annotations

import os
import re
import sys
import uuid
from datetime import datetime, timezone
from collections.abc import Callable
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Repo root on path for visual resolver
MANIM_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(MANIM_ROOT / "animations"))
sys.path.insert(0, str(MANIM_ROOT / "platform" / "backend"))

load_dotenv(MANIM_ROOT / "platform" / ".env")
load_dotenv(MANIM_ROOT / ".env")

from app.beat_compiler import compile_scene, generate_scene_code, patch_scene_code, starter_scene_code  # noqa: E402
from app.openai_service import OpenAIService  # noqa: E402
from app.project_store import ProjectStore  # noqa: E402
from app.render_jobs import cancel_render_job, read_status, start_render_job, update_status, write_status  # noqa: E402
from app.renderer import render_scene  # noqa: E402
from app.script_parser import parse_script  # noqa: E402

from app.theme_schema import ThemeCreateBody, ThemeUpdateBody  # noqa: E402
from app.theme_store import BUILTIN_ORANGE_ID, ThemeStore  # noqa: E402

store = ProjectStore()
theme_store = ThemeStore(store.data_dir)


def _resolve_and_prefetch(project: dict) -> dict:
    from visual_library import prefetch_beat_visuals  # noqa: E402
    from visual_resolver import resolve_project  # noqa: E402

    project = resolve_project(project)
    for beat in project.get("beats", []):
        prefetch_beat_visuals(beat)
    return project


def _resolve_icon_descriptions(beats: list[dict]) -> list[dict]:
    from app.icon_resolver import beats_need_icon_resolution, resolve_beat_icons  # noqa: E402

    if not beats_need_icon_resolution(beats):
        return beats
    try:
        ai = _openai()
        return resolve_beat_icons(beats, ai)
    except Exception:
        return beats


def _prepare_beats(beats: list[dict]) -> list[dict]:
    from app.beat_compiler import _sanitize_beat  # noqa: E402
    from app.icon_resolver import beats_need_icon_resolution, validate_icon_refs  # noqa: E402
    from beat_types import apply_type_defaults  # noqa: E402

    prepared = [apply_type_defaults(_sanitize_beat(dict(b))) for b in beats]
    if beats_need_icon_resolution(prepared):
        prepared = _resolve_icon_descriptions(prepared)
    else:
        prepared = validate_icon_refs(prepared)
    return prepared


def _write_scene_code(project_id: str, code: str) -> Path:
    scene_path = store.scene_path(project_id)
    scene_path.write_text(patch_scene_code(code))
    return scene_path


def _theme_for_project(project: dict) -> dict:
    return theme_store.theme_for_render(project.get("theme_id", BUILTIN_ORANGE_ID))


def _render_project(
    project_id: str,
    project: dict,
    *,
    quality: str = "-ql",
    skip_compile: bool = False,
    progress_callback=None,
) -> Path:
    scene_path = store.scene_path(project_id)
    if skip_compile and scene_path.exists():
        source = scene_path.read_text()
        patched = patch_scene_code(source)
        if patched != source:
            scene_path.write_text(patched)
    if not skip_compile and not project.get("code_customized"):
        compile_scene(project, scene_path, theme=_theme_for_project(project))
    elif not scene_path.exists():
        code = generate_scene_code(project, theme=_theme_for_project(project)) if project.get("beats") else starter_scene_code(_theme_for_project(project))
        scene_path.write_text(code)
    if quality == "-qh":
        mp4 = store.export_path(project_id)
        job_kind = "export"
    else:
        mp4 = store.render_path(project_id)
        job_kind = "preview"
    render_scene(
        scene_path,
        output_mp4=mp4,
        quality=quality,
        progress_callback=progress_callback,
        process_registry=(project_id, job_kind),
    )
    return mp4


def _prepare_render(
    project_id: str,
    project: dict,
    body: RenderRequest | None,
    *,
    on_phase: Callable[[int, str], None] | None = None,
) -> tuple[dict, bool]:
    """Compile scene if needed; return updated project and skip_compile flag."""

    def phase(progress: int, label: str) -> None:
        if on_phase:
            on_phase(progress, label)

    body = body or RenderRequest()
    scene_path = store.scene_path(project_id)
    skip = False

    if body.code is not None:
        if "class " not in body.code or "construct" not in body.code:
            raise HTTPException(
                status_code=400,
                detail="Code must define a Scene class with a construct() method.",
            )
        phase(2, "Saving scene code")
        _write_scene_code(project_id, body.code)
        project["code_customized"] = True
        store.save_project(project, snapshot=False)
        skip = True
    elif body.from_beats:
        if not project.get("beats"):
            raise HTTPException(status_code=400, detail="No beats to compile.")
        phase(1, "Resolving visuals")
        project = _resolve_and_prefetch(project)
        phase(3, "Compiling scene")
        compile_scene(project, scene_path, theme=_theme_for_project(project))
        project["code_customized"] = False
        store.save_project(project, snapshot=False)
        skip = True
    else:
        skip = project.get("code_customized", False)
        if not skip and project.get("beats"):
            phase(1, "Resolving visuals")
            project = _resolve_and_prefetch(project)
            store.save_project(project, snapshot=False)

    return project, skip


def _validate_render_body(project: dict, body: RenderRequest | None) -> RenderRequest:
    """Fast validation before kicking off a background render."""
    body = body or RenderRequest()
    if body.code is not None:
        if "class " not in body.code or "construct" not in body.code:
            raise HTTPException(
                status_code=400,
                detail="Code must define a Scene class with a construct() method.",
            )
    elif body.from_beats and not project.get("beats"):
        raise HTTPException(status_code=400, detail="No beats to compile.")
    return body


def _kickoff_preview_render(project_id: str, body: RenderRequest | None = None) -> dict:
    renders_dir = store.render_path(project_id).parent
    req_body = body or RenderRequest()

    def _run(progress_cb) -> None:
        def on_phase(progress: int, phase: str) -> None:
            update_status(
                renders_dir,
                "preview",
                status="rendering",
                progress=max(0, min(99, progress)),
                phase=phase,
            )

        project = store.load_project(project_id)
        project, skip = _prepare_render(project_id, project, req_body, on_phase=on_phase)
        _render_project(
            project_id,
            project,
            quality="-ql",
            skip_compile=skip,
            progress_callback=progress_cb,
        )

    status = start_render_job(
        project_id, "preview", renders_dir, _run, track_progress=True
    )
    preview_url = (
        f"/api/projects/{project_id}/preview"
        if status.get("status") == "done"
        else None
    )
    return {
        "status": status.get("status", "rendering"),
        "preview_url": preview_url,
        "render_error": status.get("error"),
        "progress": status.get("progress", 0),
        "phase": status.get("phase"),
    }


def _kickoff_export_render(project_id: str, project: dict, *, skip_compile: bool) -> dict:
    renders_dir = store.render_path(project_id).parent

    def _run(progress_cb) -> None:
        _render_project(
            project_id,
            project,
            quality="-qh",
            skip_compile=skip_compile,
            progress_callback=progress_cb,
        )

    status = start_render_job(
        project_id,
        "export",
        renders_dir,
        _run,
        track_progress=True,
    )
    download_url = (
        f"/api/projects/{project_id}/download"
        if status.get("status") == "done"
        else None
    )
    return {
        "status": status.get("status", "rendering"),
        "download_url": download_url,
        "quality": "1080p60",
        "progress": status.get("progress", 0),
        "phase": status.get("phase"),
        "error": status.get("error"),
    }


def _read_scene_code(project_id: str, project: dict) -> dict:
    scene_path = store.scene_path(project_id)
    if scene_path.exists():
        return {
            "code": scene_path.read_text(),
            "source": "file",
            "code_customized": project.get("code_customized", False),
        }
    theme = _theme_for_project(project)
    if project.get("beats"):
        code = generate_scene_code(project, theme=theme)
    else:
        code = starter_scene_code(theme)
    scene_path.write_text(code)
    return {"code": code, "source": "generated", "code_customized": False}

app = FastAPI(title="Manimations Studio", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _openai() -> OpenAIService:
    try:
        return OpenAIService()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


class ChatRequest(BaseModel):
    message: str


class CreateProjectRequest(BaseModel):
    name: str = "Untitled"
    theme_id: str = BUILTIN_ORANGE_ID


class ProjectPatchRequest(BaseModel):
    theme_id: str | None = None
    name: str | None = None
    style_brief: str | None = None
    use_camera: bool | None = None
    pacing: str | None = None  # relaxed | dense


class BeatsUpdateRequest(BaseModel):
    beats: list[dict]
    use_camera: bool | None = None


class IconSearchRequest(BaseModel):
    query: str
    limit: int = 24


class RevertRequest(BaseModel):
    snapshot_id: str


class ScriptRequest(BaseModel):
    script: str
    use_ai: bool = False


class CodeRequest(BaseModel):
    code: str
    render: bool = True


class RenderRequest(BaseModel):
    code: str | None = None
    from_beats: bool = False


class PythonToolRequest(BaseModel):
    code: str


def _apply_theme_to_project(project: dict) -> dict:
    theme_id = project.get("theme_id") or BUILTIN_ORANGE_ID
    if not theme_store.theme_exists(theme_id):
        theme_id = BUILTIN_ORANGE_ID
    project["theme_id"] = theme_id
    row = theme_store.get_theme_row(theme_id)
    if row:
        project["style_pack"] = row["style_pack"]
    return project


@app.get("/api/themes")
def list_themes():
    return {"themes": [t.model_dump() for t in theme_store.list_themes()]}


@app.get("/api/themes/{theme_id}")
def get_theme(theme_id: str):
    theme = theme_store.get_theme(theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    return theme.model_dump()


@app.post("/api/themes")
async def create_theme(
    name: str = Form(...),
    description: str = Form(""),
    style_pack: str = Form("course_clean"),
    background_kind: str = Form("image"),
    background_loop: bool = Form(True),
    typography_json: str = Form("{}"),
    palette_json: str = Form(""),
    background: UploadFile | None = File(None),
):
    import json as json_lib

    from app.theme_schema import PaletteSpec, TypographySpec

    try:
        typography = TypographySpec(**json_lib.loads(typography_json or "{}"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid typography_json: {exc}") from exc
    palette = None
    if palette_json.strip():
        try:
            palette = PaletteSpec(**json_lib.loads(palette_json))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid palette_json: {exc}") from exc

    body = ThemeCreateBody(
        name=name,
        description=description,
        style_pack=style_pack,
        background_kind=background_kind,  # type: ignore[arg-type]
        background_loop=background_loop,
        typography=typography,
        palette=palette,
    )
    file_bytes = None
    content_type = ""
    filename = ""
    if background and background.filename:
        file_bytes = await background.read()
        content_type = background.content_type or ""
        filename = background.filename
    try:
        created = theme_store.create_theme(body, file_bytes, content_type, filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return created.model_dump()


@app.put("/api/themes/{theme_id}")
async def update_theme(
    theme_id: str,
    name: str | None = Form(None),
    description: str | None = Form(None),
    style_pack: str | None = Form(None),
    background_kind: str | None = Form(None),
    background_loop: bool | None = Form(None),
    typography_json: str | None = Form(None),
    palette_json: str | None = Form(None),
    background: UploadFile | None = File(None),
):
    import json as json_lib

    from app.theme_schema import PaletteSpec, TypographySpec

    body = ThemeUpdateBody()
    if name is not None:
        body.name = name
    if description is not None:
        body.description = description
    if style_pack is not None:
        body.style_pack = style_pack
    if background_kind is not None:
        body.background_kind = background_kind  # type: ignore[assignment]
    if background_loop is not None:
        body.background_loop = background_loop
    if typography_json:
        try:
            body.typography = TypographySpec(**json_lib.loads(typography_json))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid typography_json: {exc}") from exc
    if palette_json:
        try:
            body.palette = PaletteSpec(**json_lib.loads(palette_json))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid palette_json: {exc}") from exc

    file_bytes = None
    content_type = ""
    filename = ""
    if background and background.filename:
        file_bytes = await background.read()
        content_type = background.content_type or ""
        filename = background.filename
    try:
        updated = theme_store.update_theme(
            theme_id, body, file_bytes, content_type, filename
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return updated.model_dump()


@app.delete("/api/themes/{theme_id}")
def delete_theme(theme_id: str):
    try:
        theme_store.delete_theme(theme_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "Theme deleted"}


@app.get("/api/themes/{theme_id}/background")
def theme_background(theme_id: str):
    row = theme_store.get_theme_row(theme_id)
    if not row:
        raise HTTPException(status_code=404, detail="Theme not found")
    path = theme_store.resolve_background_path(row)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Background file not found")
    return FileResponse(path, media_type=theme_store.background_media_type(theme_id))


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "openai_configured": bool(os.environ.get("OPENAI_API_KEY")),
        "data_dir": str(store.data_dir),
    }


@app.get("/api/projects")
def list_projects():
    return {"projects": store.list_projects()}


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str):
    try:
        store.delete_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": "Project deleted"}


@app.post("/api/projects")
def create_project(body: CreateProjectRequest):
    if not theme_store.theme_exists(body.theme_id):
        raise HTTPException(status_code=400, detail=f"Unknown theme: {body.theme_id}")
    return store.create_project(body.name, theme_id=body.theme_id)


@app.patch("/api/projects/{project_id}")
def patch_project(project_id: str, body: ProjectPatchRequest):
    try:
        project = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if body.theme_id is not None:
        if not theme_store.theme_exists(body.theme_id):
            raise HTTPException(status_code=400, detail=f"Unknown theme: {body.theme_id}")
        project["theme_id"] = body.theme_id
        row = theme_store.get_theme_row(body.theme_id)
        if row:
            project["style_pack"] = row["style_pack"]
        project["code_customized"] = False
    if body.name is not None:
        project["name"] = body.name.strip()
    if body.style_brief is not None:
        project["style_brief"] = body.style_brief.strip()
    if body.use_camera is not None:
        project["use_camera"] = body.use_camera
    if body.pacing is not None:
        project["pacing"] = body.pacing
    project = _apply_theme_to_project(project)
    store.save_project(project, snapshot=True)
    return project


@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    try:
        project = store.load_project(project_id)
        return _apply_theme_to_project(project)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/projects/{project_id}/script")
def export_project_script(project_id: str):
    try:
        project = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    from app.script_exporter import beats_to_script  # noqa: E402

    return {"script": beats_to_script(project)}


@app.put("/api/projects/{project_id}/beats")
def update_project_beats(project_id: str, body: BeatsUpdateRequest):
    try:
        project = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not body.beats:
        raise HTTPException(status_code=400, detail="At least one beat required")
    project["beats"] = _prepare_beats(body.beats)
    if body.use_camera is not None:
        project["use_camera"] = body.use_camera
    project["code_customized"] = False
    project = _resolve_and_prefetch(project)
    project = _apply_theme_to_project(project)
    store.save_project(project, snapshot=True)
    return project


@app.post("/api/projects/{project_id}/validate-beats")
def validate_project_beats(project_id: str):
    try:
        project = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    from app.beat_validation import validate_beats  # noqa: E402

    return validate_beats(project.get("beats") or [])


@app.get("/api/visual-catalog")
def visual_catalog():
    import json as json_lib

    path = MANIM_ROOT / "assets" / "visual_catalog.json"
    return json_lib.loads(path.read_text())


@app.get("/api/repo-asset")
def repo_asset(path: str):
    """Serve repo assets (e.g. brand SVGs) for catalog previews."""
    if not path.startswith("assets/") or ".." in path:
        raise HTTPException(status_code=400, detail="Invalid asset path")
    full = (MANIM_ROOT / path).resolve()
    if not str(full).startswith(str(MANIM_ROOT.resolve())):
        raise HTTPException(status_code=400, detail="Invalid asset path")
    if not full.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(full)


@app.get("/api/icons/search")
def search_icons(q: str = "", limit: int = 24):
    query = q.strip()
    if not query:
        return {"icons": []}
    sys.path.insert(0, str(MANIM_ROOT / "animations"))
    from icon_library import search_iconify  # noqa: E402

    refs = search_iconify(query, limit=min(limit, 64))
    icons = [{"ref": ref, "prefix": ref.split(":")[0] if ":" in ref else ""} for ref in refs]
    return {"icons": icons}


_ICON_UPLOAD_MAX = 2 * 1024 * 1024
_ICON_UPLOAD_TYPES = {
    "image/svg+xml": ".svg",
    "image/png": ".png",
    "application/octet-stream": None,
}


@app.post("/api/projects/{project_id}/icons/upload")
async def upload_project_icon(project_id: str, file: UploadFile = File(...)):
    try:
        store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    raw = await file.read()
    if len(raw) > _ICON_UPLOAD_MAX:
        raise HTTPException(status_code=400, detail="Icon file too large (max 2 MB)")

    name = (file.filename or "icon").lower()
    ext = Path(name).suffix.lower()
    if ext not in (".svg", ".png"):
        ct = (file.content_type or "").split(";")[0].strip()
        guessed = _ICON_UPLOAD_TYPES.get(ct)
        if not guessed:
            raise HTTPException(status_code=400, detail="Only SVG and PNG icons are supported")
        ext = guessed

    safe_stem = re.sub(r"[^\w.-]+", "_", Path(name).stem)[:48] or "icon"
    filename = f"{safe_stem}{ext}"
    icons_dir = store._project_dir(project_id) / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)
    dest = icons_dir / filename
    if dest.exists():
        filename = f"{safe_stem}_{uuid.uuid4().hex[:8]}{ext}"
        dest = icons_dir / filename
    dest.write_bytes(raw)
    ref = f"icons/{filename}"
    return {"ref": ref, "kind": "project", "filename": filename}


@app.get("/api/projects/{project_id}/icons/{filename}")
def get_project_icon(project_id: str, filename: str):
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = store._project_dir(project_id) / "icons" / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Icon not found")
    media = "image/svg+xml" if path.suffix.lower() == ".svg" else "image/png"
    return FileResponse(path, media_type=media)


@app.get("/api/projects/{project_id}/snapshots")
def list_snapshots(project_id: str):
    try:
        return store.list_snapshots(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/projects/{project_id}/revert")
def revert_project(project_id: str, body: RevertRequest):
    try:
        project = store.revert(project_id, body.snapshot_id)
        return {"project": project, "message": "Reverted successfully"}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/projects/{project_id}/chat")
def chat(project_id: str, body: ChatRequest):
    try:
        project = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    ai = _openai()
    try:
        result = ai.generate_project(
            body.message,
            current_project=project,
            chat_history=project.get("chat", [])[-20:],
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI error: {exc}") from exc

    assistant_msg = result.get("message", "Updated your animation.")
    incoming = result.get("project", {})

    if incoming.get("beats"):
        project["beats"] = _prepare_beats(incoming["beats"])
    if incoming.get("name"):
        project["name"] = incoming["name"]
    if incoming.get("style_pack"):
        project["style_pack"] = incoming["style_pack"]
    if "use_camera" in incoming:
        project["use_camera"] = incoming["use_camera"]

    project["code_customized"] = False
    project = _resolve_and_prefetch(project)
    project = _apply_theme_to_project(project)

    project.setdefault("chat", []).append({"role": "user", "content": body.message})
    project["chat"].append({"role": "assistant", "content": assistant_msg})
    store.save_project(project, snapshot=True)

    return {
        "message": assistant_msg,
        "project": project,
        "preview_url": None,
        "render_error": None,
    }


@app.post("/api/projects/{project_id}/script")
def apply_script(project_id: str, body: ScriptRequest):
    try:
        project = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        if body.use_ai:
            ai = _openai()
            parsed = ai.parse_script(body.script)
            beats = parsed.get("beats", [])
        else:
            parsed = parse_script(body.script)
            beats = parsed.get("beats", [])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        if body.use_ai:
            raise HTTPException(status_code=502, detail=f"OpenAI error: {exc}") from exc
        raise HTTPException(status_code=400, detail=f"Script parse error: {exc}") from exc

    if not beats:
        raise HTTPException(status_code=400, detail="No beats found in script")

    try:
        project["beats"] = _prepare_beats(beats)
        if parsed.get("name"):
            project["name"] = parsed["name"]
        if parsed.get("style_pack"):
            project["style_pack"] = parsed["style_pack"]
        if parsed.get("theme_id"):
            tid = parsed["theme_id"]
            if theme_store.theme_exists(tid):
                project["theme_id"] = tid
                row = theme_store.get_theme_row(tid)
                if row:
                    project["style_pack"] = row["style_pack"]
        if "use_camera" in parsed:
            project["use_camera"] = parsed["use_camera"]
        project["code_customized"] = False
        project = _resolve_and_prefetch(project)
        project = _apply_theme_to_project(project)
        project.setdefault("chat", []).append(
            {"role": "user", "content": "[Script import]\n" + body.script[:500]}
        )
        project["chat"].append(
            {"role": "assistant", "content": f"Imported {len(beats)} beat(s) from script."}
        )
        store.save_project(project, snapshot=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save project: {exc}") from exc

    return {
        "message": f"Imported {len(beats)} beat(s) from script.",
        "project": project,
        "preview_url": None,
        "render_error": None,
    }


TEMPLATE_PATH = MANIM_ROOT / "platform" / "assets" / "beat-script-template.md"
STUDIO_GUIDE_PATH = MANIM_ROOT / "platform" / "assets" / "studio-guide.md"
DOCS_DIR = MANIM_ROOT / "platform" / "assets" / "docs"
DOCS_MANIFEST_PATH = DOCS_DIR / "manifest.json"


def _load_docs_manifest() -> dict:
    if not DOCS_MANIFEST_PATH.exists():
        raise HTTPException(status_code=404, detail="Documentation manifest not found")
    import json

    return json.loads(DOCS_MANIFEST_PATH.read_text())


def _find_docs_page(slug: str) -> dict | None:
    manifest = _load_docs_manifest()
    for section in manifest.get("sections", []):
        for page in section.get("pages", []):
            if page.get("slug") == slug:
                return page
    return None


def _flat_docs_pages(manifest: dict) -> list[dict]:
    pages: list[dict] = []
    for section in manifest.get("sections", []):
        for page in section.get("pages", []):
            pages.append({**page, "section": section.get("title")})
    return pages


@app.get("/api/beat-types")
def get_beat_types():
    from beat_types import list_beat_types  # noqa: E402

    return {"beat_types": list_beat_types()}


@app.get("/api/beat-script-template")
def get_beat_script_template():
    if not TEMPLATE_PATH.exists():
        raise HTTPException(status_code=404, detail="Template file not found")
    content = TEMPLATE_PATH.read_text()
    return {
        "filename": "beat-script-template.md",
        "content": content,
    }


@app.get("/api/beat-script-template/download")
def download_beat_script_template():
    if not TEMPLATE_PATH.exists():
        raise HTTPException(status_code=404, detail="Template file not found")
    return FileResponse(
        TEMPLATE_PATH,
        media_type="text/markdown",
        filename="beat-script-template.md",
        headers={"Content-Disposition": 'attachment; filename="beat-script-template.md"'},
    )


@app.get("/api/studio-guide")
def get_studio_guide():
    if not STUDIO_GUIDE_PATH.exists():
        raise HTTPException(status_code=404, detail="Studio guide not found")
    content = STUDIO_GUIDE_PATH.read_text()
    return {
        "filename": "studio-guide.md",
        "content": content,
    }


@app.get("/api/studio-guide/download")
def download_studio_guide():
    if not STUDIO_GUIDE_PATH.exists():
        raise HTTPException(status_code=404, detail="Studio guide not found")
    return FileResponse(
        STUDIO_GUIDE_PATH,
        media_type="text/markdown",
        filename="studio-guide.md",
        headers={"Content-Disposition": 'attachment; filename="studio-guide.md"'},
    )


@app.get("/api/docs")
def get_docs_manifest():
    return _load_docs_manifest()


@app.get("/api/docs/pages/{slug}")
def get_docs_page(slug: str):
    page = _find_docs_page(slug)
    if not page:
        raise HTTPException(status_code=404, detail=f"Documentation page not found: {slug}")
    path = DOCS_DIR / page["file"]
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Documentation file missing: {page['file']}")
    content = path.read_text()
    manifest = _load_docs_manifest()
    flat = _flat_docs_pages(manifest)
    idx = next((i for i, p in enumerate(flat) if p["slug"] == slug), -1)
    prev_page = flat[idx - 1] if idx > 0 else None
    next_page = flat[idx + 1] if 0 <= idx < len(flat) - 1 else None
    return {
        "slug": slug,
        "title": page.get("title"),
        "description": page.get("description"),
        "content": content,
        "prev": {"slug": prev_page["slug"], "title": prev_page["title"]} if prev_page else None,
        "next": {"slug": next_page["slug"], "title": next_page["title"]} if next_page else None,
    }


@app.post("/api/projects/{project_id}/render")
def render_project(project_id: str, body: RenderRequest | None = None):
    try:
        project = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    body = _validate_render_body(project, body)
    renders_dir = store.render_path(project_id).parent
    write_status(
        renders_dir,
        "preview",
        {
            "status": "rendering",
            "progress": 0,
            "phase": "Preparing",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        },
    )
    return _kickoff_preview_render(project_id, body)


@app.get("/api/projects/{project_id}/render-status")
def render_status(project_id: str):
    try:
        store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    renders_dir = store.render_path(project_id).parent
    status = read_status(renders_dir, "preview")
    payload = {
        "status": status.get("status", "idle"),
        "error": status.get("error"),
        "started_at": status.get("started_at"),
        "finished_at": status.get("finished_at"),
        "progress": status.get("progress", 0),
        "phase": status.get("phase"),
        "preview_url": None,
    }
    if status.get("status") == "done" and store.render_path(project_id).exists():
        payload["preview_url"] = f"/api/projects/{project_id}/preview"
    return payload


@app.post("/api/projects/{project_id}/render/cancel")
def cancel_preview_render(project_id: str):
    try:
        store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    renders_dir = store.render_path(project_id).parent
    return cancel_render_job(project_id, "preview", renders_dir)


@app.post("/api/projects/{project_id}/export/cancel")
def cancel_export_render(project_id: str):
    try:
        store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    renders_dir = store.render_path(project_id).parent
    return cancel_render_job(project_id, "export", renders_dir)


@app.get("/api/projects/{project_id}/code")
def get_project_code(project_id: str):
    try:
        project = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _read_scene_code(project_id, project)


@app.put("/api/projects/{project_id}/code")
def save_project_code(project_id: str, body: CodeRequest):
    try:
        project = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if "class " not in body.code or "construct" not in body.code:
        raise HTTPException(
            status_code=400,
            detail="Code must define a Scene class with a construct() method.",
        )

    _write_scene_code(project_id, body.code)
    project["code_customized"] = True
    store.save_project(project, snapshot=True)

    render_error = None
    preview_url = None
    if body.render:
        try:
            _render_project(project_id, project, quality="-ql", skip_compile=True)
            preview_url = f"/api/projects/{project_id}/preview"
        except Exception as exc:
            render_error = str(exc)

    return {
        "message": "Code saved.",
        "code_customized": True,
        "preview_url": preview_url,
        "render_error": render_error,
    }


@app.post("/api/projects/{project_id}/code/regenerate")
def regenerate_project_code(project_id: str):
    """Rebuild scene code from beats JSON (discards manual edits)."""
    try:
        project = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not project.get("beats"):
        raise HTTPException(status_code=400, detail="No beats to regenerate from.")

    project = _resolve_and_prefetch(project)
    project["code_customized"] = False
    code = generate_scene_code(project, theme=_theme_for_project(project))
    store.scene_path(project_id).write_text(code)
    store.save_project(project, snapshot=True)

    return {"code": code, "code_customized": False, "message": "Regenerated from beats."}


@app.post("/api/python/format")
def format_python(body: PythonToolRequest):
    import ast

    try:
        from app.beat_compiler import _format_python

        formatted = _format_python(body.code)
        ast.parse(formatted)
        return {"code": formatted}
    except SyntaxError as exc:
        raise HTTPException(status_code=400, detail=f"Syntax error: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/python/lint")
def lint_python(body: PythonToolRequest):
    import ast

    diagnostics: list[dict] = []
    try:
        ast.parse(body.code)
    except SyntaxError as exc:
        diagnostics.append(
            {
                "line": exc.lineno or 1,
                "column": exc.offset or 1,
                "end_line": exc.lineno or 1,
                "end_column": (exc.offset or 1) + 1,
                "message": exc.msg,
                "severity": "error",
            }
        )
    return {"diagnostics": diagnostics}


@app.post("/api/projects/{project_id}/export")
def export_project(project_id: str, body: RenderRequest | None = None):
    """Render 1080p60 in the background and prepare HD download."""
    try:
        project = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    body = body or RenderRequest()
    scene_path = store.scene_path(project_id)
    if not project.get("beats") and not scene_path.exists() and body.code is None:
        raise HTTPException(status_code=400, detail="No beats or scene code to export.")

    project, skip = _prepare_render(project_id, project, body)
    return _kickoff_export_render(project_id, project, skip_compile=skip)


@app.get("/api/projects/{project_id}/export-status")
def export_status(project_id: str):
    try:
        store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    renders_dir = store.render_path(project_id).parent
    status = read_status(renders_dir, "export")
    payload = {
        "status": status.get("status", "idle"),
        "error": status.get("error"),
        "started_at": status.get("started_at"),
        "finished_at": status.get("finished_at"),
        "progress": status.get("progress", 0),
        "phase": status.get("phase"),
        "download_url": None,
        "quality": "1080p60",
    }
    if status.get("status") == "done" and store.export_path(project_id).exists():
        payload["download_url"] = f"/api/projects/{project_id}/download"
    return payload


@app.get("/api/projects/{project_id}/preview")
def preview_video(project_id: str):
    mp4 = store.render_path(project_id)
    if not mp4.exists():
        raise HTTPException(status_code=404, detail="No preview yet")
    return FileResponse(
        mp4,
        media_type="video/mp4",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )


@app.get("/api/projects/{project_id}/download")
def download_video(project_id: str):
    mp4 = store.export_path(project_id)
    if not mp4.exists():
        raise HTTPException(
            status_code=404,
            detail="No HD export yet. Click Download 1080p60 first.",
        )
    project = store.load_project(project_id)
    safe_name = re.sub(r"[^\w\-]+", "_", project.get("name", "animation"))
    return FileResponse(
        mp4,
        media_type="video/mp4",
        filename=f"{safe_name}_1080p60.mp4",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_1080p60.mp4"'},
    )
