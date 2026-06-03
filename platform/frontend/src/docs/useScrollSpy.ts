import { useEffect, useState } from "react";
import type { TocHeading } from "./docsUtils";

/** Sticky docs header + breathing room */
const SCROLL_OFFSET = 96;

export function useScrollSpy(headings: TocHeading[], enabled: boolean) {
  const [activeId, setActiveId] = useState("");

  const headingKey = headings.map((h) => h.id).join("|");

  useEffect(() => {
    if (!enabled || !headings.length) {
      setActiveId("");
      return;
    }

    const updateActive = () => {
      const marker = window.scrollY + SCROLL_OFFSET;
      let current = headings[0].id;

      for (const { id } of headings) {
        const el = document.getElementById(id);
        if (!el) continue;
        const top = el.getBoundingClientRect().top + window.scrollY;
        if (top <= marker + 1) {
          current = id;
        }
      }

      setActiveId(current);
    };

    updateActive();
    window.addEventListener("scroll", updateActive, { passive: true });
    window.addEventListener("resize", updateActive);
    return () => {
      window.removeEventListener("scroll", updateActive);
      window.removeEventListener("resize", updateActive);
    };
  }, [enabled, headingKey, headings]);

  return activeId;
}
