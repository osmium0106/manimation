const COLORFUL_PREFIXES = new Set([
  "fa6-brands",
  "fa-brands",
  "fa7-brands",
  "devicon",
  "devicon-plain",
  "logos",
  "twemoji",
  "noto",
  "emojione",
  "fluent-emoji-flat",
  "fluent-emoji",
  "skill-icons",
  "simple-icons",
  "catppuccin",
  "material-icon-theme",
  "vscode-icons",
  "bxl",
  "cib",
  "ion",
  "akar-icons",
  "game-icons",
]);

/** Named colors aligned with Manim + common studio picks */
export const ICON_NAMED_COLORS: Record<string, string> = {
  WHITE: "#ffffff",
  BLACK: "#000000",
  GRAY: "#9ca3af",
  SILVER: "#c0c0c0",
  YELLOW: "#fcfc00",
  GOLD: "#ffd700",
  AMBER: "#fbbf24",
  ORANGE: "#ff862f",
  RED: "#fc6255",
  ROSE: "#fb7185",
  PINK: "#f472b6",
  FUCHSIA: "#e879f9",
  PURPLE: "#9a72ac",
  VIOLET: "#8b5cf6",
  INDIGO: "#6366f1",
  BLUE: "#58a6ff",
  SKY: "#38bdf8",
  CYAN: "#22d3ee",
  TEAL: "#14b8a6",
  GREEN: "#83c167",
  LIME: "#a3e635",
  EMERALD: "#34d399",
};

export type IconColorOption = { value: string; label: string; group: string };

export const ICON_COLOR_PALETTE: IconColorOption[] = [
  { value: "ORIGINAL", label: "Original", group: "Special" },
  { value: "WHITE", label: "White", group: "Neutrals" },
  { value: "BLACK", label: "Black", group: "Neutrals" },
  { value: "#52525b", label: "Zinc 600", group: "Neutrals" },
  { value: "#71717a", label: "Zinc 500", group: "Neutrals" },
  { value: "#a1a1aa", label: "Zinc 400", group: "Neutrals" },
  { value: "#d4d4d8", label: "Zinc 300", group: "Neutrals" },
  { value: "RED", label: "Red", group: "Warm" },
  { value: "#ef4444", label: "Red 500", group: "Warm" },
  { value: "#f87171", label: "Red 400", group: "Warm" },
  { value: "#fca5a5", label: "Red 300", group: "Warm" },
  { value: "ORANGE", label: "Orange", group: "Warm" },
  { value: "#f97316", label: "Orange 500", group: "Warm" },
  { value: "#fb923c", label: "Orange 400", group: "Warm" },
  { value: "YELLOW", label: "Yellow", group: "Warm" },
  { value: "#eab308", label: "Yellow 500", group: "Warm" },
  { value: "#fde047", label: "Yellow 300", group: "Warm" },
  { value: "#fef08a", label: "Yellow 200", group: "Warm" },
  { value: "GREEN", label: "Green", group: "Green" },
  { value: "#22c55e", label: "Green 500", group: "Green" },
  { value: "#4ade80", label: "Green 400", group: "Green" },
  { value: "#86efac", label: "Green 300", group: "Green" },
  { value: "TEAL", label: "Teal", group: "Green" },
  { value: "#0d9488", label: "Teal 600", group: "Green" },
  { value: "#2dd4bf", label: "Teal 400", group: "Green" },
  { value: "BLUE", label: "Blue", group: "Cool" },
  { value: "#3b82f6", label: "Blue 500", group: "Cool" },
  { value: "#60a5fa", label: "Blue 400", group: "Cool" },
  { value: "#93c5fd", label: "Blue 300", group: "Cool" },
  { value: "CYAN", label: "Cyan", group: "Cool" },
  { value: "#06b6d4", label: "Cyan 500", group: "Cool" },
  { value: "#67e8f9", label: "Cyan 300", group: "Cool" },
  { value: "PURPLE", label: "Purple", group: "Cool" },
  { value: "#a855f7", label: "Purple 500", group: "Cool" },
  { value: "#c084fc", label: "Purple 400", group: "Cool" },
  { value: "PINK", label: "Pink", group: "Cool" },
  { value: "#ec4899", label: "Pink 500", group: "Cool" },
  { value: "#f9a8d4", label: "Pink 300", group: "Cool" },
  { value: "#3776AB", label: "Python blue", group: "Brand" },
  { value: "#3178c6", label: "TypeScript", group: "Brand" },
  { value: "#f7df1e", label: "JavaScript", group: "Brand" },
  { value: "#61dafb", label: "React cyan", group: "Brand" },
];

