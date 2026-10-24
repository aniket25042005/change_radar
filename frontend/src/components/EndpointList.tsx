import React, { useState } from "react";
import { Search, Route, Database, ArrowRight, FileCode, Check, Copy } from "lucide-react";
import { EndpointInfo, PydanticSchemaInfo } from "../api/client";

interface EndpointListProps {
  endpoints: EndpointInfo[];
  schemas: PydanticSchemaInfo[];
  onSelectEndpointForChange: (ep: EndpointInfo) => void;
  onSelectFieldForChange: (model: string, field: string) => void;
}

export const EndpointList: React.FC<EndpointListProps> = ({
  endpoints,
  schemas,
  onSelectEndpointForChange,
  onSelectFieldForChange,
}) => {
  const [filter, setFilter] = useState("");
  const [activeTab, setActiveTab] = useState<"endpoints" | "schemas">("endpoints");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const filteredEndpoints = endpoints.filter(
    (e) =>
      e.path.toLowerCase().includes(filter.toLowerCase()) ||
      e.method.toLowerCase().includes(filter.toLowerCase()) ||
      (e.response_model && e.response_model.toLowerCase().includes(filter.toLowerCase()))
  );

  const filteredSchemas = schemas.filter(
    (s) =>
      s.name.toLowerCase().includes(filter.toLowerCase()) ||
      s.fields.some((f) => f.name.toLowerCase().includes(filter.toLowerCase()))
  );

  const getMethodBadgeClass = (method: string) => {
    switch (method.toUpperCase()) {
      case "GET":
        return "badge-get";
      case "POST":
        return "badge-post";
      case "PUT":
        return "badge-put";
      case "DELETE":
        return "badge-delete";
      case "PATCH":
        return "badge-patch";
      default:
        return "badge-get";
    }
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  return (
    <div className="glass-panel" style={{ padding: "1.25rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Tabs & Search */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem" }}>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            className={`btn ${activeTab === "endpoints" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setActiveTab("endpoints")}
            style={{ padding: "0.45rem 0.85rem", fontSize: "0.8rem" }}
          >
            <Route style={{ width: "15px", height: "15px" }} />
            <span>Routes ({endpoints.length})</span>
          </button>
          <button
            className={`btn ${activeTab === "schemas" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setActiveTab("schemas")}
            style={{ padding: "0.45rem 0.85rem", fontSize: "0.8rem" }}
          >
            <Database style={{ width: "15px", height: "15px" }} />
            <span>Schemas ({schemas.length})</span>
          </button>
        </div>

        <div style={{ position: "relative", minWidth: "200px" }}>
          <Search
            style={{
              position: "absolute",
              left: "0.6rem",
              top: "50%",
              transform: "translateY(-50%)",
              width: "14px",
              height: "14px",
              color: "var(--text-muted)",
            }}
          />
          <input
            type="text"
            placeholder="Search routes or models..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{ paddingLeft: "2rem", fontSize: "0.8rem", padding: "0.4rem 0.6rem 0.4rem 2rem" }}
          />
        </div>
      </div>

      {/* Routes View */}
      {activeTab === "endpoints" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem", maxHeight: "450px", overflowY: "auto" }}>
          {filteredEndpoints.length === 0 ? (
            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", textAlign: "center", padding: "1.5rem" }}>
              No matching endpoints found.
            </p>
          ) : (
            filteredEndpoints.map((ep) => (
              <div
                key={ep.id}
                style={{
                  padding: "0.85rem 1rem",
                  borderRadius: "0.5rem",
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-subtle)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: "0.75rem",
                  transition: "border-color 0.15s ease",
                }}
              >
                <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem", minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                    <span className={`badge-method ${getMethodBadgeClass(ep.method)}`}>{ep.method}</span>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.875rem", fontWeight: 600 }}>
                      {ep.path}
                    </span>
                    <button
                      onClick={() => handleCopy(ep.path, ep.id)}
                      title="Copy path"
                      style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", display: "flex" }}
                    >
                      {copiedId === ep.id ? (
                        <Check style={{ width: "13px", height: "13px", color: "var(--accent-emerald)" }} />
                      ) : (
                        <Copy style={{ width: "13px", height: "13px" }} />
                      )}
                    </button>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    <span style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                      <FileCode style={{ width: "13px", height: "13px" }} />
                      {ep.file_path}:{ep.line_number}
                    </span>
                    {ep.response_model && (
                      <span style={{ color: "var(--accent-cyan)", fontFamily: "var(--font-mono)" }}>
                        &rarr; {ep.response_model}
                      </span>
                    )}
                  </div>
                </div>

                <button
                  className="btn btn-secondary"
                  onClick={() => onSelectEndpointForChange(ep)}
                  style={{ fontSize: "0.75rem", padding: "0.4rem 0.65rem", flexShrink: 0 }}
                  title="Simulate API modification on this route"
                >
                  <span>Simulate</span>
                  <ArrowRight style={{ width: "12px", height: "12px" }} />
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {/* Schemas View */}
      {activeTab === "schemas" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem", maxHeight: "450px", overflowY: "auto" }}>
          {filteredSchemas.length === 0 ? (
            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", textAlign: "center", padding: "1.5rem" }}>
              No Pydantic schemas found.
            </p>
          ) : (
            filteredSchemas.map((schema) => (
              <div
                key={schema.name}
                style={{
                  padding: "0.85rem 1rem",
                  borderRadius: "0.5rem",
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-subtle)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span style={{ fontWeight: 600, color: "var(--accent-violet)", fontFamily: "var(--font-mono)", fontSize: "0.9rem" }}>
                      class {schema.name}
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      ({schema.file_path}:{schema.line_number})
                    </span>
                  </div>
                </div>

                {/* Field Tags */}
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                  {schema.fields.map((field) => (
                    <button
                      key={field.name}
                      onClick={() => onSelectFieldForChange(schema.name, field.name)}
                      title={`Click to simulate change on '${field.name}'`}
                      style={{
                        background: "rgba(30, 41, 59, 0.8)",
                        border: "1px solid var(--border-light)",
                        borderRadius: "0.35rem",
                        padding: "0.25rem 0.55rem",
                        fontSize: "0.75rem",
                        fontFamily: "var(--font-mono)",
                        color: "var(--text-primary)",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.35rem",
                        transition: "all 0.15s ease",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--accent-cyan)")}
                      onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border-light)")}
                    >
                      <span>{field.name}</span>
                      <span style={{ color: "var(--text-muted)", fontSize: "0.7rem" }}>: {field.type_annotation}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
