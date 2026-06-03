export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface BeatEmphasis {
  word: string;
  color: string;
  animation: string;
}

export interface BeatCameraStep {
  hook: string;
  action: string;
  run_time?: number;
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
  left_lines?: string[];
  right_lines?: string[];
  hold?: number;
  icon_entrance?: string;
  continue_beat?: boolean;
  use_camera?: boolean;
  emphasis?: BeatEmphasis[];
  camera?: BeatCameraStep[];
  visuals?: Record<string, unknown>;
  visuals_resolved?: Record<string, unknown>;
}

export interface ProjectSummary {
  id: string;
  name: string;
  updated_at?: string;
  created_at?: string;
  beat_count: number;
  theme_id?: string;
  has_preview?: boolean;
}

export interface BeatValidation {
  valid: boolean;
  issue_count: number;
  warning_count: number;
  issues: { beat_index: number; label: string; code: string; message: string }[];
  warnings: { beat_index: number; label: string; code: string; message: string }[];
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
  camera_defaults?: BeatCameraStep[];
}

export interface Project {
  id: string;
  name: string;
  theme_id?: string;
  style_pack: string;
  style_brief?: string;
  pacing?: string;
  use_camera: boolean;
  beats: Beat[];
  chat: ChatMessage[];
  code_customized?: boolean;
  updated_at?: string;
}

export interface TypographyStyle {
  font: string;
  font_size: number;
  color: string;
  weight: string;
  cursor?: string | null;
}

export interface TypographySpec {
  heading: TypographyStyle;
  subheading: TypographyStyle;
  paragraph: TypographyStyle;
  code: TypographyStyle;
}

export interface PaletteSpec {
  card_fill: string;
  card_stroke: string;
  accent: string;
  emphasis_red: string;
  label_color: string;
  code_bg: string;
  code_text: string;
}

export interface ThemeSummary {
  id: string;
  name: string;
  description: string;
  style_pack: string;
  background_kind: string;
  background_loop: boolean;
  preview_url: string;
  is_builtin: boolean;
}

export interface ThemeDetail extends ThemeSummary {
  typography: TypographySpec;
  palette?: PaletteSpec | null;
  created_at: string;
  updated_at: string;
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
  progress?: number;
  phase?: string | null;
}

