"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import dynamic from "next/dynamic";
import { useTelemetry } from "@/hooks/useTelemetry";
import StatCard from "@/components/StatCard";
import WeatherWidget from "@/components/WeatherWidget";
import AgentPanel from "@/components/AgentPanel";
import AlertFeed from "@/components/AlertFeed";
import PipeNetwork from "@/components/PipeNetwork";
import TankerFleet from "@/components/TankerFleet";
import RainEffect from "@/components/RainEffect";
import "leaflet/dist/leaflet.css";

// Dynamic import for the map (no SSR)
const AquaMap = dynamic(() => import("@/components/AquaMap"), {
  ssr: false,
  loading: () => (
    <div
      className="glass"
      style={{
        minHeight: 500,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "var(--text-dim)",
        fontSize: 14,
      }}
    >
      <div style={{ textAlign: "center" }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>🗺️</div>
        <div>Initializing GIS Engine...</div>
      </div>
    </div>
  ),
});

export default function Dashboard() {
  const { data, connected, alerts, switchMode } = useTelemetry();
  const [mode, setMode] = useState<"monsoon" | "drought">("monsoon");
  const [tick, setTick] = useState(0);

  // Sync mode from server
  useEffect(() => {
    if (data?.mode) {
      setMode(data.mode as "monsoon" | "drought");
    }
    if (data?.tick) {
      setTick(data.tick);
    }
  }, [data?.mode, data?.tick]);

  // Handle mode switch
  const handleModeSwitch = useCallback(
    (newMode: "monsoon" | "drought") => {
      setMode(newMode);
      switchMode(newMode);
    },
    [switchMode]
  );

  // Compute stats
  const stats = useMemo(() => {
    if (!data) return null;

    if (mode === "monsoon") {
      const flooded = data.zones.filter((z) => z.is_waterlogged).length;
      const atRisk = data.zones.filter((z) => (z.flood_risk_score || 0) > 0.3).length;
      const avgRisk = data.zones.reduce((a, z) => a + (z.flood_risk_score || 0), 0) / data.zones.length;
      const pumpsActive = data.zones.filter((z) => z.pump_station_active).length;

      return [
        {
          label: "Zones Flooded",
          value: flooded,
          suffix: `/ ${data.zones.length}`,
          icon: "🌊",
          pulse: flooded > 3,
          change: flooded > 0 ? { value: `${flooded} active`, positive: false } : undefined,
        },
        {
          label: "Flood Risk Index",
          value: (avgRisk * 100).toFixed(1),
          suffix: "%",
          icon: "⚠️",
          pulse: avgRisk > 0.6,
          change: avgRisk > 0.5 ? { value: "HIGH", positive: false } : { value: "NORMAL", positive: true },
        },
        {
          label: "Rainfall Intensity",
          value: data.weather.rainfall_mm_hr,
          suffix: "mm/hr",
          icon: "🌧️",
          pulse: data.weather.is_cloudburst,
        },
        {
          label: "Pump Stations",
          value: pumpsActive,
          suffix: "active",
          icon: "⚡",
          change: pumpsActive > 0 ? { value: `${pumpsActive} deployed`, positive: true } : undefined,
        },
      ];
    } else {
      const critical = data.zones.filter((z) => z.is_critical).length;
      const totalDeficit = data.zones.reduce((a, z) => a + (z.deficit_kl || 0), 0);
      const avgGW = data.zones.reduce((a, z) => a + (z.groundwater_level_m || 0), 0) / data.zones.length;
      const tankersActive = data.tankers.filter((t) => t.status !== "available").length;

      return [
        {
          label: "Critical Zones",
          value: critical,
          suffix: `/ ${data.zones.length}`,
          icon: "🔥",
          pulse: critical > 3,
          change: critical > 0 ? { value: `${critical} shortage`, positive: false } : undefined,
        },
        {
          label: "Water Deficit",
          value: Math.round(totalDeficit),
          suffix: "kL",
          icon: "💧",
          pulse: totalDeficit > 5000,
        },
        {
          label: "Groundwater Level",
          value: avgGW.toFixed(1),
          suffix: "m",
          icon: "📊",
          change: avgGW < 6 ? { value: "DEPLETING", positive: false } : { value: "Stable", positive: true },
        },
        {
          label: "Tankers Active",
          value: tankersActive,
          suffix: `/ ${data.tankers.length}`,
          icon: "🚛",
          change: tankersActive > 0 ? { value: `${tankersActive} dispatched`, positive: true } : undefined,
        },
      ];
    }
  }, [data, mode]);

  return (
    <div data-theme={mode === "drought" ? "drought" : undefined}>
      {/* Rain Effect */}
      {mode === "monsoon" && (
        <RainEffect
          intensity={data?.weather?.rainfall_mm_hr || 0}
          active={mode === "monsoon"}
        />
      )}

      {/* Heat shimmer for drought */}
      {mode === "drought" && <div className="heat-overlay" />}

      {/* Header */}
      <header className="header">
        <div className="header-inner">
          <div className="logo-section">
            <div className="logo-icon">💧</div>
            <div>
              <div className="logo-text">AquaMesh</div>
              <div className="logo-subtitle">Autonomous Urban Hydro-Sentinel</div>
            </div>
          </div>

          <div className="header-status">
            {/* Mode Toggle */}
            <div className="mode-toggle">
              <div
                className={`mode-toggle-slider ${mode === "drought" ? "drought" : ""}`}
              />
              <button
                className={`mode-toggle-btn ${mode === "monsoon" ? "active" : ""}`}
                onClick={() => handleModeSwitch("monsoon")}
              >
                🌧️ Monsoon
              </button>
              <button
                className={`mode-toggle-btn ${mode === "drought" ? "active" : ""}`}
                onClick={() => handleModeSwitch("drought")}
              >
                ☀️ Drought
              </button>
            </div>

            {/* Status badges */}
            <div className="status-badge">
              <span className={`status-dot ${connected ? "online" : "danger"}`} />
              {connected ? "LIVE" : "OFFLINE"}
            </div>

            <div className="status-badge">
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>
                TICK #{tick}
              </span>
            </div>

            <div className="status-badge" style={{ fontSize: 11 }}>
              Team: Grey Coder
            </div>
          </div>
        </div>
      </header>

      {/* Dashboard */}
      <main className="dashboard">
        {/* Stats Row */}
        <div className="stats-row">
          {stats
            ? stats.map((s, i) => <StatCard key={i} {...s} />)
            : Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="stat-card glass animate-fade-in">
                  <div className="stat-label">Loading...</div>
                  <div className="stat-value">—</div>
                </div>
              ))}
        </div>

        {/* Map */}
        <AquaMap
          zones={data?.zones || []}
          pipes={data?.pipes || []}
          tankers={data?.tankers || []}
          mode={mode}
          weather={data?.weather || null}
        />

        {/* Sidebar */}
        <div className="sidebar">
          <WeatherWidget weather={data?.weather || null} mode={mode} />
          <AgentPanel agents={data?.agents || []} mode={mode} />
          <PipeNetwork pipes={data?.pipes || []} mode={mode} />
          {mode === "drought" && <TankerFleet tankers={data?.tankers || []} />}
          <AlertFeed alerts={alerts} />
        </div>
      </main>

      {/* Connection Indicator */}
      <div className={`connection-indicator ${connected ? "connected" : "disconnected"}`}>
        <span
          className={`status-dot ${connected ? "online" : "danger"}`}
          style={{ animation: "none", width: 6, height: 6 }}
        />
        {connected ? "WebSocket Connected" : "Reconnecting..."}
      </div>
    </div>
  );
}
