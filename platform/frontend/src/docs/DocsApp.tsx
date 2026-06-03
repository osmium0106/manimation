import { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useParams } from "react-router-dom";
import { ArrowLeft, ChevronLeft, ChevronRight, Loader2, Menu, Sparkles } from "lucide-react";
import { DocsManifest, DocsPageResponse, getDocsManifest, getDocsPage } from "../api";
import { DocsSidebar } from "./DocsSidebar";
import { DocsTableOfContents } from "./DocsTableOfContents";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { extractHeadings } from "./docsUtils";
import { useScrollSpy } from "./useScrollSpy";
import "./docs.css";

function DocsPageView({ manifest }: { manifest: DocsManifest }) {
  const { slug = "introduction" } = useParams();
  const [page, setPage] = useState<DocsPageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    getDocsPage(slug)
      .then(setPage)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [slug]);

  useEffect(() => {
    if (page?.title) {
      document.title = `${page.title} — ${manifest.title} Docs`;
    }
  }, [page?.title, manifest.title]);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [slug]);

  const headings = page ? extractHeadings(page.content) : [];
  const showToc = headings.length >= 2;
  const activeHeadingId = useScrollSpy(headings, showToc && !loading && !error);

  return (
    <div className={`docs-main-inner${showToc ? "" : " no-toc"}`}>
      <div className="docs-content">
        {loading && (
          <div className="docs-page-loading">
            <Loader2 size={22} className="spin" />
            Loading…
          </div>
        )}
        {error && <div className="docs-page-error">{error}</div>}
        {!loading && !error && page && (
          <>
            {page.description && <p className="docs-page-lead">{page.description}</p>}
            <MarkdownRenderer content={page.content} />
            <footer className="docs-page-footer">
              <div className="docs-page-nav">
                {page.prev ? (
                  <Link to={`/docs/${page.prev.slug}`} className="docs-page-nav-link prev">
                    <ChevronLeft size={18} />
                    <span>
                      <small>Previous</small>
                      {page.prev.title}
                    </span>
                  </Link>
                ) : (
                  <span />
                )}
                {page.next ? (
                  <Link to={`/docs/${page.next.slug}`} className="docs-page-nav-link next">
                    <span>
                      <small>Next</small>
                      {page.next.title}
                    </span>
                    <ChevronRight size={18} />
                  </Link>
                ) : (
                  <span />
                )}
              </div>
              <p className="docs-footer-credit">
                Manimations Studio — documentation by {manifest.author}
              </p>
            </footer>
          </>
        )}
      </div>
      {showToc && <DocsTableOfContents headings={headings} activeId={activeHeadingId} />}
    </div>
  );
}

export function DocsApp() {
  const [manifest, setManifest] = useState<DocsManifest | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [mobileNav, setMobileNav] = useState(false);

  useEffect(() => {
    getDocsManifest()
      .then(setManifest)
      .catch((e) => setLoadError(e instanceof Error ? e.message : String(e)));
  }, []);

  if (loadError) {
    return (
      <div className="docs-shell docs-error-shell">
        <p>Failed to load documentation: {loadError}</p>
        <a href="/">Back to Studio</a>
      </div>
    );
  }

  if (!manifest) {
    return (
      <div className="docs-shell docs-loading-shell">
        <Loader2 size={28} className="spin" />
      </div>
    );
  }

  return (
    <div className="docs-shell">
      <header className="docs-header">
        <div className="docs-header-left">
          <button
            type="button"
            className="docs-menu-btn"
            onClick={() => setMobileNav(true)}
            aria-label="Open navigation"
          >
            <Menu size={20} />
          </button>
          <Link to="/docs/introduction" className="docs-brand">
            <Sparkles size={18} className="docs-brand-icon" />
            <span>
              {manifest.title}
              <small>{manifest.subtitle || "Documentation"}</small>
            </span>
          </Link>
        </div>
        <div className="docs-header-right">
          <span className="docs-version">v{manifest.version}</span>
          <a href="/" className="docs-back-studio">
            <ArrowLeft size={14} />
            Back to Studio
          </a>
        </div>
      </header>

      <div className="docs-body">
        <DocsSidebar
          manifest={manifest}
          mobileOpen={mobileNav}
          onCloseMobile={() => setMobileNav(false)}
        />
        <main className="docs-main">
          <Routes>
        <Route index element={<Navigate to="introduction" replace />} />
        <Route path=":slug" element={<DocsPageView manifest={manifest} />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
