export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface Beat {
  label: string;
  type: string;
  layout: string;
  card_lines?: string[];
  bg_lines?: string[];
  punchline_line?: string;
  code_lines?: string[];
  code_output?: string;
  code_result?: string;
  list_lines?: string[];
}

export interface BeatTypeRegion {
  id: string;
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
  kind: string;
}

export interface BeatTypeMeta {
  id: string;
  label: string;
  description: string;
  layout: string;
  visuals: string[];
  regions: BeatTypeRegion[];
  script_template: string;
}

export interface Project {
  id: string;
  name: string;
  style_pack: string;
  use_camera: boolean;
  beats: Beat[];
  chat: ChatMessage[];
  code_customized?: boolean;
  updated_at?: string;
}

export interface CodeResponse {
  code: string;
  source: string;
  code_customized: boolean;
}

export interface CodeSaveResponse {
  message: string;
  code_customized: boolean;
  preview_url: string | null;
  render_error: string | null;
}

export interface Snapshot {
  id: string;
  label: string;
  created_at: string;
}

export interface ChatResponse {
  message: string;
  project: Project;
  preview_url: string | null;
  render_error: string | null;
}

export interface RenderResponse {
  status?: string;
  preview_url: string | null;
  code_customized?: boolean;
  render_error?: string | null;
}

export interface RenderStatusResponse {
  status: "idle" | "rendering" | "done" | "error";
  preview_url: string | null;
  error?: string | null;
  started_at?: string;
  finished_at?: string;
}

export interface ExportResponse {
  status?: string;
  download_url: string | null;
  quality: string;
  progress?: number;
  phase?: string | null;
  error?: string | null;
}

export interface ExportStatusResponse {
  status: "idle" | "rendering" | "done" | "error";
  download_url: string | null;
  quality: string;
  progress: number;
  phase?: string | null;
  error?: string | null;
  started_at?: string;
  finished_at?: string;
}

const API = "/api";

const RENDER_POLL_MS = 2000;
const RENDER_POLL_MAX_MS = 600_000;

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function json<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = err.detail;
    const msg = Array.isArray(detail)
      ? detail.map((d: { msg?: string }) => d.msg).join(", ")
      : detail || res.statusText;
    throw new Error(msg);
  }
  return res.json();
}

export async function health() {
  return json<{ status: string; openai_configured: boolean; data_dir: string }>(
    `${API}/health`
  );
}

export async function createProject(name = "Untitled") {
  return json<Project>(`${API}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

export async function getProject(id: string) {
  return json<Project>(`${API}/projects/${id}`);
}

export async function sendChat(projectId: string, message: string) {
  return json<ChatResponse>(`${API}/projects/${projectId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
}

export async function getRenderStatus(projectId: string) {
  return json<RenderStatusResponse>(`${API}/projects/${projectId}/render-status`);
}

async function waitForPreviewRender(projectId: string): Promise<RenderResponse> {
  const deadline = Date.now() + RENDER_POLL_MAX_MS;
  while (Date.now() < deadline) {
    await sleep(RENDER_POLL_MS);
    const status = await getRenderStatus(projectId);
    if (status.status === "done" && status.preview_url) {
      return { status: "done", preview_url: status.preview_url };
    }
    if (status.status === "error") {
      throw new Error(status.error || "Manim render failed");
    }
  }
  throw new Error("Render timed out waiting for preview");
}

export async function renderProject(
  projectId: string,
  options?: { code?: string; fromBeats?: boolean }
) {
  const started = await json<RenderResponse>(`${API}/projects/${projectId}/render`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      code: options?.code,
      from_beats: options?.fromBeats ?? false,
    }),
  });

  if (started.preview_url) {
    return started;
  }
  if (started.status === "rendering" || started.status === "idle") {
    return waitForPreviewRender(projectId);
  }
  if (started.render_error) {
    throw new Error(started.render_error);
  }
  return started;
}

export async function submitScript(
  projectId: string,
  script: string,
  useAi = false
) {
  return json<ChatResponse>(`${API}/projects/${projectId}/script`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ script, use_ai: useAi }),
  });
}

export async function getExportStatus(projectId: string) {
  return json<ExportStatusResponse>(`${API}/projects/${projectId}/export-status`);
}

async function waitForExportRender(
  projectId: string,
  onProgress?: (progress: number, phase?: string | null) => void
): Promise<ExportResponse> {
  const deadline = Date.now() + RENDER_POLL_MAX_MS;
  while (Date.now() < deadline) {
    await sleep(RENDER_POLL_MS);
    const status = await getExportStatus(projectId);
    onProgress?.(status.progress ?? 0, status.phase);
    if (status.status === "done" && status.download_url) {
      return {
        status: "done",
        download_url: status.download_url,
        quality: status.quality,
        progress: 100,
        phase: status.phase,
      };
    }
    if (status.status === "error") {
      throw new Error(status.error || "1080p export failed");
    }
  }
  throw new Error("1080p export timed out waiting for render");
}

export async function exportHd(
  projectId: string,
  options?: { code?: string; fromBeats?: boolean },
  onProgress?: (progress: number, phase?: string | null) => void
) {
  onProgress?.(0, "Starting export");
  const started = await json<ExportResponse>(`${API}/projects/${projectId}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      code: options?.code,
      from_beats: options?.fromBeats ?? false,
    }),
  });

  if (started.download_url) {
    onProgress?.(100, "Complete");
    return started;
  }
  if (started.status === "rendering" || started.status === "idle") {
    return waitForExportRender(projectId, onProgress);
  }
  if (started.error) {
    throw new Error(started.error);
  }
  return started;
}

export function downloadUrl(projectId: string) {
  return `${API}/projects/${projectId}/download`;
}

export async function getBeatTypes() {
  return json<{ beat_types: BeatTypeMeta[] }>(`${API}/beat-types`);
}

export async function getBeatScriptTemplate() {
  return json<{ filename: string; content: string }>(`${API}/beat-script-template`);
}

export function beatScriptTemplateDownloadUrl() {
  return `${API}/beat-script-template/download`;
}

export async function getProjectCode(projectId: string) {
  return json<CodeResponse>(`${API}/projects/${projectId}/code`);
}

export async function saveProjectCode(
  projectId: string,
  code: string,
  render = true
) {
  return json<CodeSaveResponse>(`${API}/projects/${projectId}/code`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, render }),
  });
}

export async function regenerateProjectCode(projectId: string) {
  return json<{ code: string; code_customized: boolean; message: string }>(
    `${API}/projects/${projectId}/code/regenerate`,
    { method: "POST" }
  );
}

export async function listSnapshots(projectId: string) {
  return json<Snapshot[]>(`${API}/projects/${projectId}/snapshots`);
}

export async function revertProject(projectId: string, snapshotId: string) {
  return json<{ project: Project; message: string }>(
    `${API}/projects/${projectId}/revert`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ snapshot_id: snapshotId }),
    }
  );
}

export function previewUrl(projectId: string, cacheBust?: number) {
  const q = cacheBust ? `?t=${cacheBust}` : "";
  return `${API}/projects/${projectId}/preview${q}`;
}

export interface PythonDiagnostic {
  line: number;
  column: number;
  end_line: number;
  end_column: number;
  message: string;
  severity: "error" | "warning" | "info";
}

export async function formatPython(code: string) {
  return json<{ code: string }>(`${API}/python/format`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
}

export async function lintPython(code: string) {
  return json<{ diagnostics: PythonDiagnostic[] }>(`${API}/python/lint`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
}
