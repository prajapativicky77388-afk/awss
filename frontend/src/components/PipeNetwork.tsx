"use client";

import type { PipeData } from "@/hooks/useTelemetry";

interface PipeNetworkProps {
  pipes: PipeData[];
  mode: string;
}

export default function PipeNetwork({ pipes, mode }: PipeNetworkProps) {
  if (!pipes.length) return null;

  const getIntegrityColor = (pct: number) => {
    if (pct > 70) return "var(--success)";
    if (pct > 40) return "var(--warning)";
    return "var(--danger)";
  };

  return (
    <div className="pipe-section glass-sm">
      <div className="section-title">
        <span className="section-title-icon" />
        Pipe Network — Digital Twin
      </div>

      <div style={{ maxHeight: 280, overflowY: "auto" }}>
        {pipes.map((pipe) => (
          <div
            key={pipe.pipe_id}
            className={`pipe-item ${pipe.anomaly_detected ? "anomaly" : ""}`}
          >
            <div className="pipe-info">
              <span className="pipe-id">{pipe.pipe_id}</span>
              <span style={{ color: "var(--text-dim)", fontSize: 10 }}>
                {pipe.material} • {pipe.diameter_mm}mm
              </span>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 10, color: "var(--text-dim)" }}>
                  {pipe.pressure_bar} bar
                </div>
                {pipe.anomaly_detected && (
                  <div
                    style={{
                      fontSize: 9,
                      color: "var(--danger)",
                      fontWeight: 700,
                    }}
                  >
                    ⚠ LEAK: {pipe.estimated_loss_lph} L/hr
                  </div>
                )}
              </div>
              <div className="pipe-bar">
                <div
                  className="pipe-bar-fill"
                  style={{
                    width: `${pipe.integrity_pct}%`,
                    background: getIntegrityColor(pipe.integrity_pct),
                  }}
                />
              </div>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  color: getIntegrityColor(pipe.integrity_pct),
                  fontFamily: "'JetBrains Mono', monospace",
                  minWidth: 36,
                  textAlign: "right",
                }}
              >
                {pipe.integrity_pct}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
