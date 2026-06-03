import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { Loader2, Search, Upload } from "lucide-react";
import { getVisualCatalog, searchIcons, uploadProjectIcon, projectIconUrl } from "../api";
import {
  defaultIconColor,
  iconifySvgUrl,
  isColorfulIconRef,
  normalizeIconColorValue,
  repoAssetUrl,
  swatchBackground,
} from "../iconifyUrl";
import { IconColorPopover } from "./IconColorPopover";

interface VisualPrimary {
  ref?: string;
  concept?: string;
  description?: string;
  kind?: string;
  color?: string;
}

interface CatalogCandidate {
  kind?: string;
  ref?: string;
  color?: string | null;
}

interface CatalogEntry {
  candidates?: CatalogCandidate[];
  tags?: string[];
  synonyms?: string[];
}

interface IconPickerProps {
  projectId: string;
  value?: VisualPrimary;
  onChange: (primary: VisualPrimary) => void;
  /** Fill available height (beat editor Icon tab). */
  expanded?: boolean;
}

type GridItem =
  | { key: string; type: "concept"; concept: string; entry: CatalogEntry }
  | { key: string; type: "iconify"; ref: string };

function primaryIconifyRef(entry: CatalogEntry | undefined): string | null {
  if (!entry?.candidates?.length) return null;
  for (const c of entry.candidates) {
    if (c.kind === "iconify" && c.ref) return c.ref;
  }
  return null;
}

function catalogPreview(
  entry: CatalogEntry | undefined,
  concept?: string,
  tint?: string
): string | null {
  const candidates = entry?.candidates ?? [];
  const iconify = candidates.find((c) => c.kind === "iconify" && c.ref);
  if (iconify?.ref) {
    const resolved =
      tint ??
      iconify.color ??
      (isColorfulIconRef(iconify.ref) ? "ORIGINAL" : "WHITE");
    return iconifySvgUrl(iconify.ref, 32, resolved) ?? null;
  }
  const brand = candidates.find((c) => c.kind === "brand" && c.ref?.startsWith("assets/"));
  if (brand?.ref) {
    return repoAssetUrl(brand.ref);
  }
  if (concept === "python") {
    return iconifySvgUrl("fa6-brands:python", 32, tint ?? "#3776AB");
  }
  return null;
}

function matchesCatalogQuery(concept: string, entry: CatalogEntry, q: string): boolean {
  if (concept.includes(q)) return true;
  if (entry.tags?.some((t) => t.toLowerCase().includes(q))) return true;
  if (entry.synonyms?.some((s) => s.toLowerCase().includes(q))) return true;
  for (const c of entry.candidates ?? []) {
    if (c.ref?.toLowerCase().includes(q)) return true;
  }
  return false;
}

function pickPrimary(
  prev: VisualPrimary | undefined,
  patch: Partial<VisualPrimary>
): VisualPrimary {
  const next = { ...prev, ...patch };
  if (patch.ref !== undefined || patch.concept !== undefined) {
    if (!patch.color) {
      next.color = defaultIconColor(next.ref, next.concept);
    }
  }
  if (patch.color !== undefined) {
    next.color = normalizeIconColorValue(patch.color);
  }
  return next;
}

function swatchStyle(value: string): CSSProperties {
  return { background: swatchBackground(value) };
}

