import { useEffect, useRef, type MouseEvent } from "react";
import type { TocHeading } from "./docsUtils";

interface DocsTableOfContentsProps {
  headings: TocHeading[];
  activeId: string;
}

export function DocsTableOfContents({ headings, activeId }: DocsTableOfContentsProps) {
  const listRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    if (!activeId || !listRef.current) return;
    const activeLink = listRef.current.querySelector(`a[data-id="${activeId}"]`);
    if (activeLink instanceof HTMLElement) {
      activeLink.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }, [activeId]);

  if (headings.length < 2) return null;

  const handleClick = (id: string) => (e: MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const el = document.getElementById(id);
    if (!el) return;
    el.scrollIntoView({ behavior: "smooth", block: "start" });
    window.history.replaceState(null, "", `#${id}`);
  };

  return (
    <aside className="docs-toc" aria-label="On this page">
      <div className="docs-toc-title">On this page</div>
      <ul ref={listRef}>
        {headings.map((h) => (
          <li key={h.id} className={h.level === 3 ? "depth-3" : undefined}>
            <a
              href={`#${h.id}`}
              data-id={h.id}
              className={activeId === h.id ? "active" : undefined}
              aria-current={activeId === h.id ? "location" : undefined}
              onClick={handleClick(h.id)}
            >
              {h.text}
            </a>
          </li>
        ))}
      </ul>
    </aside>
  );
}
