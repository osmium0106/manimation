import { useEffect, useState } from "react";
import { Film, Loader2, Plus, Trash2 } from "lucide-react";
import {
  ProjectSummary,
  deleteProject,
  listProjects,
  previewUrl,
} from "../api";

interface ProjectHubProps {
  onOpen: (projectId: string) => void;
  onCreate: () => void;
}

export function ProjectHub({ onOpen, onCreate }: ProjectHubProps) {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const refresh = () => {
    setLoading(true);
    listProjects()
      .then((res) => setProjects(res.projects))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this project permanently?")) return;
    setDeletingId(id);
    try {
      await deleteProject(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      setError(String(err));
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="project-hub">
      <div className="project-hub-inner">
        <div className="project-hub-header">
          <div className="theme-gate-brand">
            <Film size={28} />
            <h1>Manimations Studio</h1>
          </div>
          <p className="theme-gate-lead">Your animation projects — open one or start fresh.</p>
          <button type="button" className="btn-primary" onClick={onCreate}>
            <Plus size={18} />
            New project
          </button>
        </div>

        {error && <div className="error-bar">{error}</div>}

        {loading ? (
          <div className="project-hub-loading">
            <Loader2 size={32} className="spin" />
          </div>
        ) : projects.length === 0 ? (
          <div className="project-hub-empty">
            <p>No projects yet. Create your first animation.</p>
          </div>
        ) : (
          <div className="project-grid">
            {projects.map((p) => (
              <button
                key={p.id}
                type="button"
                className="project-card"
                onClick={() => onOpen(p.id)}
              >
                <div className="project-card-thumb">
                  {p.has_preview ? (
                    <video
                      src={previewUrl(p.id)}
                      muted
                      playsInline
                      preload="metadata"
                    />
                  ) : (
                    <div className="project-card-placeholder">
                      <Film size={24} />
                    </div>
                  )}
                </div>
                <div className="project-card-body">
                  <div className="project-card-title">{p.name}</div>
                  <div className="project-card-meta">
                    {p.beat_count} beat{p.beat_count === 1 ? "" : "s"}
                    {p.updated_at && (
                      <> · {new Date(p.updated_at).toLocaleDateString()}</>
                    )}
                  </div>
                </div>
                <button
                  type="button"
                  className="project-card-delete"
                  title="Delete project"
                  disabled={deletingId === p.id}
                  onClick={(e) => handleDelete(p.id, e)}
                >
                  {deletingId === p.id ? (
                    <Loader2 size={14} className="spin" />
                  ) : (
                    <Trash2 size={14} />
                  )}
                </button>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
