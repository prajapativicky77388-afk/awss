"use client";

import { useMemo } from "react";
import type { AlertData } from "@/hooks/useTelemetry";

interface AlertFeedProps {
  alerts: AlertData[];
}

export default function AlertFeed({ alerts }: AlertFeedProps) {
  const sortedAlerts = useMemo(() => {
    return alerts.slice(0, 30);
  }, [alerts]);

  return (
    <div className="alerts-section glass-sm">
      <div className="alerts-title">
        🔔 Live Alert Feed
        {sortedAlerts.length > 0 && (
          <span className="alert-count">{sortedAlerts.length}</span>
        )}
      </div>

      {sortedAlerts.length === 0 ? (
        <div
          style={{
            color: "var(--text-dim)",
            fontSize: 13,
            textAlign: "center",
            padding: 24,
          }}
        >
          No active alerts — system nominal
        </div>
      ) : (
        <div className="alert-feed">
          {sortedAlerts.map((alert, i) => (
            <div
              key={`${alert.id}-${i}`}
              className={`alert-item ${alert.severity}`}
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <div className="alert-agent">{alert.agent}</div>
              <div className="alert-title-text">{alert.title}</div>
              <div className="alert-desc">{alert.description}</div>
              <div className="alert-time">
                {new Date(alert.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
