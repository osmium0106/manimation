const LAST_PROJECT_KEY = "manimations.lastProjectId";

export function getLastProjectId(): string | null {
  try {
    return localStorage.getItem(LAST_PROJECT_KEY);
  } catch {
    return null;
  }
}

export function setLastProjectId(id: string) {
  try {
    localStorage.setItem(LAST_PROJECT_KEY, id);
  } catch {
    /* ignore */
  }
}

export function clearLastProjectId() {
  try {
    localStorage.removeItem(LAST_PROJECT_KEY);
  } catch {
    /* ignore */
  }
}

export function projectIdFromUrl(): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get("project");
}

export function setProjectUrl(projectId: string) {
  const url = new URL(window.location.href);
  url.searchParams.set("project", projectId);
  window.history.replaceState({}, "", url.toString());
}

export function clearProjectUrl() {
  const url = new URL(window.location.href);
  url.searchParams.delete("project");
  window.history.replaceState({}, "", url.toString());
}
