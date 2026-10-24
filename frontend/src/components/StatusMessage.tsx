import React from "react";
import { AlertCircle, CheckCircle, Info } from "lucide-react";

interface StatusMessageProps {
  type: "error" | "success" | "info";
  message: string;
  onClose?: () => void;
}

export const StatusMessage: React.FC<StatusMessageProps> = ({
  type,
  message,
  onClose,
}) => {
  const getStyles = () => {
    switch (type) {
      case "error":
        return {
          bg: "rgba(244, 63, 94, 0.15)",
          border: "rgba(244, 63, 94, 0.3)",
          color: "#fda4af",
          icon: <AlertCircle style={{ width: "18px", height: "18px", flexShrink: 0 }} />,
        };
      case "success":
        return {
          bg: "rgba(16, 185, 129, 0.15)",
          border: "rgba(16, 185, 129, 0.3)",
          color: "#86efac",
          icon: <CheckCircle style={{ width: "18px", height: "18px", flexShrink: 0 }} />,
        };
      default:
        return {
          bg: "rgba(6, 182, 212, 0.15)",
          border: "rgba(6, 182, 212, 0.3)",
          color: "#7dd3fc",
          icon: <Info style={{ width: "18px", height: "18px", flexShrink: 0 }} />,
        };
    }
  };

  const s = getStyles();

  return (
    <div
      style={{
        padding: "0.75rem 1rem",
        borderRadius: "0.5rem",
        background: s.bg,
        border: `1px solid ${s.border}`,
        color: s.color,
        fontSize: "0.85rem",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "0.75rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        {s.icon}
        <span>{message}</span>
      </div>

      {onClose && (
        <button
          onClick={onClose}
          style={{ background: "none", border: "none", color: s.color, cursor: "pointer", fontSize: "1rem" }}
        >
          &times;
        </button>
      )}
    </div>
  );
};