export interface RenderStatusResponse {
  status: "idle" | "rendering" | "done" | "error" | "cancelled";
  preview_url: string | null;
  error?: string | null;
  started_at?: string;
  finished_at?: string;
  progress?: number;
  phase?: string | null;
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

const RENDER_POLL_MS = 400;
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

export async function createProject(name = "Untitled", themeId = "builtin_orange") {
  return json<Project>(`${API}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, theme_id: themeId }),
  });
}

export async function listProjects() {
  return json<{ projects: ProjectSummary[] }>(`${API}/projects`);
}

export async function deleteProject(projectId: string) {
  return json<{ message: string }>(`${API}/projects/${projectId}`, { method: "DELETE" });
}

export async function patchProject(
  projectId: string,
  body: { theme_id?: string; name?: string; style_brief?: string; pacing?: string; use_camera?: boolean }
) {
  return json<Project>(`${API}/projects/${projectId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function listThemes() {
  return json<{ themes: ThemeSummary[] }>(`${API}/themes`);
}

export async function getTheme(themeId: string) {
  return json<ThemeDetail>(`${API}/themes/${themeId}`);
}

export function themeBackgroundUrl(themeId: string, cacheBust?: number) {
  const q = cacheBust ? `?t=${cacheBust}` : "";
  return `${API}/themes/${themeId}/background${q}`;
}

export async function createTheme(form: FormData) {
  const res = await fetch(`${API}/themes`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json() as Promise<ThemeDetail>;
}

export async function updateTheme(themeId: string, form: FormData) {
  const res = await fetch(`${API}/themes/${themeId}`, { method: "PUT", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json() as Promise<ThemeDetail>;
}

export async function deleteTheme(themeId: string) {
  return json<{ message: string }>(`${API}/themes/${themeId}`, { method: "DELETE" });
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

async function* pollRenderStatus(
  fetchStatus: () => Promise<{ status: string; progress?: number; phase?: string | null; preview_url?: string | null; download_url?: string | null; error?: string | null; quality?: string }>,
  onProgress?: (progress: number, phase?: string | null) => void,
  deadlineMs = RENDER_POLL_MAX_MS
) {
  const deadline = Date.now() + deadlineMs;
  while (Date.now() < deadline) {
    const status = await fetchStatus();
    onProgress?.(status.progress ?? 0, status.phase);
    yield status;
    if (status.status === "done" || status.status === "error" || status.status === "cancelled") {
      return;
    }
    await sleep(RENDER_POLL_MS);
  }
  throw new Error("Render timed out");
}

export async function cancelPreviewRender(projectId: string) {
  return json<RenderStatusResponse>(`${API}/projects/${projectId}/render/cancel`, {
    method: "POST",
  });
}

export async function renderProject(
  projectId: string,
  options?: { code?: string; fromBeats?: boolean },
  onProgress?: (progress: number, phase?: string | null) => void
): Promise<RenderResponse> {
  onProgress?.(0, "Preparing");

  const postPromise = json<RenderResponse>(`${API}/projects/${projectId}/render`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      code: options?.code,
      from_beats: options?.fromBeats ?? false,
    }),
  });

  const deadline = Date.now() + RENDER_POLL_MAX_MS;
  while (Date.now() < deadline) {
    try {
      const status = await getRenderStatus(projectId);
      onProgress?.(status.progress ?? 0, status.phase ?? null);

      if (status.status === "done" && status.preview_url) {
        return { status: "done", preview_url: status.preview_url };
      }
      if (status.status === "error") {
        throw new Error(status.error || "Manim render failed");
      }
      if (status.status === "cancelled") {
        throw new Error("Render cancelled");
      }
    } catch (err) {
      if (err instanceof Error && err.message.includes("Manim render failed")) {
        throw err;
      }
      if (err instanceof Error && err.message.includes("Render cancelled")) {
        throw err;
      }
    }

    const postOutcome = await Promise.race([
      postPromise.then(
        (res) => ({ ok: true as const, res }),
        (err: unknown) => ({
          ok: false as const,
          err: err instanceof Error ? err : new Error(String(err)),
        })
      ),
      sleep(0).then(() => null),
    ]);

    if (postOutcome?.ok === false) {
      throw postOutcome.err;
    }
    if (postOutcome?.ok === true && postOutcome.res.preview_url) {
      onProgress?.(100, "Complete");
      return postOutcome.res;
    }
    if (postOutcome?.ok === true && postOutcome.res.render_error) {
      throw new Error(postOutcome.res.render_error);
    }

    await sleep(RENDER_POLL_MS);
  }

  try {
    const started = await postPromise;
    if (started.preview_url) {
      onProgress?.(100, "Complete");
      return started;
    }
    if (started.render_error) {
      throw new Error(started.render_error);
    }
  } catch (err) {
    throw err instanceof Error ? err : new Error(String(err));
  }

  throw new Error("Render timed out waiting for preview");
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
  onProgress?.(0, "Starting export");
  for await (const status of pollRenderStatus(
    () => getExportStatus(projectId),
    onProgress
  )) {
    if (status.status === "done" && status.download_url) {
      return {
        status: "done",
        download_url: status.download_url,
        quality: (status as ExportStatusResponse).quality,
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

export async function getStudioGuide() {
  return json<{ filename: string; content: string }>(`${API}/studio-guide`);
}

export function studioGuideDownloadUrl() {
  return `${API}/studio-guide/download`;
}

export interface DocsPageMeta {
  slug: string;
  title: string;
  description?: string;
  file: string;
}

export interface DocsSection {
  title: string;
  pages: DocsPageMeta[];
}

export interface DocsManifest {
  title: string;
  subtitle?: string;
  author: string;
  version: string;
  sections: DocsSection[];
}

export interface DocsPageResponse {
  slug: string;
  title: string;
  description?: string;
  content: string;
  prev: { slug: string; title: string } | null;
  next: { slug: string; title: string } | null;
}

export async function getDocsManifest() {
  return json<DocsManifest>(`${API}/docs`);
}

export async function getDocsPage(slug: string) {
  return json<DocsPageResponse>(`${API}/docs/pages/${encodeURIComponent(slug)}`);
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

export async function updateProjectBeats(projectId: string, beats: Beat[], useCamera?: boolean) {
  return json<Project>(`${API}/projects/${projectId}/beats`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ beats, use_camera: useCamera }),
  });
}

export async function getProjectScript(projectId: string) {
  return json<{ script: string }>(`${API}/projects/${projectId}/script`);
}

export async function validateBeats(projectId: string) {
  return json<BeatValidation>(`${API}/projects/${projectId}/validate-beats`, {
    method: "POST",
  });
}

export async function getVisualCatalog() {
  return json<Record<string, unknown>>(`${API}/visual-catalog`);
}

export async function searchIcons(query: string, limit = 24) {
  return json<{ icons: { ref: string; prefix?: string }[] }>(
    `${API}/icons/search?q=${encodeURIComponent(query)}&limit=${limit}`
  );
}

export async function uploadProjectIcon(projectId: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API}/projects/${projectId}/icons/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json() as Promise<{ ref: string; kind: string; filename: string }>;
}

export function projectIconUrl(projectId: string, filename: string) {
  const name = filename.replace(/^icons\//, "");
  return `${API}/projects/${projectId}/icons/${encodeURIComponent(name)}`;
}
