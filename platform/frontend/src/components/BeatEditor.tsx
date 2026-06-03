import { useRef, useState } from "react";
import { Copy, Plus, Trash2 } from "lucide-react";
import { Beat, BeatCameraStep, BeatEmphasis, BeatTypeMeta, updateProjectBeats } from "../api";
import { Button } from "./Button";
import { IconColorPopover } from "./IconColorPopover";
import { IconPicker } from "./IconPicker";
import { LayoutPreview } from "./LayoutPreview";
import { iconColorToHex, normalizeIconColorValue, swatchBackground } from "../iconifyUrl";

const LAYOUTS = [
  "card_right_icon_left",
  "card_left_icon_right",
  "text_right_icon_left",
  "text_left_icon_right",
  "code_full_card",
  "dual_card",
  "card_right_only",
  "card_left_only",
];

const FALLBACK_TYPES = [
  "statement",
  "question",
  "joke",
  "explain",
  "recap",
  "code_demo",
  "list",
  "compare",
];

const ENTRANCES = [
  { value: "fade_in", label: "Fade in" },
  { value: "pop_in", label: "Pop in" },
  { value: "slide_from_left", label: "Slide from left" },
  { value: "slide_from_right", label: "Slide from right" },
  { value: "pulse", label: "Pulse" },
  { value: "none", label: "Instant (no animation)" },
];

const EMPHASIS_ANIMATIONS = [
  { value: "indicate", label: "Indicate (pulse highlight)" },
  { value: "wiggle", label: "Wiggle" },
];

const DEFAULT_EMPHASIS_COLOR = "#FC6255";

const CAMERA_ACTIONS = [
  { value: "cam_focus_left", label: "Focus left (icon panel)" },
  { value: "cam_focus_right", label: "Focus right (card / text)" },
  { value: "cam_focus_card", label: "Focus card" },
  { value: "cam_focus_mobject", label: "Focus mobject" },
  { value: "cam_restore", label: "Restore (full frame)" },
  { value: "cam_restore_fast", label: "Restore (fast)" },
  { value: "cam_pan_left", label: "Pan left" },
  { value: "cam_pan_right", label: "Pan right" },
];

const CAMERA_HOOKS = [
  { value: "after_icon", label: "After icon entrance" },
  { value: "after_line_1", label: "After line 1 typed" },
  { value: "after_line_2", label: "After line 2 typed" },
  { value: "after_line_3", label: "After line 3 typed" },
  { value: "after_code", label: "After code block" },
  { value: "after_output", label: "After code output" },
  { value: "after_run", label: "After run button" },
  { value: "punchline", label: "Punchline moment" },
  { value: "exit", label: "Beat exit" },
];

type BeatFormTab = "content" | "icon" | "emphasis" | "camera";

interface BeatEditorProps {
  projectId: string;
  beats: Beat[];
  beatTypes: BeatTypeMeta[];
  pacing?: string;
  onChange: (beats: Beat[]) => void;
  onSaved?: () => void;
}

type VisualPrimary = {
  ref?: string;
  concept?: string;
  kind?: string;
  color?: string;
};

function blankBeat(): Beat {
  return {
    label: "New beat",
    type: "statement",
    layout: "card_right_icon_left",
    card_lines: ["Your text here"],
    hold: 1.5,
  };
}

function blankEmphasis(): BeatEmphasis {
  return { word: "", color: DEFAULT_EMPHASIS_COLOR, animation: "wiggle" };
}

function blankCameraStep(): BeatCameraStep {
  return { action: "cam_focus_left", hook: "after_icon", run_time: 0.9 };
}

function linesField(beat: Beat): string {
  if (beat.bg_lines?.length) return beat.bg_lines.join("\n");
  if (beat.card_lines?.length) return beat.card_lines.join("\n");
  if (beat.list_lines?.length) return beat.list_lines.join("\n");
  return "";
}

function setLinesField(beat: Beat, text: string): Beat {
  const lines = text.split("\n").filter((l) => l.trim());
  const layout = beat.layout || "";
  if (layout.includes("text_") || beat.type === "question") {
    return { ...beat, bg_lines: lines, card_lines: undefined };
  }
  if (beat.type === "list") {
    return { ...beat, list_lines: lines, card_lines: undefined };
  }
  return { ...beat, card_lines: lines, bg_lines: undefined };
}

function getPrimary(beat: Beat): VisualPrimary {
  return ((beat.visuals as { primary?: VisualPrimary })?.primary || {}) as VisualPrimary;
}

