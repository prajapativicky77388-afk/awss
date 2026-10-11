"use client";

import type { AgentData } from "@/hooks/useTelemetry";

interface AgentPanelProps {
  agents: AgentData[];
  mode: string;
}

export default function AgentPanel({ agents, mode }: AgentPanelProps) {
  if (!agents.length) {
    return (
      <div className="glass-sm" style={{ padding: 16 }}>
        <div className="section-title">
          <span className="section-title-icon" />
          AI Agent Swarm
        </div>
        <div style={{ color: "var(--text-dim)", fontSize: 13, textAlign: "center", padding: 20 }}>
          Initializing agent swarm...
        </div>
      </div>
    );
  }

  return (
    <div className="glass-sm" style={{ padding: 16 }}>
      <div className="section-title">
        <span className="section-title-icon" />
        AI Agent Swarm
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {agents.map((agent, i) => (
          <div
            key={agent.name}
            className="agent-card glass-sm animate-slide-in-up"
            style={{ animationDelay: `${i * 0.1}s` }}
          >
            <div className="agent-header">
              <div className="agent-icon">{agent.icon}</div>
              <div style={{ flex: 1 }}>
                <div className="agent-name">{agent.name}</div>
                <span className={`agent-status-badge ${agent.status}`}>
                  {agent.status}
                </span>
              </div>
            </div>
            <div className="agent-metrics">
              <div className="agent-metric">
                <div className="agent-metric-label">Tasks</div>
                <div className="agent-metric-value">{agent.tasks_completed}</div>
              </div>
              <div className="agent-metric">
                <div className="agent-metric-label">Accuracy</div>
                <div className="agent-metric-value">{agent.accuracy_pct}%</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
