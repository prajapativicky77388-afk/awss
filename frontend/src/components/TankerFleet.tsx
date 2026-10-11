"use client";

import type { TankerData } from "@/hooks/useTelemetry";

interface TankerFleetProps {
  tankers: TankerData[];
}

export default function TankerFleet({ tankers }: TankerFleetProps) {
  if (!tankers.length) return null;

  const statusLabel: Record<string, string> = {
    available: "Available",
    en_route: "En Route",
    delivering: "Delivering",
    returning: "Returning",
  };

  return (
    <div className="tanker-section glass-sm">
      <div className="section-title">
        <span className="section-title-icon" />
        Smart Tanker Fleet
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
        {["available", "en_route", "delivering", "returning"].map((status) => {
          const count = tankers.filter((t) => t.status === status).length;
          return (
            <div key={status} className={`tanker-status ${status}`}>
              {count} {statusLabel[status]}
            </div>
          );
        })}
      </div>

      <div style={{ maxHeight: 200, overflowY: "auto" }}>
        {tankers.map((tanker) => (
          <div key={tanker.tanker_id} className="tanker-item">
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 16 }}>🚛</span>
              <div>
                <div
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontWeight: 600,
                    fontSize: 12,
                  }}
                >
                  {tanker.tanker_id}
                </div>
                <div style={{ fontSize: 10, color: "var(--text-dim)" }}>
                  {(tanker.capacity_liters / 1000).toFixed(0)}kL •{" "}
                  {tanker.fill_level_pct.toFixed(0)}% full
                </div>
              </div>
            </div>

            <div style={{ textAlign: "right" }}>
              <span className={`tanker-status ${tanker.status}`}>
                {statusLabel[tanker.status] || tanker.status}
              </span>
              {tanker.eta_minutes && (
                <div
                  style={{
                    fontSize: 10,
                    color: "var(--primary)",
                    marginTop: 2,
                    fontFamily: "'JetBrains Mono', monospace",
                  }}
                >
                  ETA: {tanker.eta_minutes.toFixed(0)} min
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
