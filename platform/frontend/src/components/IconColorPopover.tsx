import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Pipette } from "lucide-react";
import {
  clamp,
  hexToHsv,
  hexToRgb,
  hsvToHex,
  hsvToRgb,
  hueCss,
  rgbToHex,
  rgbToHsv,
} from "../colorUtils";
import { iconColorToHex, normalizeIconColorValue } from "../iconifyUrl";

interface IconColorPopoverProps {
  value: string;
  anchorEl: HTMLElement | null;
  onChange: (color: string) => void;
  onClose: () => void;
  /** When false, hide "Keep original" and always pick a hex/named color. */
  showOriginalOption?: boolean;
}

function initialHsv(value: string) {
  if (value.toUpperCase() === "ORIGINAL") return { h: 0, s: 100, v: 100 };
  const hex = iconColorToHex(value) ?? "#ffffff";
  return hexToHsv(hex);
}

export function IconColorPopover({
  value,
  anchorEl,
  onChange,
  onClose,
  showOriginalOption = true,
}: IconColorPopoverProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const sbRef = useRef<HTMLDivElement>(null);
  const hueRef = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ top: 0, left: 0 });
  const [hsv, setHsv] = useState(() => initialHsv(value));
  const [hexInput, setHexInput] = useState(() => iconColorToHex(value) ?? "#FFFFFF");
  const [rgb, setRgb] = useState(() => {
    const hex = iconColorToHex(value) ?? "#FFFFFF";
    const parsed = hexToRgb(hex) ?? { r: 255, g: 255, b: 255 };
    return parsed;
  });
  const [keepOriginal, setKeepOriginal] = useState(value.toUpperCase() === "ORIGINAL");

  const currentHex = keepOriginal ? "ORIGINAL" : hsvToHex(hsv.h, hsv.s, hsv.v);

  const syncFromHsv = useCallback((next: { h: number; s: number; v: number }) => {
    setKeepOriginal(false);
    setHsv(next);
    const hex = hsvToHex(next.h, next.s, next.v);
    setHexInput(hex);
    const c = hsvToRgb(next.h, next.s, next.v);
    setRgb({ r: Math.round(c.r), g: Math.round(c.g), b: Math.round(c.b) });
  }, []);

  const syncFromHex = useCallback((hex: string) => {
    const parsed = hexToRgb(hex);
    if (!parsed) return;
    setKeepOriginal(false);
    setHexInput(rgbToHex(parsed.r, parsed.g, parsed.b));
    setRgb(parsed);
    setHsv(rgbToHsv(parsed.r, parsed.g, parsed.b));
  }, []);

  useLayoutEffect(() => {
    const place = () => {
      if (!anchorEl || !panelRef.current) return;
      const rect = anchorEl.getBoundingClientRect();
      const panel = panelRef.current.getBoundingClientRect();
      let top = rect.bottom + 8;
      let left = rect.right - panel.width;
      if (left < 8) left = 8;
      if (left + panel.width > window.innerWidth - 8) {
        left = window.innerWidth - panel.width - 8;
      }
      if (top + panel.height > window.innerHeight - 8) {
        top = rect.top - panel.height - 8;
      }
      setPos({ top: Math.max(8, top), left: Math.max(8, left) });
    };
    place();
    const raf = requestAnimationFrame(place);
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
    };
  }, [anchorEl]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const pickSb = (clientX: number, clientY: number) => {
    const el = sbRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = clamp((clientX - rect.left) / rect.width, 0, 1);
    const y = clamp((clientY - rect.top) / rect.height, 0, 1);
    syncFromHsv({ h: hsv.h, s: x * 100, v: (1 - y) * 100 });
  };

  const pickHue = (clientX: number) => {
    const el = hueRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = clamp((clientX - rect.left) / rect.width, 0, 1);
    syncFromHsv({ h: x * 360, s: hsv.s, v: hsv.v });
  };

  const drag = (move: (e: PointerEvent) => void) => (e: React.PointerEvent) => {
    e.preventDefault();
    move(e.nativeEvent);
    const onMove = (ev: PointerEvent) => move(ev);
    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  };

  const tryEyedropper = async () => {
    const EyeDropperCtor = (window as Window & { EyeDropper?: new () => { open: () => Promise<{ sRGBHex: string }> } }).EyeDropper;
    if (!EyeDropperCtor) return;
    try {
      const dropper = new EyeDropperCtor();
      const result = await dropper.open();
      syncFromHex(result.sRGBHex);
    } catch {
      /* cancelled */
    }
  };

  const previewHex = keepOriginal
    ? "conic-gradient(from 135deg, #ef4444, #facc15, #22c55e, #3b82f6, #a855f7, #ef4444)"
    : currentHex;

  const content = (
    <>
      <div className="icon-color-backdrop" onClick={onClose} aria-hidden />
      <div
        ref={panelRef}
        className="icon-color-picker-portal"
        style={{ top: pos.top, left: pos.left }}
        role="dialog"
        aria-label={showOriginalOption ? "Icon color picker" : "Color picker"}
        onClick={(e) => e.stopPropagation()}
      >
        {showOriginalOption && (
        <button
          type="button"
          className={`icon-color-original-btn ${keepOriginal ? "active" : ""}`}
          onClick={() => {
            setKeepOriginal(true);
            setHexInput("ORIGINAL");
          }}
        >
          Keep original icon colors
        </button>
        )}

        <div
          ref={sbRef}
          className="icon-color-sb-panel"
          style={{ backgroundColor: hueCss(hsv.h) }}
          onPointerDown={drag((e) => pickSb(e.clientX, e.clientY))}
        >
          <div className="icon-color-sb-white" />
          <div className="icon-color-sb-black" />
          <span
            className="icon-color-sb-handle"
            style={{
              left: `${hsv.s}%`,
              top: `${100 - hsv.v}%`,
              background: keepOriginal ? "#fff" : currentHex,
            }}
          />
        </div>

        <div className="icon-color-controls-row">
          <span
            className="icon-color-preview-dot"
            style={{ background: previewHex }}
            aria-hidden
          />
          <button
            type="button"
            className="icon-color-eyedropper"
            title="Pick color from screen"
            aria-label="Eyedropper"
            onClick={() => void tryEyedropper()}
          >
            <Pipette size={16} />
          </button>
          <div
            ref={hueRef}
            className="icon-color-hue-slider"
            onPointerDown={drag((e) => pickHue(e.clientX))}
          >
            <span className="icon-color-hue-handle" style={{ left: `${(hsv.h / 360) * 100}%` }} />
          </div>
        </div>

        <div className="icon-color-inputs">
          <label className="icon-color-field">
            <span>Hex</span>
            <input
              value={keepOriginal ? "ORIGINAL" : hexInput}
              disabled={keepOriginal}
              spellCheck={false}
              onChange={(e) => {
                const v = e.target.value.trim();
                setHexInput(v.startsWith("#") ? v : `#${v}`);
              }}
              onBlur={() => {
                if (keepOriginal) return;
                const v = hexInput.startsWith("#") ? hexInput : `#${hexInput}`;
                if (hexToRgb(v)) syncFromHex(v);
              }}
            />
          </label>
          <label className="icon-color-field sm">
            <span>R</span>
            <input
              type="number"
              min={0}
              max={255}
              disabled={keepOriginal}
              value={rgb.r}
              onChange={(e) => {
                const r = clamp(parseInt(e.target.value, 10) || 0, 0, 255);
                syncFromHex(rgbToHex(r, rgb.g, rgb.b));
              }}
            />
          </label>
          <label className="icon-color-field sm">
            <span>G</span>
            <input
              type="number"
              min={0}
              max={255}
              disabled={keepOriginal}
              value={rgb.g}
              onChange={(e) => {
                const g = clamp(parseInt(e.target.value, 10) || 0, 0, 255);
                syncFromHex(rgbToHex(rgb.r, g, rgb.b));
              }}
            />
          </label>
          <label className="icon-color-field sm">
            <span>B</span>
            <input
              type="number"
              min={0}
              max={255}
              disabled={keepOriginal}
              value={rgb.b}
              onChange={(e) => {
                const b = clamp(parseInt(e.target.value, 10) || 0, 0, 255);
                syncFromHex(rgbToHex(rgb.r, rgb.g, b));
              }}
            />
          </label>
        </div>

        <div className="icon-color-actions">
          <button type="button" className="icon-color-btn ghost" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="icon-color-btn primary"
            onClick={() => {
              onChange(
                showOriginalOption && keepOriginal
                  ? "ORIGINAL"
                  : normalizeIconColorValue(currentHex)
              );
              onClose();
            }}
          >
            OK
          </button>
        </div>
      </div>
    </>
  );

  return createPortal(content, document.body);
}
