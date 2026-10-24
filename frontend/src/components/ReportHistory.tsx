import React from "react";
import { History, Clock, ArrowRight } from "lucide-react";
import { ImpactReport } from "../api/client";

interface ReportHistoryProps {
  reports: any[];
  onSelectReport: (report: ImpactReport) => void;
}

export const ReportHistory: React.FC<ReportHistoryProps> = ({
  reports,
  onSelectReport,
}) => {
  if (reports.length === 0) {
    return null;
  }

  return (
    <div className="glass-panel" style={{ padding: "1.25rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <History style={{ width: "16px", height: "16px", color: "var(--accent-cyan)" }} />
        <h4 style={{ fontSize: "0.95rem", fontWeight: 600 }}>Saved Report History ({reports.length})</h4>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: "250px", overflowY: "auto" }}>
        {reports.map((r) => {
          const reportData: ImpactReport = r.report_data;
          const formattedDate = new Date(r.created_at).toLocaleString();

          return (
            <div
              key={r.id}
              style={{
                padding: "0.6rem 0.8rem",
                borderRadius: "0.4rem",
                background: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "0.5rem",
              }}
            >
              <div>
                <div style={{ fontSize: "0.85rem", fontWeight: 500, color: "var(--text-primary)" }}>
                  {reportData.change_summary}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  <Clock style={{ width: "12px", height: "12px" }} />
                  <span>{formattedDate}</span>
                  <span>•</span>
                  <span style={{ color: reportData.risk_level === "Breaking" ? "#f43f5e" : "#06b6d4" }}>
                    {reportData.risk_level}
                  </span>
                </div>
              </div>

              <button
                className="btn btn-secondary"
                onClick={() => onSelectReport(reportData)}
                style={{ padding: "0.3rem 0.6rem", fontSize: "0.75rem" }}
              >
                <span>View</span>
                <ArrowRight style={{ width: "12px", height: "12px" }} />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
