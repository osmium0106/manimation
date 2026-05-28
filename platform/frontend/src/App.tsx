import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  Copy,
  Code2,
  Download,
  FileText,
  Film,
  Loader2,
  MessageSquare,
  RotateCcw,
  Send,
  Sparkles,
  Wand2,
  X,
  BookOpen,
} from "lucide-react";
import {
  ChatMessage,
  Project,
  Snapshot,
  BeatTypeMeta,
  beatScriptTemplateDownloadUrl,
  createProject,
  downloadUrl,
  exportHd,
  formatPython,
  getBeatScriptTemplate,
  getBeatTypes,
  getProjectCode,
  health,
  lintPython,
  listSnapshots,
  previewUrl,
  regenerateProjectCode,
  revertProject,
  renderProject,
  saveProjectCode,
  sendChat,
  submitScript,
} from "./api";
import { CodeEditor } from "./CodeEditor";
import { BeatTypePicker } from "./components/BeatTypePicker";
import { LayoutPreview } from "./components/LayoutPreview";

type PanelMode = "chat" | "script";
type PreviewView = "video" | "code";

function detectScriptBeatType(script: string): string | null {
  const blocks = script.split(/^###\s*BEAT/m).slice(1);
  const target = blocks[blocks.length - 1] ?? script;
  const m = target.match(/^TYPE:\s*(.+)$/im);
  return m?.[1]?.trim().toLowerCase().replace(/\s+/g, "_") ?? null;
}

function nextBeatNumber(script: string): number {
  const matches = script.match(/^###\s*BEAT\s*(\d+)/gim);
  if (!matches?.length) return 1;
  const nums = matches.map((line) => parseInt(line.replace(/\D/g, ""), 10));
  return Math.max(...nums) + 1;
}

export default function App() {
  const [project, setProject] = useState<Project | null>(null);
  const [mode, setMode] = useState<PanelMode>("chat");
  const [input, setInput] = useState("");
  const [script, setScript] = useState("");
  const [beatTypes, setBeatTypes] = useState<BeatTypeMeta[]>([]);
  const [selectedBeatTypeId, setSelectedBeatTypeId] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [codeCustomized, setCodeCustomized] = useState(false);
  const [useAiParse, setUseAiParse] = useState(false);
  const [loading, setLoading] = useState(false);
  const [rendering, setRendering] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportPhase, setExportPhase] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [previewKey, setPreviewKey] = useState(0);
  const [hasPreview, setHasPreview] = useState(false);
  const [previewView, setPreviewView] = useState<PreviewView>("video");
  const [hdReady, setHdReady] = useState(false);
  const [showTemplate, setShowTemplate] = useState(false);
  const [templateContent, setTemplateContent] = useState("");
  const [templateCopied, setTemplateCopied] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    health()
      .then((h) => setApiOk(h.openai_configured))
      .catch(() => setApiOk(false));
    createProject("My Animation")
      .then(setProject)
      .catch((e) => setError(String(e)));
    getBeatTypes()
      .then((res) => {
        setBeatTypes(res.beat_types);
        if (res.beat_types.length) {
          setSelectedBeatTypeId(res.beat_types[0].id);
        }
      })
      .catch(() => setBeatTypes([]));
  }, []);

  useEffect(() => {
    const detected = detectScriptBeatType(script);
    if (!detected || !beatTypes.length) return;
    const match = beatTypes.find(
      (b) =>
        b.id === detected ||
        b.id === detected.replace(/-/g, "_") ||
        b.label.toLowerCase().replace(/\s+/g, "_") === detected
    );
    if (match) setSelectedBeatTypeId(match.id);
  }, [script, beatTypes]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [project?.chat]);

  const refreshSnapshots = useCallback(async (id: string) => {
    try {
      const snaps = await listSnapshots(id);
      setSnapshots(snaps);
    } catch {
      setSnapshots([]);
    }
  }, []);

  useEffect(() => {
    if (project?.id) refreshSnapshots(project.id);
  }, [project?.id, project?.updated_at, refreshSnapshots]);

  const onPreviewReady = () => {
    setHasPreview(true);
    setPreviewKey(Date.now());
    setHdReady(false);
  };

  const beginRenderPreview = () => {
    setRendering(true);
    setHasPreview(false);
    setHdReady(false);
  };

  const loadCode = useCallback(
    async (projectId: string, opts?: { force?: boolean }) => {
      const hasGeneratedSource =
        hasPreview ||
        codeCustomized ||
        Boolean(project?.beats?.length) ||
        Boolean(project?.code_customized);

      if (!opts?.force && !hasGeneratedSource) {
        return;
      }

      try {
        const res = await getProjectCode(projectId);
        setCode(res.code);
        setCodeCustomized(res.code_customized);
      } catch {
        /* keep current editor content */
      }
    },
    [
      hasPreview,
      codeCustomized,
      project?.beats?.length,
      project?.code_customized,
    ]
  );

  useEffect(() => {
    if (previewView === "code" && project?.id) {
      loadCode(project.id);
    }
  }, [previewView, project?.id, loadCode, hasPreview, project?.beats?.length]);

  const openCodeView = () => {
    setPreviewView("code");
  };

  const canRender =
    Boolean(project?.beats.length) || codeCustomized || hasPreview;

  const runPreviewRender = async (
    projectId: string,
    options?: { code?: string; fromBeats?: boolean }
  ) => {
    const rendered = await renderProject(projectId, options);
    if (rendered.preview_url) {
      onPreviewReady();
      setPreviewView("video");
    }
    return rendered;
  };

  const handleSend = async (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || !project || loading) return;
    setInput("");
    setLoading(true);
    beginRenderPreview();
    setError(null);
    try {
      const res = await sendChat(project.id, msg);
      setProject(res.project);
      setCodeCustomized(false);
      await loadCode(project.id, { force: true });
      if (res.preview_url) {
        onPreviewReady();
        setPreviewView("video");
      } else if (res.project.beats?.length) {
        try {
          await runPreviewRender(project.id, { fromBeats: true });
        } catch (e) {
          setError(`Render: ${String(e)}`);
        }
      } else if (res.render_error) {
        setError(`Render: ${res.render_error}`);
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
      setRendering(false);
    }
  };

  const handleScriptGenerate = async () => {
    if (!project || !script.trim() || loading) return;
    setLoading(true);
    beginRenderPreview();
    setError(null);
    try {
      const res = await submitScript(project.id, script, useAiParse);
      setProject(res.project);
      setCodeCustomized(false);
      await loadCode(project.id, { force: true });
      if (res.preview_url) {
        onPreviewReady();
        setPreviewView("video");
      } else if (res.project.beats?.length) {
        try {
          await runPreviewRender(project.id, { fromBeats: true });
        } catch (e) {
          setError(`Video imported but render failed: ${String(e)}`);
        }
      } else if (res.render_error) {
        setError(`Video imported but render failed: ${res.render_error}`);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
      setRendering(false);
    }
  };

  const handleViewTemplate = async () => {
    setError(null);
    try {
      const res = await getBeatScriptTemplate();
      setTemplateContent(res.content);
      setShowTemplate(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleCopyTemplate = async () => {
    if (!templateContent) return;
    try {
      await navigator.clipboard.writeText(templateContent);
      setTemplateCopied(true);
      window.setTimeout(() => setTemplateCopied(false), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const resolveBeatTypeMeta = (typeId: string | undefined) => {
    if (!typeId || !beatTypes.length) return undefined;
    const norm = typeId.toLowerCase().replace(/\s+/g, "_").replace(/-/g, "_");
    return beatTypes.find(
      (b) =>
        b.id === norm ||
        b.id.replace(/_/g, "") === norm.replace(/_/g, "") ||
        b.label.toLowerCase().replace(/\s+/g, "_") === norm
    );
  };

  const handleInsertBeatTemplate = (bt: BeatTypeMeta) => {
    const n = nextBeatNumber(script);
    const slug = bt.id.replace(/_/g, "_");
    let tpl = bt.script_template.replace(/BEAT N/g, `BEAT ${n}`).replace(/slug_name/g, slug);
    const prefix = script.trim() ? "\n\n" : "";
    setScript((s) => s + prefix + tpl);
    setSelectedBeatTypeId(bt.id);
  };

  const previewBeatType =
    resolveBeatTypeMeta(detectScriptBeatType(script) ?? undefined) ??
    resolveBeatTypeMeta(selectedBeatTypeId ?? undefined);

  const handleCodeFormat = async () => {
    if (!code.trim()) return;
    try {
      const res = await formatPython(code);
      setCode(res.code);
    } catch (e) {
      setError(String(e));
    }
  };

  const handleCodeApply = async () => {
    if (!project || !code.trim() || loading) return;
    setLoading(true);
    beginRenderPreview();
    setError(null);
    try {
      await saveProjectCode(project.id, code, false);
      setCodeCustomized(true);
      setProject({ ...project, code_customized: true });
      const rendered = await renderProject(project.id, { code });
      setCodeCustomized(Boolean(rendered.code_customized));
      if (rendered.preview_url) {
        onPreviewReady();
        setPreviewView("video");
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
      setRendering(false);
    }
  };

  const handleCodeRegenerate = async () => {
    if (!project || loading) return;
    setLoading(true);
    setError(null);
    try {
      const res = await regenerateProjectCode(project.id);
      setCode(res.code);
      setCodeCustomized(false);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleRevert = async (snapshotId: string) => {
    if (!project) return;
    setLoading(true);
    setError(null);
    try {
      const res = await revertProject(project.id, snapshotId);
      setProject(res.project);
      setShowHistory(false);
      beginRenderPreview();
      await renderProject(project.id);
      onPreviewReady();
      await loadCode(project.id, { force: true });
      await refreshSnapshots(project.id);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
      setRendering(false);
    }
  };

  const handleRerender = async () => {
    if (!project) return;
    beginRenderPreview();
    setError(null);
    try {
      if (previewView === "code" || codeCustomized) {
        if (!code.trim()) {
          throw new Error("No scene code to render.");
        }
        await saveProjectCode(project.id, code, false);
        setCodeCustomized(true);
        setProject({ ...project, code_customized: true });
        await renderProject(project.id, { code });
      } else {
        await renderProject(project.id, { fromBeats: true });
      }
      onPreviewReady();
    } catch (e) {
      setError(String(e));
    } finally {
      setRendering(false);
    }
  };

  const handleDownloadHd = async () => {
    if (!project) return;
    setExporting(true);
    setExportProgress(0);
    setExportPhase("Starting export");
    setError(null);
    try {
      const exportOpts =
        previewView === "code" || codeCustomized
          ? { code: code.trim() || undefined }
          : { fromBeats: true };
      await exportHd(project.id, exportOpts, (progress, phase) => {
        setExportProgress(progress);
        setExportPhase(phase ?? null);
      });
      setHdReady(true);
      setExportProgress(100);
      const a = document.createElement("a");
      a.href = downloadUrl(project.id);
      a.download = `${project.name.replace(/\s+/g, "_")}_1080p60.mp4`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      setError(String(e));
    } finally {
      setExporting(false);
      setExportPhase(null);
    }
  };

  const chat: ChatMessage[] = project?.chat ?? [];

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <Film size={18} />
            <span>Manimations Studio</span>
          </div>
          {project && <span className="project-name">{project.name}</span>}
        </div>
        <div className="header-right">
          {apiOk === false && (
            <span className="badge badge-warn">Set OPENAI_API_KEY in platform/.env</span>
          )}
          <div className="history-wrap">
            <button
              className="btn-ghost"
              onClick={() => setShowHistory(!showHistory)}
              disabled={!project || snapshots.length === 0}
            >
              <RotateCcw size={16} />
              Revert
            </button>
            {showHistory && snapshots.length > 0 && (
              <div className="history-menu">
                <div className="history-title">Version history (local)</div>
                {snapshots.slice(0, 12).map((s) => (
                  <button
                    key={s.id}
                    className="history-item"
                    onClick={() => handleRevert(s.id)}
                  >
                    <span>{s.label}</span>
                    <span className="history-time">
                      {new Date(s.created_at).toLocaleString()}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="main">
        <aside className="chat-panel">
          <div className="panel-tabs">
            <button
              className={`panel-tab ${mode === "chat" ? "active" : ""}`}
              onClick={() => setMode("chat")}
            >
              <MessageSquare size={14} />
              Chat
            </button>
            <button
              className={`panel-tab ${mode === "script" ? "active" : ""}`}
              onClick={() => setMode("script")}
            >
              <FileText size={14} />
              Beat script
            </button>
          </div>

          {mode === "chat" ? (
            <>
              <div className="chat-messages">
                {chat.length === 0 && (
                  <div className="welcome">
                    <Sparkles size={28} className="welcome-icon" />
                    <h2>Describe your animation</h2>
                    <p>
                      Describe your animation in plain English, or use the Beat script
                      tab for structured scripts. Preview and code editor are on the right.
                    </p>
                  </div>
                )}
                {chat.map((m, i) => (
                  <div key={i} className={`msg msg-${m.role}`}>
                    <div className="msg-bubble">{m.content}</div>
                  </div>
                ))}
                {loading && mode === "chat" && (
                  <div className="msg msg-assistant">
                    <div className="msg-bubble typing">
                      <Loader2 size={16} className="spin" />
                      Generating beats & rendering…
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              <div className="chat-input-wrap">
                <textarea
                  className="chat-input"
                  placeholder="Describe your animation or ask for changes…"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  rows={3}
                  disabled={loading || !project}
                />
                <button
                  className="send-btn"
                  onClick={() => handleSend()}
                  disabled={loading || !input.trim() || !project}
                >
                  {loading ? <Loader2 size={18} className="spin" /> : <Send size={18} />}
                </button>
              </div>
            </>
          ) : mode === "script" ? (
            <div className="script-panel">
              {beatTypes.length > 0 && (
                <BeatTypePicker
                  beatTypes={beatTypes}
                  selectedId={selectedBeatTypeId}
                  onSelect={(bt) => setSelectedBeatTypeId(bt.id)}
                  onInsertTemplate={handleInsertBeatTemplate}
                />
              )}
              <div className="script-toolbar">
                <p className="script-hint">
                  Copy the template, fill one <code>### BEAT</code> block per idea.
                  Pick a beat type for live layout preview — output is authored, not executed.
                </p>
                <div className="script-toolbar-btns">
                  <button
                    type="button"
                    className="btn-ghost sm"
                    onClick={handleViewTemplate}
                  >
                    <BookOpen size={14} />
                    View template
                  </button>
                </div>
              </div>
              <textarea
                className="script-editor"
                value={script}
                onChange={(e) => setScript(e.target.value)}
                placeholder="Paste your beat script here — click View template to copy the starter format."
                spellCheck={false}
                disabled={loading || !project}
              />
              <label className="script-option">
                <input
                  type="checkbox"
                  checked={useAiParse}
                  onChange={(e) => setUseAiParse(e.target.checked)}
                />
                Use AI author (full manim-video skill — narration → beat script)
              </label>
              <button
                className="script-generate-btn"
                onClick={handleScriptGenerate}
                disabled={loading || !script.trim() || !project}
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="spin" />
                    Generating video…
                  </>
                ) : (
                  <>
                    <Film size={16} />
                    Generate from script
                  </>
                )}
              </button>
            </div>
          ) : null}

          {error && <div className="error-bar">{error}</div>}
        </aside>

        <section className="preview-panel">
          <div className="preview-toolbar">
            <div className="preview-view-toggle">
              <button
                type="button"
                className={`preview-view-btn ${previewView === "video" ? "active" : ""}`}
                onClick={() => setPreviewView("video")}
                title="Video preview"
              >
                <Film size={14} />
              </button>
              <button
                type="button"
                className={`preview-view-btn ${previewView === "code" ? "active" : ""}`}
                onClick={openCodeView}
                title="Manim scene code"
              >
                <Code2 size={14} />
              </button>
            </div>
            <span className="preview-label">
              {previewView === "video" ? "Preview" : "Scene code"}
            </span>
            {project && previewView === "video" && (
              <span className="beat-count">{project.beats.length} beat(s)</span>
            )}
            {previewView === "code" && codeCustomized && (
              <span className="code-badge preview-code-badge">edited</span>
            )}
            {previewView === "video" && (
              <div className="preview-toolbar-actions">
                <button
                  className="btn-ghost sm"
                  onClick={handleRerender}
                  disabled={rendering || exporting || !canRender}
                >
                  {rendering ? (
                    <Loader2 size={14} className="spin" />
                  ) : (
                    <ArrowLeft size={14} className="flip" />
                  )}
                  Re-render
                </button>
                <button
                  className="btn-download"
                  onClick={handleDownloadHd}
                  disabled={exporting || !canRender}
                  title="Render and download 1080p 60fps MP4"
                >
                  {exporting ? (
                    <Loader2 size={14} className="spin" />
                  ) : (
                    <Download size={14} />
                  )}
                  {exporting
                    ? `${exportProgress}%`
                    : "1080p60"}
                </button>
                {hdReady && !exporting && (
                  <a
                    className="btn-ghost sm hd-link"
                    href={project ? downloadUrl(project.id) : "#"}
                    download
                  >
                    Re-download HD
                  </a>
                )}
              </div>
            )}
            {previewView === "code" && (
              <div className="preview-toolbar-actions">
                <button
                  className="btn-ghost sm"
                  onClick={handleCodeFormat}
                  disabled={loading || !code.trim()}
                  title="Format Python (Ctrl+Shift+F)"
                >
                  <Wand2 size={14} />
                  Format
                </button>
                <button
                  className="btn-ghost sm"
                  onClick={handleCodeRegenerate}
                  disabled={loading || !project?.beats.length}
                  title="Regenerate code from beats"
                >
                  <RotateCcw size={14} />
                  From beats
                </button>
                <button
                  className="btn-ghost sm"
                  onClick={handleRerender}
                  disabled={rendering || loading || !code.trim() || !project}
                  title="Render current editor code"
                >
                  {rendering ? (
                    <Loader2 size={14} className="spin" />
                  ) : (
                    <ArrowLeft size={14} className="flip" />
                  )}
                  Re-render
                </button>
                <button
                  className="btn-download"
                  onClick={handleCodeApply}
                  disabled={loading || !code.trim() || !project}
                >
                  {loading && previewView === "code" ? (
                    <Loader2 size={14} className="spin" />
                  ) : (
                    <Film size={14} />
                  )}
                  Apply & Re-render
                </button>
              </div>
            )}
          </div>

          {previewView === "video" ? (
            <>
              <div className="preview-stage">
                {!hasPreview && !rendering && !loading && (
                  <div className="preview-empty">
                    <Film size={48} strokeWidth={1} />
                    <p>Your animation preview will appear here</p>
                  </div>
                )}
                {(rendering || (loading && !hasPreview)) && !exporting && (
                  <div className="preview-empty">
                    <Loader2 size={40} className="spin" />
                    <p>Rendering with Manim…</p>
                  </div>
                )}
                {exporting && (
                  <div className="preview-empty export-progress-wrap">
                    <Loader2 size={40} className="spin" />
                    <p>Exporting 1080p60…</p>
                    <div className="export-progress-bar" aria-hidden="true">
                      <div
                        className="export-progress-fill"
                        style={{ width: `${exportProgress}%` }}
                      />
                    </div>
                    <p className="export-progress-label">
                      {exportProgress}% — {exportPhase || "Rendering"}
                    </p>
                  </div>
                )}
                {project && hasPreview && !exporting && !rendering && !loading && (
                  <video
                    key={previewKey}
                    className="preview-video"
                    src={previewUrl(project.id, previewKey)}
                    controls
                    autoPlay
                    loop
                    onError={() =>
                      setError(
                        "Preview video failed to load. Try Render preview again."
                      )
                    }
                  />
                )}
              </div>

              {project && project.beats.length > 0 && (
                <div className="beats-list">
                  <div className="beats-title">Beats</div>
                  {project.beats.map((b, i) => {
                    const meta = resolveBeatTypeMeta(b.type);
                    return (
                      <div key={i} className="beat-card">
                        <div className="beat-num">{i + 1}</div>
                        <div className="beat-card-body">
                          <div className="beat-label">{b.label}</div>
                          <div className="beat-meta">
                            {b.type} · {b.layout}
                          </div>
                        </div>
                        {meta && (
                          <LayoutPreview
                            title={meta.label}
                            layout={b.layout || meta.layout}
                            regions={meta.regions}
                            compact
                          />
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
              {mode === "script" && previewBeatType && (
                <div className="preview-layout-strip">
                  <span className="preview-layout-label">Live layout</span>
                  <LayoutPreview
                    title={previewBeatType.label}
                    layout={previewBeatType.layout}
                    regions={previewBeatType.regions}
                    compact
                  />
                </div>
              )}
            </>
          ) : (
            <div className="preview-code-wrap">
              <p className="preview-code-hint">
                {hasPreview || codeCustomized || (project?.beats?.length ?? 0) > 0
                  ? "Manim Python for this project. Syntax lint + Black format. Ctrl+Shift+F to format."
                  : "Paste a Manim scene class with construct(), then Apply & Re-render — no beat script required."}
              </p>
              <CodeEditor
                value={code}
                onChange={setCode}
                disabled={loading || !project}
                onFormat={async (source) => {
                  const res = await formatPython(source);
                  return res.code;
                }}
                onLint={async (source) => {
                  const res = await lintPython(source);
                  return res.diagnostics;
                }}
              />
            </div>
          )}
        </section>
      </div>

      {showTemplate && (
        <div className="modal-overlay" onClick={() => setShowTemplate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Beat script template</h3>
              <button
                type="button"
                className="modal-close"
                onClick={() => setShowTemplate(false)}
              >
                <X size={18} />
              </button>
            </div>
            <pre className="modal-body">{templateContent}</pre>
            <div className="modal-footer">
              <button type="button" className="btn-ghost sm" onClick={handleCopyTemplate}>
                <Copy size={14} />
                {templateCopied ? "Copied!" : "Copy template"}
              </button>
              <a
                className="btn-download sm"
                href={beatScriptTemplateDownloadUrl()}
                download="beat-script-template.md"
              >
                <Download size={14} />
                Download .md
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
