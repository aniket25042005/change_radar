import React, { useState, useRef } from "react";
import { UploadCloud, FileArchive, CheckCircle2, AlertCircle, Sparkles } from "lucide-react";
import { uploadProject } from "../api/client";

interface UploadPanelProps {
  onUploadSuccess: (proj: any) => void;
  onLoadSample: () => void;
  loadingSample: boolean;
}

export const UploadPanel: React.FC<UploadPanelProps> = ({
  onUploadSuccess,
  onLoadSample,
  loadingSample,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".zip")) {
      setErrorMsg("Please select a valid .zip archive file.");
      return;
    }
    setErrorMsg(null);
    setUploading(true);
    try {
      const proj = await uploadProject(file);
      onUploadSuccess(proj);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to upload project ZIP");
    } finally {
      setUploading(false);
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Upload Box */}
      <div
        className="glass-panel"
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        style={{
          padding: "2.5rem 2rem",
          textAlign: "center",
          borderStyle: "dashed",
          borderWidth: "2px",
          borderColor: isDragging ? "var(--accent-cyan)" : "var(--border-light)",
          backgroundColor: isDragging ? "rgba(6, 182, 212, 0.05)" : "var(--bg-glass)",
          cursor: "pointer",
          transition: "all 0.2s ease",
        }}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: "none" }}
          accept=".zip"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFile(e.target.files[0]);
            }
          }}
        />

        <div
          style={{
            width: "56px",
            height: "56px",
            borderRadius: "50%",
            background: "rgba(6, 182, 212, 0.1)",
            border: "1px solid rgba(6, 182, 212, 0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 1rem",
            color: "var(--accent-cyan)",
          }}
        >
          <UploadCloud style={{ width: "28px", height: "28px" }} />
        </div>

        <h3 style={{ fontSize: "1.1rem", marginBottom: "0.4rem" }}>
          {uploading ? "Extracting & Scanning Project..." : "Upload Full-Stack Project ZIP"}
        </h3>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", maxWidth: "420px", margin: "0 auto 1.25rem" }}>
          Drag & drop your repository archive containing a FastAPI backend and React/TypeScript frontend.
        </p>

        <button
          className="btn btn-primary"
          onClick={(e) => {
            e.stopPropagation();
            fileInputRef.current?.click();
          }}
          disabled={uploading}
        >
          <FileArchive style={{ width: "16px", height: "16px" }} />
          <span>{uploading ? "Scanning Files..." : "Browse ZIP File"}</span>
        </button>

        <div
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "1.5rem",
            marginTop: "1.5rem",
            fontSize: "0.75rem",
            color: "var(--text-muted)",
          }}
        >
          <span>Max Size: 25 MB</span>
          <span>•</span>
          <span>Zero Code Execution</span>
          <span>•</span>
          <span>Auto-skips .env & node_modules</span>
        </div>
      </div>

      {errorMsg && (
        <div
          style={{
            padding: "0.75rem 1rem",
            borderRadius: "0.5rem",
            background: "rgba(244, 63, 94, 0.15)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            color: "#fda4af",
            fontSize: "0.85rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
          }}
        >
          <AlertCircle style={{ width: "18px", height: "18px", flexShrink: 0 }} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Or Load Demo Sample */}
      <div
        className="glass-panel"
        style={{
          padding: "1.25rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
          background: "linear-gradient(135deg, rgba(139, 92, 246, 0.08), rgba(6, 182, 212, 0.08))",
          borderColor: "rgba(139, 92, 246, 0.25)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
            <Sparkles style={{ width: "18px", height: "18px", color: "var(--accent-violet)" }} />
            <h4 style={{ fontSize: "0.95rem" }}>Don't have a ZIP on hand?</h4>
          </div>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
            Explore ChangeRadar instantly with the bundled FastAPI + React/TS store demo project.
          </p>
        </div>

        <button
          className="btn btn-accent"
          onClick={onLoadSample}
          disabled={loadingSample}
        >
          <CheckCircle2 style={{ width: "16px", height: "16px" }} />
          <span>{loadingSample ? "Provisioning..." : "Load Demo Sample (1-Click)"}</span>
        </button>
      </div>
    </div>
  );
};
