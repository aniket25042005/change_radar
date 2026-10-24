import React, { useState, useEffect } from "react";
import {
  Bot,
  Network,
  Send,
  Sparkles,
  Check,
  Copy,
  Clock,
  Code2,
  ChevronRight,
  ShieldAlert,
  Terminal,
  Activity,
  Layers,
} from "lucide-react";
import {
  AgentGraphSpecResponse,
  AgentQueryResponse,
  fetchAgentGraphSpec,
  fetchOllamaStatus,
  OllamaStatusResponse,
  queryAgentCopilot,
} from "../api/client";

interface LangGraphWorkspaceProps {
  projectId: string;
  contextReportId?: string;
  changeType?: string;
  fieldName?: string;
  onClose?: () => void;
}

export const LangGraphWorkspace: React.FC<LangGraphWorkspaceProps> = ({
  projectId,
  contextReportId,
  changeType,
  fieldName,
  onClose,
}) => {
  const [graphSpec, setGraphSpec] = useState<AgentGraphSpecResponse | null>(null);
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatusResponse | null>(null);
  const [queryInput, setQueryInput] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [conversation, setConversation] = useState<AgentQueryResponse[]>([]);
  const [activeTraceNode, setActiveTraceNode] = useState<string | null>(null);
  const [copiedCodeIdx, setCopiedCodeIdx] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load LangGraph specification & Ollama status on mount
  useEffect(() => {
    fetchAgentGraphSpec(projectId)
      .then(setGraphSpec)
      .catch(() => {});

    fetchOllamaStatus()
      .then(setOllamaStatus)
      .catch(() => {});
  }, [projectId]);

  const quickPrompts = [
    { label: "Zero-Downtime Deprecation", text: "How do I safely deprecate without breaking clients?" },
    { label: "Generate Dual-Read Adapter", text: "Generate backwards-compatible wrapper in TypeScript and Pydantic" },
    { label: "Write Verification Tests", text: "Write test specifications for the affected files" },
    { label: "Draft Senior PR Review", text: "Draft senior staff PR review comment with approval gates" },
  ];

  const handleSendQuery = async (queryText?: string) => {
    const textToSend = (queryText || queryInput).trim();
    if (!textToSend || loading) return;

    setLoading(true);
    setErrorMsg(null);
    setQueryInput("");

    try {
      const resp = await queryAgentCopilot(projectId, {
        query: textToSend,
        context_report_id: contextReportId,
        change_type: changeType,
        field_name: fieldName,
      });
      setConversation((prev) => [...prev, resp]);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to query LangGraph copilot.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCode = (code: string, idx: number) => {
    navigator.clipboard.writeText(code);
    setCopiedCodeIdx(idx);
    setTimeout(() => setCopiedCodeIdx(null), 2000);
  };

  return (
    <div
      className="glass-panel"
      style={{
        padding: "1.25rem",
        background: "linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.95))",
        border: "1px solid rgba(6, 182, 212, 0.35)",
        boxShadow: "0 10px 30px rgba(0, 0, 0, 0.4)",
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              background: "linear-gradient(135deg, rgba(6, 182, 212, 0.25), rgba(139, 92, 246, 0.25))",
              border: "1px solid rgba(6, 182, 212, 0.4)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Bot style={{ width: "20px", height: "20px", color: "var(--accent-cyan)" }} />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 700 }}>LangGraph Agentic Copilot Studio</h3>
              <span
                style={{
                  fontSize: "0.7rem",
                  fontWeight: 600,
                  padding: "0.15rem 0.5rem",
                  borderRadius: "9999px",
                  background: "rgba(6, 182, 212, 0.2)",
                  color: "#38bdf8",
                  border: "1px solid rgba(6, 182, 212, 0.4)",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.25rem",
                }}
              >
                <Network style={{ width: "12px", height: "12px" }} />
                <span>STATEGRAPH 1.2</span>
              </span>

              {/* Local Ollama Status Chip */}
              {ollamaStatus?.online ? (
                <span
                  style={{
                    fontSize: "0.7rem",
                    fontWeight: 600,
                    padding: "0.15rem 0.5rem",
                    borderRadius: "9999px",
                    background: "rgba(16, 185, 129, 0.2)",
                    color: "#34d399",
                    border: "1px solid rgba(16, 185, 129, 0.4)",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.25rem",
                  }}
                  title={`Ollama active at ${ollamaStatus.base_url} with ${ollamaStatus.available_models.length} models`}
                >
                  <span>🦙 Ollama Online ({ollamaStatus.default_model})</span>
                </span>
              ) : (
                <span
                  style={{
                    fontSize: "0.7rem",
                    fontWeight: 500,
                    padding: "0.15rem 0.5rem",
                    borderRadius: "9999px",
                    background: "rgba(148, 163, 184, 0.12)",
                    color: "#94a3b8",
                    border: "1px solid rgba(148, 163, 184, 0.25)",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.25rem",
                  }}
                  title="Run 'ollama serve' or 'ollama run llama3.2' to activate local neural inference"
                >
                  <span>🦙 Ollama: Offline (Deterministic AST Active)</span>
                </span>
              )}
            </div>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Multi-Node Autonomous Agent Graph with Conditional Routing & Grounded AST Reasoning
            </p>
          </div>
        </div>

        {onClose && (
          <button
            className="btn btn-secondary"
            onClick={onClose}
            style={{ padding: "0.3rem 0.7rem", fontSize: "0.8rem" }}
          >
            Close Studio
          </button>
        )}
      </div>

      {/* Visual StateGraph Pipeline Diagram */}
      <div
        style={{
          padding: "0.85rem 1rem",
          borderRadius: "0.5rem",
          background: "rgba(10, 15, 30, 0.75)",
          border: "1px solid var(--border-subtle)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.8rem", color: "var(--text-muted)" }}>
            <Activity style={{ width: "14px", height: "14px", color: "var(--accent-cyan)" }} />
            <span style={{ fontWeight: 600 }}>Active StateGraph Topology (6 Nodes):</span>
          </div>
          <span style={{ fontSize: "0.7rem", color: "#94a3b8" }}>
            Conditional Router: `START` &rarr; (Interactive vs Full Analysis)
          </span>
        </div>

        {/* Nodes flow layout */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            overflowX: "auto",
            paddingBottom: "0.4rem",
          }}
        >
          <div
            style={{
              padding: "0.35rem 0.65rem",
              borderRadius: "0.4rem",
              background: "rgba(148, 163, 184, 0.15)",
              border: "1px solid rgba(148, 163, 184, 0.3)",
              fontSize: "0.75rem",
              fontWeight: 600,
              color: "#cbd5e1",
            }}
          >
            START
          </div>
          <ChevronRight style={{ width: "14px", height: "14px", color: "var(--text-muted)" }} />

          {(graphSpec?.nodes || [
            { id: "assess_architectural_risk", label: "Risk & SemVer Assessor", node_type: "evaluator", description: "Evaluates SemVer impact" },
            { id: "synthesize_migration_guide", label: "Migration Synthesizer", node_type: "generator", description: "Synthesizes migration steps" },
            { id: "synthesize_compatibility_code", label: "Code Synthesizer", node_type: "coder", description: "Generates adapters" },
            { id: "draft_pr_review_comment", label: "Senior PR Reviewer", node_type: "critic", description: "Drafts PR review" },
            { id: "determine_autonomous_next_steps", label: "Flight Control", node_type: "planner", description: "Plans flight path" },
          ]).map((node) => {
            const isActive = activeTraceNode === node.id || loading;
            return (
              <React.Fragment key={node.id}>
                <div
                  style={{
                    padding: "0.35rem 0.65rem",
                    borderRadius: "0.4rem",
                    background: isActive ? "rgba(6, 182, 212, 0.25)" : "rgba(30, 41, 59, 0.7)",
                    border: isActive ? "1px solid var(--accent-cyan)" : "1px solid var(--border-light)",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: isActive ? "#38bdf8" : "#e2e8f0",
                    whiteSpace: "nowrap",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.35rem",
                    transition: "all 0.2s ease",
                  }}
                  title={node.description || node.label}
                >
                  <Layers style={{ width: "12px", height: "12px" }} />
                  <span>{node.label}</span>
                </div>
                <ChevronRight style={{ width: "14px", height: "14px", color: "var(--text-muted)" }} />
              </React.Fragment>
            );
          })}

          <div
            style={{
              padding: "0.35rem 0.65rem",
              borderRadius: "0.4rem",
              background: "rgba(16, 185, 129, 0.15)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              fontSize: "0.75rem",
              fontWeight: 600,
              color: "#34d399",
            }}
          >
            END
          </div>
        </div>
      </div>

      {/* Quick Prompt Chips */}
      <div>
        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: "0.4rem" }}>
          Suggested LangGraph Agent Inquiries:
        </span>
        <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
          {quickPrompts.map((p, idx) => (
            <button
              key={idx}
              type="button"
              className="btn btn-secondary"
              onClick={() => handleSendQuery(p.text)}
              disabled={loading}
              style={{
                padding: "0.3rem 0.65rem",
                fontSize: "0.75rem",
                background: "rgba(30, 41, 59, 0.6)",
                borderColor: "rgba(6, 182, 212, 0.25)",
              }}
            >
              <Sparkles style={{ width: "12px", height: "12px", color: "var(--accent-cyan)" }} />
              <span>{p.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Conversation Stream */}
      {conversation.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem", maxHeight: "400px", overflowY: "auto", paddingRight: "0.25rem" }}>
          {conversation.map((item, idx) => (
            <div
              key={idx}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
                padding: "1rem",
                borderRadius: "0.5rem",
                background: "rgba(15, 23, 42, 0.8)",
                border: "1px solid var(--border-light)",
              }}
            >
              {/* Query bubble */}
              <div style={{ display: "flex", alignItems: "center", gap: "0.45rem", color: "var(--accent-cyan)", fontSize: "0.85rem", fontWeight: 600 }}>
                <Terminal style={{ width: "15px", height: "15px" }} />
                <span>Developer: "{item.query}"</span>
              </div>

              {/* Answer content */}
              <div
                style={{
                  fontSize: "0.85rem",
                  lineHeight: 1.6,
                  color: "#e2e8f0",
                  whiteSpace: "pre-line",
                }}
              >
                {item.answer}
              </div>

              {/* Synthesized Compatibility Code */}
              {item.compatibility_code && (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", marginTop: "0.25rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "0.3rem" }}>
                      <Code2 style={{ width: "14px", height: "14px", color: "var(--accent-cyan)" }} />
                      <span>Synthesized Compatibility Adapter:</span>
                    </span>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => handleCopyCode(item.compatibility_code!, idx)}
                      style={{ padding: "0.2rem 0.55rem", fontSize: "0.7rem" }}
                    >
                      {copiedCodeIdx === idx ? (
                        <>
                          <Check style={{ width: "12px", height: "12px", color: "var(--accent-emerald)" }} />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy style={{ width: "12px", height: "12px" }} />
                          <span>Copy Code</span>
                        </>
                      )}
                    </button>
                  </div>
                  <pre
                    style={{
                      padding: "0.75rem 0.85rem",
                      borderRadius: "0.4rem",
                      background: "rgba(10, 15, 30, 0.85)",
                      border: "1px solid var(--border-subtle)",
                      fontSize: "0.75rem",
                      color: "#93c5fd",
                      whiteSpace: "pre-wrap",
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    <code>{item.compatibility_code}</code>
                  </pre>
                </div>
              )}

              {/* Node Execution Trace */}
              {item.trace && item.trace.length > 0 && (
                <div style={{ marginTop: "0.4rem", padding: "0.6rem 0.75rem", borderRadius: "0.4rem", background: "rgba(30, 41, 59, 0.4)", border: "1px solid var(--border-subtle)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginBottom: "0.4rem", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    <Clock style={{ width: "12px", height: "12px", color: "var(--accent-emerald)" }} />
                    <span style={{ fontWeight: 600 }}>LangGraph Execution Trace:</span>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.3rem" }}>
                    {item.trace.map((t, tIdx) => (
                      <div
                        key={tIdx}
                        onMouseEnter={() => setActiveTraceNode(t.node_name)}
                        onMouseLeave={() => setActiveTraceNode(null)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          fontSize: "0.7rem",
                          color: "#cbd5e1",
                          padding: "0.2rem 0.4rem",
                          borderRadius: "0.25rem",
                          background: activeTraceNode === t.node_name ? "rgba(6, 182, 212, 0.15)" : "transparent",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                          <span style={{ color: "var(--accent-cyan)", fontWeight: 600 }}>✓ {t.label}:</span>
                          <span>{t.summary}</span>
                        </div>
                        <span style={{ color: "#34d399", fontWeight: 600, fontFamily: "var(--font-mono)" }}>
                          {t.duration_ms}ms
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Follow-up Chips */}
              {item.suggested_followups && item.suggested_followups.length > 0 && (
                <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", marginTop: "0.25rem" }}>
                  <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", alignSelf: "center" }}>Follow-up:</span>
                  {item.suggested_followups.map((fText, fIdx) => (
                    <button
                      key={fIdx}
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => handleSendQuery(fText)}
                      disabled={loading}
                      style={{ padding: "0.2rem 0.5rem", fontSize: "0.7rem" }}
                    >
                      <span>{fText}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Error alert if any */}
      {errorMsg && (
        <div
          style={{
            padding: "0.6rem 0.85rem",
            borderRadius: "0.4rem",
            background: "rgba(239, 68, 68, 0.15)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            color: "#fca5a5",
            fontSize: "0.8rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
          }}
        >
          <ShieldAlert style={{ width: "15px", height: "15px" }} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Query Input Box */}
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
        <input
          type="text"
          value={queryInput}
          onChange={(e) => setQueryInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleSendQuery();
            }
          }}
          placeholder="Ask LangGraph Copilot (e.g. 'How do I add Sunset headers in FastAPI?', 'Generate Jest mock')..."
          disabled={loading}
          style={{
            flex: 1,
            padding: "0.65rem 0.9rem",
            fontSize: "0.85rem",
            background: "rgba(15, 23, 42, 0.75)",
            border: "1px solid rgba(6, 182, 212, 0.3)",
            borderRadius: "0.4rem",
            color: "#f8fafc",
          }}
        />
        <button
          className="btn btn-primary"
          onClick={() => handleSendQuery()}
          disabled={loading || !queryInput.trim()}
          style={{ padding: "0.65rem 1rem", fontSize: "0.85rem" }}
        >
          <Send style={{ width: "15px", height: "15px" }} />
          <span>{loading ? "Agent Reasoning..." : "Ask Agent"}</span>
        </button>
      </div>
    </div>
  );
};
