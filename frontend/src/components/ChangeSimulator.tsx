import React, { useState, useEffect } from "react";
import { Play, GitPullRequest, Sliders } from "lucide-react";
import { AnalyzePayload, EndpointInfo, PydanticSchemaInfo } from "../api/client";

interface ChangeSimulatorProps {
  endpoints: EndpointInfo[];
  schemas: PydanticSchemaInfo[];
  onRunAnalysis: (payload: AnalyzePayload) => void;
  loading: boolean;
  prefillEndpoint?: EndpointInfo | null;
  prefillField?: { model: string; field: string } | null;
}

export const ChangeSimulator: React.FC<ChangeSimulatorProps> = ({
  endpoints,
  schemas,
  onRunAnalysis,
  loading,
  prefillEndpoint,
  prefillField,
}) => {
  const [mode, setMode] = useState<"structured" | "git_diff">("structured");
  const [changeType, setChangeType] = useState<AnalyzePayload["change_type"]>("remove_field");
  const [selectedEndpoint, setSelectedEndpoint] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [fieldName, setFieldName] = useState<string>("");
  const [newFieldName, setNewFieldName] = useState<string>("");
  const [newFieldType, setNewFieldType] = useState<string>("");
  const [newPath, setNewPath] = useState<string>("");
  const [newMethod, setNewMethod] = useState<string>("POST");
  const [gitDiffText, setGitDiffText] = useState<string>("");

  // Handle prefills from parent
  useEffect(() => {
    if (prefillEndpoint) {
      setMode("structured");
      setChangeType("change_route");
      setSelectedEndpoint(prefillEndpoint.id);
      setNewPath(prefillEndpoint.path + "/v2");
    }
  }, [prefillEndpoint]);

  useEffect(() => {
    if (prefillField) {
      setMode("structured");
      setChangeType("remove_field");
      setSelectedModel(prefillField.model);
      setFieldName(prefillField.field);
    }
  }, [prefillField]);

  // Set initial selections when data loads
  useEffect(() => {
    if (endpoints.length > 0 && !selectedEndpoint) {
      setSelectedEndpoint(endpoints[0].id);
    }
    if (schemas.length > 0 && !selectedModel) {
      setSelectedModel(schemas[0].name);
      if (schemas[0].fields.length > 0 && !fieldName) {
        setFieldName(schemas[0].fields[0].name);
      }
    }
  }, [endpoints, schemas]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === "git_diff") {
      onRunAnalysis({
        change_type: "git_diff",
        git_diff: gitDiffText,
      });
      return;
    }

    const payload: AnalyzePayload = {
      change_type: changeType,
      endpoint_id: selectedEndpoint,
      model_name: selectedModel,
      field_name: fieldName,
      new_field_name: newFieldName,
      new_field_type: newFieldType,
      new_path: newPath,
      new_method: newMethod,
    };
    onRunAnalysis(payload);
  };

  const handleInsertSampleDiff = () => {
    const sampleDiff = 
`--- a/backend/schemas/user.py
+++ b/backend/schemas/user.py
@@ -5,4 +5,3 @@ class UserResponse(BaseModel):
     id: int
     name: str
-    email: str
     role: str = "user"
`;
    setGitDiffText(sampleDiff);
  };

  return (
    <div className="glass-panel" style={{ padding: "1.25rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Mode Toggle Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Sliders style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
          <h3 style={{ fontSize: "1rem", fontWeight: 600 }}>API Change Simulator</h3>
        </div>

        <div style={{ display: "flex", gap: "0.25rem", background: "var(--bg-surface)", padding: "0.2rem", borderRadius: "0.5rem" }}>
          <button
            type="button"
            className={`btn ${mode === "structured" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setMode("structured")}
            style={{ padding: "0.3rem 0.6rem", fontSize: "0.75rem", border: "none" }}
          >
            <span>Configurator</span>
          </button>
          <button
            type="button"
            className={`btn ${mode === "git_diff" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setMode("git_diff")}
            style={{ padding: "0.3rem 0.6rem", fontSize: "0.75rem", border: "none" }}
          >
            <GitPullRequest style={{ width: "12px", height: "12px" }} />
            <span>Git Diff (PR)</span>
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {mode === "structured" ? (
          <>
            {/* Change Type Selector */}
            <div>
              <label>Proposed Change Type</label>
              <select
                value={changeType}
                onChange={(e) => setChangeType(e.target.value as any)}
              >
                <option value="remove_field">Remove Response Field</option>
                <option value="rename_field">Rename Response Field</option>
                <option value="change_field_type">Change Field Type</option>
                <option value="change_route">Change Route Path</option>
                <option value="change_http_method">Change HTTP Method</option>
              </select>
            </div>

            {/* Field-related inputs */}
            {(changeType === "remove_field" || changeType === "rename_field" || changeType === "change_field_type") && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                <div>
                  <label>Pydantic Schema</label>
                  <select
                    value={selectedModel}
                    onChange={(e) => {
                      setSelectedModel(e.target.value);
                      const s = schemas.find((x) => x.name === e.target.value);
                      if (s && s.fields.length > 0) setFieldName(s.fields[0].name);
                    }}
                  >
                    {schemas.map((s) => (
                      <option key={s.name} value={s.name}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label>Target Field Name</label>
                  <input
                    type="text"
                    value={fieldName}
                    onChange={(e) => setFieldName(e.target.value)}
                    placeholder="e.g. email, role, id"
                    required
                  />
                </div>
              </div>
            )}

            {/* Rename Field */}
            {changeType === "rename_field" && (
              <div>
                <label>New Field Name</label>
                <input
                  type="text"
                  value={newFieldName}
                  onChange={(e) => setNewFieldName(e.target.value)}
                  placeholder="e.g. contact_email, user_id"
                  required
                />
              </div>
            )}

            {/* Change Field Type */}
            {changeType === "change_field_type" && (
              <div>
                <label>New Type Annotation</label>
                <input
                  type="text"
                  value={newFieldType}
                  onChange={(e) => setNewFieldType(e.target.value)}
                  placeholder="e.g. List[str], Optional[int], bool"
                  required
                />
              </div>
            )}

            {/* Route-related inputs */}
            {(changeType === "change_route" || changeType === "change_http_method") && (
              <div>
                <label>Target FastAPI Endpoint</label>
                <select
                  value={selectedEndpoint}
                  onChange={(e) => setSelectedEndpoint(e.target.value)}
                >
                  {endpoints.map((ep) => (
                    <option key={ep.id} value={ep.id}>
                      {ep.method} {ep.path} ({ep.file_path})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {changeType === "change_route" && (
              <div>
                <label>New Route Path</label>
                <input
                  type="text"
                  value={newPath}
                  onChange={(e) => setNewPath(e.target.value)}
                  placeholder="e.g. /api/v2/users"
                  required
                />
              </div>
            )}

            {changeType === "change_http_method" && (
              <div>
                <label>New HTTP Method</label>
                <select
                  value={newMethod}
                  onChange={(e) => setNewMethod(e.target.value)}
                >
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="PATCH">PATCH</option>
                  <option value="DELETE">DELETE</option>
                </select>
              </div>
            )}
          </>
        ) : (
          /* Git Diff Mode */
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <label>Paste Unified Git Diff from Pull Request</label>
              <button
                type="button"
                onClick={handleInsertSampleDiff}
                style={{ background: "none", border: "none", color: "var(--accent-cyan)", fontSize: "0.75rem", cursor: "pointer" }}
              >
                + Insert Sample Diff
              </button>
            </div>
            <textarea
              rows={6}
              value={gitDiffText}
              onChange={(e) => setGitDiffText(e.target.value)}
              placeholder="Paste git diff here (e.g. diff --git a/backend/schemas/user.py ... - email: str)"
              style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem", resize: "vertical" }}
              required
            />
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading}
          style={{ width: "100%", padding: "0.65rem", marginTop: "0.25rem" }}
        >
          <Play style={{ width: "16px", height: "16px" }} />
          <span>{loading ? "Analyzing Cross-Stack Blast Radius..." : "Simulate Change & Generate Radar Report"}</span>
        </button>
      </form>
    </div>
  );
};