/** @deprecated use ICON_COLOR_PALETTE */
export const ICON_COLOR_OPTIONS = ICON_COLOR_PALETTE;

export function isColorfulIconRef(ref: string): boolean {
  const idx = ref.indexOf(":");
  if (idx <= 0) return false;
  const prefix = ref.slice(0, idx).toLowerCase();
  return COLORFUL_PREFIXES.has(prefix) || prefix.startsWith("emoji");
}

export function normalizeIconColorValue(color: string): string {
  const trimmed = color.trim();
  if (!trimmed) return "WHITE";
  if (trimmed.toUpperCase() === "ORIGINAL") return "ORIGINAL";
  const named = ICON_NAMED_COLORS[trimmed.toUpperCase()];
  if (named) return trimmed.toUpperCase();
  const hex = trimmed.startsWith("#") ? trimmed : `#${trimmed}`;
  if (/^#[0-9a-fA-F]{3,8}$/.test(hex)) return hex.toUpperCase();
  return trimmed.toUpperCase();
}

export function iconColorToHex(color: string): string | null {
  if (!color || color.toUpperCase() === "ORIGINAL") return null;
  const normalized = normalizeIconColorValue(color);
  if (normalized === "ORIGINAL") return null;
  const named = ICON_NAMED_COLORS[normalized];
  if (named) return named;
  if (/^#[0-9a-fA-F]{3,8}$/.test(normalized)) return normalized;
  return null;
}

/** Iconify CDN color param — use `#hex`, `white`, or `black` for valid SVG strokes */
export function iconColorToIconifyParam(color: string): string | null {
  const hex = iconColorToHex(color);
  if (!hex) return null;
  const lower = hex.toLowerCase();
  if (lower === "#ffffff") return "white";
  if (lower === "#000000") return "black";
  return hex;
}

export function colorsMatch(a: string, b: string): boolean {
  if (a.toUpperCase() === b.toUpperCase()) return true;
  const ha = iconColorToHex(a);
  const hb = iconColorToHex(b);
  return ha !== null && hb !== null && ha.toLowerCase() === hb.toLowerCase();
}

/** Iconify CDN thumbnail — ref format `prefix:name` → `/prefix/name.svg` */
export function iconifySvgUrl(
  ref: string,
  size = 32,
  color: string | null = "white"
): string | null {
  const idx = ref.indexOf(":");
  if (idx <= 0) return null;
  const prefix = ref.slice(0, idx);
  const name = ref.slice(idx + 1);
  if (!prefix || !name) return null;
  const params = new URLSearchParams({ height: String(size) });
  const preserveOriginal =
    color === null ||
    (typeof color === "string" && color.toUpperCase() === "ORIGINAL") ||
    isColorfulIconRef(ref);
  if (!preserveOriginal) {
    const param = iconColorToIconifyParam(color ?? "WHITE");
    if (param) params.set("color", param);
  }
  return `https://api.iconify.design/${prefix}/${name}.svg?${params}`;
}

export function defaultIconColor(ref?: string, concept?: string): string {
  if (ref && isColorfulIconRef(ref)) return "ORIGINAL";
  if (concept === "python") return "#3776AB";
  return "WHITE";
}

export function repoAssetUrl(path: string): string {
  return `/api/repo-asset?path=${encodeURIComponent(path)}`;
}

export function swatchBackground(color: string): string {
  if (color.toUpperCase() === "ORIGINAL") {
    return "conic-gradient(from 135deg, #ef4444, #facc15, #22c55e, #3b82f6, #a855f7, #ef4444)";
  }
  return iconColorToHex(color) ?? "#ffffff";
}

export function isValidHexColor(input: string): boolean {
  const trimmed = input.trim();
  const hex = trimmed.startsWith("#") ? trimmed : `#${trimmed}`;
  return /^#[0-9a-fA-F]{3}$/.test(hex) || /^#[0-9a-fA-F]{6}$/.test(hex) || /^#[0-9a-fA-F]{8}$/.test(hex);
}
