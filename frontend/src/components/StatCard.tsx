"use client";

interface StatCardProps {
  label: string;
  value: string | number;
  suffix?: string;
  icon: string;
  change?: { value: string; positive: boolean };
  pulse?: boolean;
}

export default function StatCard({ label, value, suffix, icon, change, pulse }: StatCardProps) {
  return (
    <div
      className="stat-card glass animate-slide-in-up"
      style={pulse ? { animation: "pulse-danger 2s infinite" } : {}}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div className="stat-label">{label}</div>
          <div className="stat-value">
            {value}
            {suffix && (
              <span style={{ fontSize: 16, opacity: 0.7, marginLeft: 4 }}>{suffix}</span>
            )}
          </div>
          {change && (
            <div className={`stat-change ${change.positive ? "positive" : "negative"}`}>
              {change.positive ? "▲" : "▼"} {change.value}
            </div>
          )}
        </div>
        <div
          style={{
            fontSize: 32,
            opacity: 0.3,
            lineHeight: 1,
          }}
        >
          {icon}
        </div>
      </div>
    </div>
  );
}