export function IconPicker({ projectId, value, onChange, expanded = false }: IconPickerProps) {
  const [catalog, setCatalog] = useState<Record<string, CatalogEntry>>({});
  const [query, setQuery] = useState("");
  const [iconifyResults, setIconifyResults] = useState<{ ref: string }[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [colorOpen, setColorOpen] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const swatchRef = useRef<HTMLButtonElement>(null);

  const iconColor = value?.color || defaultIconColor(value?.ref, value?.concept);

  useEffect(() => {
    getVisualCatalog()
      .then((c) => setCatalog(c as Record<string, CatalogEntry>))
      .catch(() => setCatalog({}));
  }, []);

  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setIconifyResults([]);
      setSearchError(null);
      return;
    }
    const t = window.setTimeout(() => {
      setSearching(true);
      setSearchError(null);
      searchIcons(q, 32)
        .then((r) => {
          setIconifyResults(r.icons);
          if (r.icons.length === 0) {
            setSearchError("No Iconify icons found — try another word.");
          }
        })
        .catch((e) => {
          setIconifyResults([]);
          setSearchError(e instanceof Error ? e.message : "Icon search failed");
        })
        .finally(() => setSearching(false));
    }, 350);
    return () => window.clearTimeout(t);
  }, [query]);

  const gridItems = useMemo((): GridItem[] => {
    const q = query.trim().toLowerCase();
    const items: GridItem[] = [];

    const concepts = Object.entries(catalog)
      .filter(([concept, entry]) => !q || matchesCatalogQuery(concept, entry, q))
      .sort(([a], [b]) => a.localeCompare(b));

    for (const [concept, entry] of concepts) {
      items.push({ key: `concept-${concept}`, type: "concept", concept, entry });
    }

    if (q) {
      const seen = new Set(concepts.map(([c]) => c));
      for (const icon of iconifyResults) {
        if (seen.has(icon.ref)) continue;
        items.push({ key: `iconify-${icon.ref}`, type: "iconify", ref: icon.ref });
      }
    }

    return items;
  }, [catalog, query, iconifyResults]);

  const previewRef =
    value?.ref ||
    (value?.concept ? primaryIconifyRef(catalog[value.concept]) : null) ||
    null;

  const current = value?.ref || value?.concept || value?.description || "";
  const previewColor = iconColor;

  const handleUpload = async (file: File) => {
    setUploadError(null);
    setUploading(true);
    try {
      const res = await uploadProjectIcon(projectId, file);
      onChange(pickPrimary(value, { ref: res.ref, kind: "project", color: "ORIGINAL" }));
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : String(e));
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const currentPreview =
    value?.kind === "project" && value.ref
      ? projectIconUrl(projectId, value.ref.replace(/^icons\//, ""))
      : previewRef
        ? iconifySvgUrl(previewRef, 32, previewColor)
        : value?.concept
          ? catalogPreview(catalog[value.concept], value.concept, previewColor)
          : null;

  const previewKey = `${previewRef ?? value?.concept ?? ""}-${previewColor}`;

  const isActive = (item: GridItem) => {
    if (item.type === "concept") return value?.concept === item.concept;
    return value?.ref === item.ref;
  };

  const setColor = (color: string) => {
    onChange(pickPrimary(value, { color }));
    setColorOpen(false);
  };

  return (
    <div className={`icon-picker ${expanded ? "icon-picker-expanded" : ""}`}>
      <div className="icon-picker-header">
        <span>Icon / visual</span>
        <div className="icon-picker-header-end">
          <div className="icon-color-wrap">
            <button
              ref={swatchRef}
              type="button"
              className={`icon-color-swatch ${iconColor.toUpperCase() === "WHITE" ? "outline" : ""}`}
              style={swatchStyle(iconColor)}
              title="Icon color"
              aria-label="Icon color"
              aria-expanded={colorOpen}
              onClick={() => setColorOpen((o) => !o)}
            />
            {colorOpen && (
              <IconColorPopover
                value={iconColor}
                anchorEl={swatchRef.current}
                onChange={setColor}
                onClose={() => setColorOpen(false)}
              />
            )}
          </div>
          {current && (
            <div className="icon-picker-current-wrap">
              {currentPreview && (
                <img
                  key={previewKey}
                  src={currentPreview}
                  alt=""
                  className="icon-picker-current-img"
                  width={20}
                  height={20}
                />
              )}
              <code className="icon-picker-current">{current}</code>
            </div>
          )}
        </div>
      </div>

      <div className="icon-search-row">
        <Search size={14} className="icon-search-icon" />
        <input
          placeholder="Search catalog or Iconify…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {searching && <Loader2 size={14} className="spin icon-search-spinner" />}
        <input
          ref={fileRef}
          type="file"
          accept=".svg,.png,image/svg+xml,image/png"
          className="icon-upload-input"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleUpload(file);
          }}
        />
        <button
          type="button"
          className="icon-search-upload"
          disabled={uploading}
          title="Upload SVG or PNG"
          aria-label="Upload SVG or PNG"
          onClick={() => fileRef.current?.click()}
        >
          {uploading ? <Loader2 size={14} className="spin" /> : <Upload size={14} />}
        </button>
      </div>
      {searchError && !searching && <p className="icon-search-error">{searchError}</p>}
      {uploadError && <p className="icon-upload-error">{uploadError}</p>}

      <div className="icon-picker-section-label">
        {query.trim() ? "Results" : "Catalog"}
      </div>
      <div className="icon-picker-grid">
        {gridItems.length === 0 && !searching && (
          <p className="icon-grid-empty">
            {query.trim() ? "No matches — try python, question, terminal…" : "Loading catalog…"}
          </p>
        )}
        {gridItems.map((item) => {
          const active = isActive(item);
          if (item.type === "concept") {
            const thumb = catalogPreview(item.entry, item.concept);
            return (
              <button
                key={item.key}
                type="button"
                className={`icon-concept-card ${active ? "active" : ""}`}
                title={item.concept}
                onClick={() => {
                  const ref = primaryIconifyRef(item.entry);
                  onChange(
                    pickPrimary(value, {
                      concept: item.concept,
                      kind: ref ? "iconify" : item.entry.candidates?.[0]?.kind || "iconify",
                      ...(ref ? { ref } : {}),
                    })
                  );
                }}
              >
                <span className="icon-concept-thumb">
                  {thumb ? (
                    <img src={thumb} alt="" width={32} height={32} loading="lazy" />
                  ) : (
                    <span className="icon-concept-fallback">{item.concept.slice(0, 1).toUpperCase()}</span>
                  )}
                </span>
                <span className="icon-concept-label">{item.concept}</span>
              </button>
            );
          }
          const thumb = iconifySvgUrl(
            item.ref,
            32,
            isColorfulIconRef(item.ref) ? "ORIGINAL" : "WHITE"
          );
          return (
            <button
              key={item.key}
              type="button"
              className={`icon-concept-card ${active ? "active" : ""}`}
              title={item.ref}
              onClick={() =>
                onChange(
                  pickPrimary(value, {
                    ref: item.ref,
                    kind: "iconify",
                    concept: undefined,
                  })
                )
              }
            >
              <span className="icon-concept-thumb">
                {thumb ? (
                  <img src={thumb} alt="" width={32} height={32} loading="lazy" />
                ) : (
                  <span className="icon-concept-fallback">?</span>
                )}
              </span>
              <span className="icon-concept-label">{item.ref.split(":").pop()}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
