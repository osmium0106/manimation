import { Link, useLocation } from "react-router-dom";
import { Search, X } from "lucide-react";
import { useMemo, useState } from "react";
import type { DocsManifest } from "../api";

interface DocsSidebarProps {
  manifest: DocsManifest;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

export function DocsSidebar({ manifest, mobileOpen, onCloseMobile }: DocsSidebarProps) {
  const location = useLocation();
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return manifest.sections;
    return manifest.sections
      .map((section) => ({
        ...section,
        pages: section.pages.filter(
          (p) =>
            p.title.toLowerCase().includes(q) ||
            p.description?.toLowerCase().includes(q) ||
            p.slug.toLowerCase().includes(q)
        ),
      }))
      .filter((s) => s.pages.length > 0);
  }, [manifest.sections, query]);

  return (
    <>
      <div
        className={`docs-sidebar-backdrop ${mobileOpen ? "open" : ""}`}
        onClick={onCloseMobile}
        aria-hidden
      />
      <aside className={`docs-sidebar ${mobileOpen ? "open" : ""}`}>
        <div className="docs-sidebar-search">
          <Search size={16} className="docs-search-icon" />
          <input
            type="search"
            placeholder="Search docs…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search documentation"
          />
          {query && (
            <button type="button" className="docs-search-clear" onClick={() => setQuery("")}>
              <X size={14} />
            </button>
          )}
        </div>

        <nav className="docs-nav">
          {filtered.map((section) => (
            <div key={section.title} className="docs-nav-section">
              <div className="docs-nav-section-title">{section.title}</div>
              <ul>
                {section.pages.map((page) => {
                  const href = `/docs/${page.slug}`;
                  const active = location.pathname === href;
                  return (
                    <li key={page.slug}>
                      <Link
                        to={href}
                        className={active ? "active" : undefined}
                        onClick={onCloseMobile}
                      >
                        {page.title}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
          {filtered.length === 0 && (
            <p className="docs-nav-empty">No pages match &ldquo;{query}&rdquo;</p>
          )}
        </nav>
      </aside>
    </>
  );
}
