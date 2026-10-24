import React, { useState } from "react";
import { Check, Copy, X, Terminal, Sparkles, Wand2, RotateCcw } from "lucide-react";
import { applyPatch, revertPatch } from "../api/client";

interface MigrationPatchModalProps {
  patch: string;
  projectId?: string;
  onClose: () => void;
}

export const MigrationPatchModal: React.FC<MigrationPatchModalProps> = ({
  patch,
  projectId,
  onClose,
}) => {
  const [copied, setCopied] = useState(false);
  const [applying, setApplying] = useState(false);
  const [reverting, setReverting] = useState(false);
  const [backupId, setBackupId] = useState<string | null>(null);
  const [resultMsg, setResultMsg] = useState<string | null>(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(patch);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleApply = async () => {
    if (!projectId) return;
    setApplying(true);
    setResultMsg(null);
    try {
      const res = await applyPatch(projectId, patch);
      setBackupId(res.backup_id);
      setResultMsg(`Applied successfully to: ${res.modified_files.join(", ")}`);
    } catch (err: any) {
      setResultMsg(err.message || "Failed to apply migration patch");
    } finally {
      setApplying(false);
    }
  };

  const handleRevert = async () => {
    if (!projectId || !backupId) return;
    setReverting(true);
    try {
      const res = await revertPatch(projectId, backupId);
      setBackupId(null);
      setResultMsg(`Reverted ${res.restored_files.length} file(s) back to original state.`);
    } catch (err: any) {
      setResultMsg(err.message || "Failed to revert patch");
    } finally {
      setReverting(false);
    }
  };

  const renderDiffLine = (line: string, index: number) => {
    let color = "#e2e8f0";
    let bg = "transparent";

    if (line.startsWith("---") || line.startsWith("+++")) {
      color = "var(--text-muted)";
    } else if (line.startsWith("@@")) {
      color = "var(--accent-cyan)";
      bg = "rgba(6, 182, 212, 0.1)";
    } else if (line.startsWith("-")) {
      color = "#fda4af";
      bg = "rgba(244, 63, 94, 0.15)";
    } else if (line.startsWith("+")) {
      color = "#86efac";
      bg = "rgba(16, 185, 129, 0.15)";
    }

    return (
      <div
        key={index}
        style={{
          color,
          backgroundColor: bg,
          padding: "0.1rem 0.5rem",
          whiteSpace: "pre",
          fontFamily: "var(--font-mono)",
        }}
      >
        {line}
      </div>
    );
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "1rem",
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: "100%",
          maxWidth: "850px",
          maxHeight: "85vh",
          display: "flex",
          flexDirection: "column",
          padding: "1.5rem",
          gap: "1rem",
          boxShadow: "0 20px 40px rgba(0, 0, 0, 0.6)",
          borderColor: "rgba(139, 92, 246, 0.4)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Sparkles style={{ width: "20px", height: "20px", color: "var(--accent-violet)" }} />
            <h3 style={{ fontSize: "1.1rem" }}>1-Click Migration Patch (.diff)</h3>
          </div>

          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              color: "var(--text-muted)",
              cursor: "pointer",
            }}
          >
            <X style={{ width: "20px", height: "20px" }} />
          </button>
        </div>

        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
          ChangeRadar generated this unified diff patch to migrate your frontend files. You can apply it directly to files with instant undo, or copy it for Git.
        </p>

        {/* Diff Viewer */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            background: "#050811",
            borderRadius: "0.5rem",
            border: "1px solid var(--border-light)",
            padding: "0.75rem",
            fontSize: "0.8rem",
          }}
        >
          {patch.split("\n").map(renderDiffLine)}
        </div>

        {/* Feedback message if applied */}
        {resultMsg && (
          <div
            style={{
              padding: "0.55rem 0.85rem",
              borderRadius: "0.4rem",
              background: backupId ? "rgba(16, 185, 129, 0.15)" : "rgba(6, 182, 212, 0.15)",
              border: backupId ? "1px solid rgba(16, 185, 129, 0.3)" : "1px solid rgba(6, 182, 212, 0.3)",
              color: backupId ? "#86efac" : "#7dd3fc",
              fontSize: "0.8rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <Check style={{ width: "15px", height: "15px" }} />
            <span>{resultMsg}</span>
          </div>
        )}

        {/* CLI command snippet & Copy action */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.8rem", color: "var(--text-muted)" }}>
            <Terminal style={{ width: "16px", height: "16px", color: "var(--accent-cyan)" }} />
            <span>Apply CLI: <code>git apply migration.patch</code></span>
          </div>

          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <button
              className="btn btn-secondary"
              onClick={handleCopy}
              style={{ padding: "0.55rem 0.9rem" }}
            >
              {copied ? (
                <>
                  <Check style={{ width: "16px", height: "16px" }} />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <Copy style={{ width: "16px", height: "16px" }} />
                  <span>Copy Patch</span>
                </>
              )}
            </button>

            {projectId && (
              !backupId ? (
                <button
                  className="btn btn-accent"
                  onClick={handleApply}
                  disabled={applying}
                  style={{ padding: "0.55rem 1rem" }}
                >
                  <Wand2 style={{ width: "16px", height: "16px" }} />
                  <span>{applying ? "Applying..." : "Apply Directly to Files"}</span>
                </button>
              ) : (
                <button
                  className="btn btn-danger"
                  onClick={handleRevert}
                  disabled={reverting}
                  style={{ padding: "0.55rem 1rem" }}
                >
                  <RotateCcw style={{ width: "16px", height: "16px" }} />
                  <span>{reverting ? "Reverting..." : "Undo / Revert Files"}</span>
                </button>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
