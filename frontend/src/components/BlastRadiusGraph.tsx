import React, { useState } from "react";
import { Zap, Info, Layers, RefreshCw } from "lucide-react";
import { BlastRadiusGraphResponse, GraphNode } from "../api/client";

interface BlastRadiusGraphProps {
  graph: BlastRadiusGraphResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

export const BlastRadiusGraph: React.FC<BlastRadiusGraphProps> = ({
  graph,
  loading,
  onRefresh,
}) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: "2rem", textAlign: "center" }}>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
          No graph data available. Upload a project or load the demo sample to visualize the cross-stack blast radius.
        </p>
      </div>
    );
  }

  // Organize nodes by column layers for clean layout
  const layerOrder: Record<string, number> = {
    route: 0,
    schema: 1,
    type: 2,
    client: 2,
    component: 3,
    test: 4,
  };

  const columns: Record<number, GraphNode[]> = { 0: [], 1: [], 2: [], 3: [], 4: [] };
  graph.nodes.forEach((n) => {
    const layer = layerOrder[n.node_type] ?? 3;
    columns[layer].push(n);
  });

  const width = 860;
  const height = 360;
  const colX = [70, 240, 420, 600, 780];

  // Calculate node positions
  const nodePositions: Record<string, { x: number; y: number }> = {};
  Object.entries(columns).forEach(([layerStr, nodesInCol]) => {
    const l = Number(layerStr);
    const x = colX[l];
    const total = nodesInCol.length;
    const spacing = height / (total + 1);

    nodesInCol.forEach((node, idx) => {
      nodePositions[node.id] = {
        x,
        y: spacing * (idx + 1),
      };
    });
  });

  const getNodeColor = (node: GraphNode) => {
    const isAffected = graph.affected_node_ids.includes(node.id) || node.status === "breaking";
    if (isAffected) return { bg: "rgba(244, 63, 94, 0.2)", border: "#f43f5e", text: "#fda4af" };

    switch (node.node_type) {
      case "route":
        return { bg: "rgba(6, 182, 212, 0.15)", border: "rgba(6, 182, 212, 0.5)", text: "#38bdf8" };
      case "schema":
        return { bg: "rgba(139, 92, 246, 0.15)", border: "rgba(139, 92, 246, 0.5)", text: "#c084fc" };
      case "type":
        return { bg: "rgba(99, 102, 241, 0.15)", border: "rgba(99, 102, 241, 0.5)", text: "#a5b4fc" };
      case "client":
        return { bg: "rgba(16, 185, 129, 0.15)", border: "rgba(16, 185, 129, 0.5)", text: "#34d399" };
      case "component":
        return { bg: "rgba(14, 165, 233, 0.15)", border: "rgba(14, 165, 233, 0.5)", text: "#7dd3fc" };
      case "test":
        return { bg: "rgba(245, 158, 11, 0.15)", border: "rgba(245, 158, 11, 0.5)", text: "#fbbf24" };
      default:
        return { bg: "rgba(148, 163, 184, 0.15)", border: "rgba(148, 163, 184, 0.3)", text: "#cbd5e1" };
    }
  };

  return (
    <div className="glass-panel" style={{ padding: "1.25rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Title & Legend */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Layers style={{ width: "18px", height: "18px", color: "var(--accent-cyan)" }} />
          <h3 style={{ fontSize: "1rem", fontWeight: 600 }}>Interactive Blast Radius Graph</h3>
          {graph.affected_node_ids.length > 0 && (
            <span className="badge-risk badge-risk-breaking">
              <Zap style={{ width: "12px", height: "12px" }} />
              <span>{graph.affected_node_ids.length} Nodes in Blast Radius</span>
            </span>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <button
            onClick={onRefresh}
            className="btn btn-secondary"
            style={{ padding: "0.35rem 0.65rem", fontSize: "0.75rem" }}
            title="Refresh graph"
            disabled={loading}
          >
            <RefreshCw style={{ width: "12px", height: "12px", animation: loading ? "spin 1s linear infinite" : "none" }} />
            <span>Reset View</span>
          </button>
        </div>
      </div>

      {/* SVG Canvas */}
      <div
        style={{
          width: "100%",
          overflowX: "auto",
          background: "rgba(15, 23, 42, 0.6)",
          borderRadius: "0.5rem",
          border: "1px solid var(--border-subtle)",
          position: "relative",
        }}
      >
        <svg
          viewBox={`0 0 ${width} ${height}`}
          style={{ width: "100%", height: "360px", minWidth: "750px", display: "block" }}
        >
          <defs>
            <linearGradient id="edgeNormal" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="rgba(6, 182, 212, 0.3)" />
              <stop offset="100%" stopColor="rgba(139, 92, 246, 0.3)" />
            </linearGradient>
            <linearGradient id="edgeBreaking" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="rgba(244, 63, 94, 0.8)" />
              <stop offset="100%" stopColor="rgba(244, 63, 94, 0.4)" />
            </linearGradient>
          </defs>

          {/* Layer Labels */}
          <text x={colX[0]} y={24} fill="var(--text-muted)" fontSize="11" textAnchor="middle" fontWeight="600">
            FASTAPI ROUTES
          </text>
          <text x={colX[1]} y={24} fill="var(--text-muted)" fontSize="11" textAnchor="middle" fontWeight="600">
            SCHEMAS
          </text>
          <text x={colX[2]} y={24} fill="var(--text-muted)" fontSize="11" textAnchor="middle" fontWeight="600">
            TYPES & CLIENTS
          </text>
          <text x={colX[3]} y={24} fill="var(--text-muted)" fontSize="11" textAnchor="middle" fontWeight="600">
            COMPONENTS
          </text>
          <text x={colX[4]} y={24} fill="var(--text-muted)" fontSize="11" textAnchor="middle" fontWeight="600">
            TESTS
          </text>

          {/* Connecting Edges */}
          {graph.edges.map((edge) => {
            const p1 = nodePositions[edge.source];
            const p2 = nodePositions[edge.target];
            if (!p1 || !p2) return null;

            const isBreaking =
              graph.affected_node_ids.includes(edge.source) ||
              graph.affected_node_ids.includes(edge.target);

            const dx = p2.x - p1.x;
            const cx1 = p1.x + dx * 0.5;
            const cy1 = p1.y;
            const cx2 = p1.x + dx * 0.5;
            const cy2 = p2.y;

            const d = `M ${p1.x} ${p1.y} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${p2.x} ${p2.y}`;

            return (
              <path
                key={edge.id}
                d={d}
                fill="none"
                stroke={isBreaking ? "url(#edgeBreaking)" : "url(#edgeNormal)"}
                strokeWidth={isBreaking ? 2.5 : 1.2}
                strokeDasharray={isBreaking ? "none" : "none"}
                style={{
                  transition: "all 0.3s ease",
                  filter: isBreaking ? "drop-shadow(0 0 4px rgba(244, 63, 94, 0.6))" : "none",
                }}
              />
            );
          })}

          {/* Node Circles & Labels */}
          {graph.nodes.map((node) => {
            const pos = nodePositions[node.id];
            if (!pos) return null;

            const colors = getNodeColor(node);
            const isAffected = graph.affected_node_ids.includes(node.id) || node.status === "breaking";
            const isSelected = selectedNode?.id === node.id;

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={() => setSelectedNode(node)}
                style={{ cursor: "pointer" }}
                className={isAffected ? "pulse-affected" : ""}
              >
                {/* Glow ring if affected */}
                {isAffected && (
                  <circle
                    r={18}
                    fill="none"
                    stroke="#f43f5e"
                    strokeWidth="2"
                    opacity="0.6"
                  />
                )}

                {/* Main Node Body */}
                <circle
                  r={12}
                  fill={colors.bg}
                  stroke={isSelected ? "#ffffff" : colors.border}
                  strokeWidth={isSelected ? 3 : 1.8}
                />

                {/* Label text */}
                <text
                  y={22}
                  fill={colors.text}
                  fontSize="10"
                  fontFamily="var(--font-mono)"
                  textAnchor="middle"
                  fontWeight={isAffected ? "700" : "500"}
                  style={{ pointerEvents: "none" }}
                >
                  {node.label.length > 18 ? `${node.label.slice(0, 16)}…` : node.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div
          style={{
            padding: "0.75rem 1rem",
            borderRadius: "0.5rem",
            background: "var(--bg-surface)",
            border: "1px solid var(--border-light)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: "0.8rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <Info style={{ width: "16px", height: "16px", color: "var(--accent-cyan)" }} />
            <div>
              <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                {selectedNode.label}
              </span>
              <span style={{ color: "var(--text-muted)", marginLeft: "0.5rem" }}>
                ({selectedNode.node_type})
              </span>
              {selectedNode.details.file && (
                <span style={{ marginLeft: "0.75rem", fontFamily: "var(--font-mono)", color: "var(--accent-cyan)" }}>
                  {selectedNode.details.file}:{selectedNode.details.line}
                </span>
              )}
            </div>
          </div>

          <button
            onClick={() => setSelectedNode(null)}
            style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "0.85rem" }}
          >
            &times; Close
          </button>
        </div>
      )}
    </div>
  );
};
