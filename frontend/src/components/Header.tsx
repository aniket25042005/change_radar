import React from "react";
import { Radar, ShieldCheck, Trash2, FolderPlus, Sparkles, Bot } from "lucide-react";
import { Project } from "../api/client";

interface HeaderProps {
  projects: Project[];
  activeProject: Project | null;
  onSelectProject: (proj: Project) => void;
  onDeleteProject: (id: string) => void;
  onLoadSample: () => void;
  onOpenUpload: () => void;
  onOpenAgentStudio?: () => void;
  loadingSample: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  projects,
  activeProject,
  onSelectProject,
  onDeleteProject,
  onLoadSample,
  onOpenUpload,
  onOpenAgentStudio,
  loadingSample,
}) => {
  return (
    <header className="glass-panel" style={{ padding: "1rem 1.5rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div
            style={{
              width: "42px",
              height: "42px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(139, 92, 246, 0.2))",
              border: "1px solid rgba(6, 182, 212, 0.4)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 15px rgba(6, 182, 212, 0.2)",
            }}
          >
            <Radar style={{ color: "var(--accent-cyan)", width: "24px", height: "24px" }} />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <h1 style={{ fontSize: "1.25rem", fontWeight: 700, letterSpacing: "-0.02em" }}>ChangeRadar</h1>
              <span
                style={{
                  fontSize: "0.7rem",
                  fontWeight: 600,
                  padding: "0.15rem 0.45rem",
                  borderRadius: "9999px",
                  background: "rgba(6, 182, 212, 0.15)",
                  color: "var(--accent-cyan)",
                  border: "1px solid rgba(6, 182, 212, 0.3)",
                }}
              >
                v1.0
              </span>
            </div>
            <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Fullstack API Impact Analysis & Blast-Radius Radar
            </p>
          </div>
        </div>

        {/* Local Security Badge */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.45rem",
            padding: "0.4rem 0.8rem",
            background: "rgba(16, 185, 129, 0.1)",
            border: "1px solid rgba(16, 185, 129, 0.25)",
            borderRadius: "9999px",
            fontSize: "0.75rem",
            color: "#34d399",
            fontWeight: 500,
          }}
        >
          <ShieldCheck style={{ width: "16px", height: "16px" }} />
          <span>100% Local Sandboxed • Zero External Uploads</span>
        </div>

        {/* Actions & Project Selector */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
          {projects.length > 0 && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <select
                value={activeProject?.id || ""}
                onChange={(e) => {
                  const p = projects.find((x) => x.id === e.target.value);
                  if (p) onSelectProject(p);
                }}
                style={{ minWidth: "220px", maxWidth: "300px" }}
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.file_count} files)
                  </option>
                ))}
              </select>

              {activeProject && (
                <button
                  className="btn btn-danger"
                  onClick={() => onDeleteProject(activeProject.id)}
                  title="Delete active project"
                  style={{ padding: "0.5rem" }}
                >
                  <Trash2 style={{ width: "16px", height: "16px" }} />
                </button>
              )}
            </div>
          )}

          {activeProject && onOpenAgentStudio && (
            <button
              className="btn btn-secondary"
              onClick={onOpenAgentStudio}
              style={{
                borderColor: "rgba(6, 182, 212, 0.4)",
                background: "rgba(6, 182, 212, 0.12)",
                color: "#38bdf8",
              }}
            >
              <Bot style={{ width: "16px", height: "16px", color: "var(--accent-cyan)" }} />
              <span>LangGraph Studio</span>
            </button>
          )}

          <button className="btn btn-secondary" onClick={onOpenUpload}>
            <FolderPlus style={{ width: "16px", height: "16px" }} />
            <span>Upload ZIP</span>
          </button>

          <button
            className="btn btn-accent"
            onClick={onLoadSample}
            disabled={loadingSample}
          >
            <Sparkles style={{ width: "16px", height: "16px" }} />
            <span>{loadingSample ? "Loading..." : "Load Demo Sample"}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