function layoutForType(type: string, beatTypes: BeatTypeMeta[], current: string): string {
  const meta = beatTypes.find((b) => b.id === type || b.id === type.replace(/\s+/g, "_"));
  return meta?.layout || current;
}

function tabCount(beat: Beat, tab: BeatFormTab): number | null {
  if (tab === "emphasis") {
    const n = beat.emphasis?.length ?? 0;
    return n > 0 ? n : null;
  }
  if (tab === "camera") {
    const n = beat.camera?.length ?? 0;
    return n > 0 ? n : null;
  }
  return null;
}

function beatContentText(beat: Beat): string {
  return [
    ...(beat.card_lines || []),
    ...(beat.bg_lines || []),
    ...(beat.list_lines || []),
    ...(beat.left_lines || []),
    ...(beat.right_lines || []),
    beat.punchline_line || "",
  ].join(" ");
}

function wordInBeatContent(word: string, beat: Beat): boolean {
  const trimmed = word.trim();
  if (!trimmed) return true;
  const full = beatContentText(beat);
  const compact = (s: string) => s.replace(/\s+/g, "").toLowerCase();
  return compact(full).includes(compact(trimmed)) || full.toLowerCase().includes(trimmed.toLowerCase());
}

function EmphasisColorSwatch({
  value,
  onChange,
}: {
  value: string;
  onChange: (color: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const swatchRef = useRef<HTMLButtonElement>(null);
  const hex = iconColorToHex(value) ?? DEFAULT_EMPHASIS_COLOR;
  const isLight = hex.toLowerCase() === "#ffffff" || hex.toLowerCase() === "#fff";

  return (
    <div className="icon-color-wrap emphasis-color-wrap">
      <button
        ref={swatchRef}
        type="button"
        className={`icon-color-swatch emphasis-color-swatch ${isLight ? "outline" : ""}`}
        style={{ background: swatchBackground(value || DEFAULT_EMPHASIS_COLOR) }}
        title={`Emphasis color ${hex}`}
        aria-label="Emphasis color"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      />
      {open && (
        <IconColorPopover
          value={value || DEFAULT_EMPHASIS_COLOR}
          anchorEl={swatchRef.current}
          showOriginalOption={false}
          onChange={(color) => {
            onChange(normalizeIconColorValue(color));
            setOpen(false);
          }}
          onClose={() => setOpen(false)}
        />
      )}
    </div>
  );
}

export function BeatEditor({
  projectId,
  beats,
  beatTypes,
  pacing,
  onChange,
  onSaved,
}: BeatEditorProps) {
  const [selected, setSelected] = useState(0);
  const [activeTab, setActiveTab] = useState<BeatFormTab>("content");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const beat = beats[selected] ?? beats[0];
  const meta = beatTypes.find((b) => b.id === beat?.type);
  const typeOptions =
    beatTypes.length > 0
      ? beatTypes.map((b) => ({ id: b.id, label: b.label || b.id }))
      : FALLBACK_TYPES.map((id) => ({ id, label: id }));

  const patchBeat = (patch: Partial<Beat>) => {
    const next = beats.map((b, i) => (i === selected ? { ...b, ...patch } : b));
    onChange(next);
  };

  const patchBeatAt = (index: number, patch: Partial<Beat>) => {
    const next = beats.map((b, i) => (i === index ? { ...b, ...patch } : b));
    onChange(next);
  };

  const changeType = (index: number, type: string) => {
    const b = beats[index];
    patchBeatAt(index, {
      type,
      layout: layoutForType(type, beatTypes, b.layout || "card_right_icon_left"),
    });
  };

  const moveBeat = (from: number, to: number) => {
    if (to < 0 || to >= beats.length) return;
    const next = [...beats];
    const [item] = next.splice(from, 1);
    next.splice(to, 0, item);
    onChange(next);
    setSelected(to);
  };

  const duplicateBeat = () => {
    const copy = JSON.parse(JSON.stringify(beat)) as Beat;
    copy.label = `${copy.label} (copy)`;
    const next = [...beats];
    next.splice(selected + 1, 0, copy);
    onChange(next);
    setSelected(selected + 1);
  };

  const deleteBeat = () => {
    if (beats.length <= 1) return;
    const next = beats.filter((_, i) => i !== selected);
    onChange(next);
    setSelected(Math.max(0, selected - 1));
  };

  const saveBeats = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateProjectBeats(projectId, beats);
      onChange(updated.beats);
      onSaved?.();
    } catch (e) {
      setError(String(e));
    } finally {
      setSaving(false);
    }
  };

  const patchEmphasis = (emphasis: BeatEmphasis[]) => patchBeat({ emphasis });

  const updateEmphasis = (index: number, patch: Partial<BeatEmphasis>) => {
    const list = [...(beat.emphasis || [])];
    list[index] = { ...list[index], ...patch };
    patchEmphasis(list);
  };

  const addEmphasis = () => patchEmphasis([...(beat.emphasis || []), blankEmphasis()]);

  const removeEmphasis = (index: number) => {
    patchEmphasis((beat.emphasis || []).filter((_, i) => i !== index));
  };

  const patchCamera = (camera: BeatCameraStep[]) => patchBeat({ camera });

  const updateCameraStep = (index: number, patch: Partial<BeatCameraStep>) => {
    const list = [...(beat.camera || [])];
    list[index] = { ...list[index], ...patch };
    patchCamera(list);
  };

  const addCameraStep = () => patchCamera([...(beat.camera || []), blankCameraStep()]);

  const removeCameraStep = (index: number) => {
    patchCamera((beat.camera || []).filter((_, i) => i !== index));
  };

  const applyTypeCameraDefaults = () => {
    const defaults = meta?.camera_defaults || [];
    if (!defaults.length) return;
    patchBeat({
      use_camera: true,
      camera: defaults.map((step) => ({
        action: step.action,
        hook: step.hook,
        run_time: step.run_time ?? 0.9,
      })),
    });
  };

  const primary = getPrimary(beat);

  const formTabs: { id: BeatFormTab; label: string }[] = [
    { id: "content", label: "Content" },
    { id: "icon", label: "Icon" },
    { id: "emphasis", label: "Emphasis" },
    { id: "camera", label: "Camera" },
  ];

  if (!beat) {
    return (
      <div className="beat-editor-empty">
        <p>No beats yet. Use Chat or Beat script to add content.</p>
        <button type="button" className="btn-ghost sm" onClick={() => onChange([blankBeat()])}>
          <Plus size={14} /> Add blank beat
        </button>
      </div>
    );
  }

  return (
    <div className="beat-editor">
      <div className="beat-editor-toolbar">
        <span className="beat-editor-title">Beat timeline</span>
        <div className="beat-editor-toolbar-actions">
          <Button
            variant="icon"
            size="icon"
            icon={<Copy size={15} />}
            title="Duplicate beat"
            aria-label="Duplicate beat"
            onClick={duplicateBeat}
          />
          <Button
            variant="icon"
            size="icon"
            className="ui-btn-danger"
            icon={<Trash2 size={15} />}
            title="Delete beat"
            aria-label="Delete beat"
            disabled={beats.length <= 1}
            onClick={deleteBeat}
          />
          <Button
            variant="icon"
            size="icon"
            icon={<Plus size={15} />}
            title="Add beat"
            aria-label="Add beat"
            onClick={() => onChange([...beats, blankBeat()])}
          />
          <Button variant="primary" size="sm" loading={saving} onClick={saveBeats}>
            Save beats
          </Button>
        </div>
      </div>
      {error && <div className="error-bar compact">{error}</div>}

      <div className="beat-editor-body">
        <div className="beat-timeline-col">
          <ol className="beat-timeline">
            {beats.map((b, i) => (
              <li
                key={i}
                className={`beat-timeline-item ${i === selected ? "active" : ""}`}
                onClick={() => setSelected(i)}
              >
                <span className="beat-timeline-num">{i + 1}</span>
                <div className="beat-timeline-text">
                  <span className="beat-timeline-label">{b.label || `Beat ${i + 1}`}</span>
                  <div className="beat-timeline-meta">
                    <span className="beat-timeline-type-badge">{b.type}</span>
                    {(b.emphasis?.length ?? 0) > 0 && (
                      <span className="beat-timeline-pill emphasis" title="Emphasis words">
                        E{b.emphasis!.length}
                      </span>
                    )}
                    {(b.camera?.length ?? 0) > 0 && (
                      <span className="beat-timeline-pill camera" title="Camera steps">
                        C{b.camera!.length}
                      </span>
                    )}
                    {b.use_camera && (
                      <span className="beat-timeline-pill camera-on" title="Camera enabled">
                        cam
                      </span>
                    )}
                  </div>
                </div>
                <div className="beat-timeline-actions">
                  <button type="button" className="btn-icon" onClick={(e) => { e.stopPropagation(); moveBeat(i, i - 1); }}>↑</button>
                  <button type="button" className="btn-icon" onClick={(e) => { e.stopPropagation(); moveBeat(i, i + 1); }}>↓</button>
                </div>
              </li>
            ))}
          </ol>

          <div className="beat-timeline-footer">
            <label className="beat-timeline-control">
              <span>Beat type</span>
              <select
                value={beat.type}
                onChange={(e) => changeType(selected, e.target.value)}
              >
                {typeOptions.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        <div className={`beat-form-col ${activeTab === "icon" ? "icon-tab-active" : ""}`}>
          <div className="panel-tabs beat-form-tabs">
            {formTabs.map((tab) => {
              const count = tabCount(beat, tab.id);
              return (
                <button
                  key={tab.id}
                  type="button"
                  className={`panel-tab ${activeTab === tab.id ? "active" : ""}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                  {count != null && <span className="beat-tab-count">{count}</span>}
                </button>
              );
            })}
          </div>

          <div className="beat-form">
            {activeTab === "content" && (
              <>
                {meta && (
                  <LayoutPreview
                    title={meta.label}
                    layout={meta.layout}
                    regions={meta.regions}
                    compact
                  />
                )}

                <label className="beat-field">
                  <span>Label</span>
                  <input value={beat.label} onChange={(e) => patchBeat({ label: e.target.value })} />
                </label>

                <div className="beat-field-row">
                  <label className="beat-field">
                    <span>Type</span>
                    <select value={beat.type} onChange={(e) => changeType(selected, e.target.value)}>
                      {typeOptions.map((t) => (
                        <option key={t.id} value={t.id}>{t.label}</option>
                      ))}
                    </select>
                  </label>
                  <label className="beat-field">
                    <span>Layout</span>
                    <select value={beat.layout} onChange={(e) => patchBeat({ layout: e.target.value })}>
                      {LAYOUTS.map((l) => (
                        <option key={l} value={l}>{l}</option>
                      ))}
                    </select>
                  </label>
                </div>

                <label className="beat-field">
                  <span>Text lines (one per line)</span>
                  <textarea
                    rows={4}
                    value={linesField(beat)}
                    onChange={(e) => patchBeat(setLinesField(beat, e.target.value))}
                  />
                </label>

                {beat.type === "joke" && (
                  <label className="beat-field">
                    <span>Punchline line</span>
                    <input
                      value={beat.punchline_line || ""}
                      onChange={(e) => patchBeat({ punchline_line: e.target.value })}
                      placeholder="Final punchline (typed after setup fades)"
                    />
                  </label>
                )}

                <div className="beat-field-row">
                  <label className="beat-field">
                    <span>Hold (seconds)</span>
                    <input
                      type="number"
                      step={0.1}
                      min={0}
                      value={beat.hold ?? (pacing === "dense" ? 1.0 : 1.5)}
                      onChange={(e) => patchBeat({ hold: parseFloat(e.target.value) || 1.5 })}
                    />
                  </label>
                </div>

                <label className="beat-field-checkbox">
                  <input
                    type="checkbox"
                    checked={Boolean(beat.continue_beat)}
                    onChange={(e) => patchBeat({ continue_beat: e.target.checked })}
                  />
                  Continue into next beat (no wipe transition)
                </label>
              </>
            )}

            {activeTab === "icon" && (
              <div className="beat-form-icon-tab">
                <div className="beat-form-icon-controls">
                  <label className="beat-field">
                    <span>Icon entrance</span>
                    <select
                      value={beat.icon_entrance || "fade_in"}
                      onChange={(e) => patchBeat({ icon_entrance: e.target.value })}
                    >
                      {ENTRANCES.map((en) => (
                        <option key={en.value} value={en.value}>{en.label}</option>
                      ))}
                    </select>
                  </label>
                  <p className="beat-tab-hint">
                    Camera pans to the icon panel before the entrance animation when camera is enabled on this beat.
                  </p>
                </div>

                <IconPicker
                  expanded
                  projectId={projectId}
                  value={primary}
                  onChange={(p) => patchBeat({ visuals: { ...(beat.visuals || {}), primary: p } })}
                />
              </div>
            )}

            {activeTab === "emphasis" && (
              <>
                <p className="beat-tab-hint">
                  Highlight words as lines are typed. The word must appear in this beat&apos;s text (Content tab). If it doesn&apos;t match any line, nothing happens — no error, the emphasis is skipped silently at render time.
                </p>

                <div className="beat-list-editor">
                  {(beat.emphasis || []).length === 0 && (
                    <p className="beat-list-empty">No emphasis words yet.</p>
                  )}
                  {(beat.emphasis || []).map((em, i) => {
                    const missing = em.word.trim() && !wordInBeatContent(em.word, beat);
                    return (
                    <div key={i} className="beat-list-row">
                      <div className="beat-card-header">
                        <span className="beat-card-title">
                          {em.word.trim() ? `"${em.word.trim()}"` : `Emphasis ${i + 1}`}
                        </span>
                        <div className="beat-card-header-actions">
                          <EmphasisColorSwatch
                            value={em.color || DEFAULT_EMPHASIS_COLOR}
                            onChange={(color) => updateEmphasis(i, { color })}
                          />
                          <Button
                            variant="icon"
                            size="icon"
                            className="ui-btn-danger"
                            icon={<Trash2 size={14} />}
                            title="Remove emphasis"
                            aria-label="Remove emphasis"
                            onClick={() => removeEmphasis(i)}
                          />
                        </div>
                      </div>
                      <div className="beat-card-body">
                        <label className="beat-field">
                          <span>Word</span>
                          <input
                            value={em.word}
                            onChange={(e) => updateEmphasis(i, { word: e.target.value })}
                            placeholder="e.g. Python"
                            className={missing ? "beat-input-warn" : undefined}
                          />
                          {missing && (
                            <span className="beat-field-note warn">
                              Not found in beat text — render will skip this emphasis.
                            </span>
                          )}
                        </label>
                        <label className="beat-field">
                          <span>Animation</span>
                          <select
                            value={em.animation || "indicate"}
                            onChange={(e) => updateEmphasis(i, { animation: e.target.value })}
                          >
                            {EMPHASIS_ANIMATIONS.map((a) => (
                              <option key={a.value} value={a.value}>{a.label}</option>
                            ))}
                          </select>
                        </label>
                      </div>
                    </div>
                    );
                  })}
                </div>

                <Button variant="ghost" size="sm" icon={<Plus size={14} />} onClick={addEmphasis}>
                  Add emphasis word
                </Button>
              </>
            )}

            {activeTab === "camera" && (
              <>
                <label className="beat-field-checkbox">
                  <input
                    type="checkbox"
                    checked={Boolean(beat.use_camera)}
                    onChange={(e) => patchBeat({ use_camera: e.target.checked })}
                  />
                  Use moving camera on this beat
                </label>

                <p className="beat-tab-hint">
                  When checked, this beat opts into the episode&apos;s moving camera. Camera steps below run at narrative hooks (after icon, after a typed line, punchline, exit). Uncheck to keep the frame static even if the project uses a moving camera elsewhere. Include <code>cam_restore: exit</code> on camera beats.
                </p>

                <div className="beat-list-editor-toolbar">
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={!meta?.camera_defaults?.length}
                    onClick={applyTypeCameraDefaults}
                  >
                    Load defaults for {meta?.label || beat.type}
                  </Button>
                </div>

                <div className="beat-list-editor">
                  {(beat.camera || []).length === 0 && (
                    <p className="beat-list-empty">No camera steps yet.</p>
                  )}
                  {(beat.camera || []).map((step, i) => (
                    <div key={i} className="beat-list-row">
                      <div className="beat-card-header">
                        <span className="beat-card-title">
                          {CAMERA_ACTIONS.find((a) => a.value === step.action)?.label.split(" (")[0] || step.action}
                        </span>
                        <div className="beat-card-header-actions">
                          <label className="beat-card-duration">
                            <span>Duration</span>
                            <input
                              type="number"
                              step={0.1}
                              min={0.1}
                              value={step.run_time ?? 0.9}
                              onChange={(e) => updateCameraStep(i, { run_time: parseFloat(e.target.value) || 0.9 })}
                              aria-label="Duration in seconds"
                            />
                            <span>s</span>
                          </label>
                          <Button
                            variant="icon"
                            size="icon"
                            className="ui-btn-danger"
                            icon={<Trash2 size={14} />}
                            title="Remove camera step"
                            aria-label="Remove camera step"
                            onClick={() => removeCameraStep(i)}
                          />
                        </div>
                      </div>
                      <div className="beat-card-body">
                        <label className="beat-field">
                          <span>Action</span>
                          <select
                            value={step.action}
                            onChange={(e) => updateCameraStep(i, { action: e.target.value })}
                          >
                            {CAMERA_ACTIONS.map((a) => (
                              <option key={a.value} value={a.value}>{a.label}</option>
                            ))}
                          </select>
                        </label>
                        <label className="beat-field">
                          <span>Hook</span>
                          <select
                            value={step.hook}
                            onChange={(e) => updateCameraStep(i, { hook: e.target.value })}
                          >
                            {CAMERA_HOOKS.map((h) => (
                              <option key={h.value} value={h.value}>{h.label}</option>
                            ))}
                          </select>
                        </label>
                      </div>
                    </div>
                  ))}
                </div>

                <Button variant="ghost" size="sm" icon={<Plus size={14} />} onClick={addCameraStep}>
                  Add camera step
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
