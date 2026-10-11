"use client";

import { useMemo } from "react";
import type { Weather } from "@/hooks/useTelemetry";

interface WeatherWidgetProps {
  weather: Weather | null;
  mode: string;
}

export default function WeatherWidget({ weather, mode }: WeatherWidgetProps) {
  if (!weather) {
    return (
      <div className="weather-widget glass-sm">
        <div className="section-title">
          <span className="section-title-icon" />
          Weather Telemetry
        </div>
        <div style={{ color: "var(--text-dim)", fontSize: 13, textAlign: "center", padding: 20 }}>
          Connecting to weather feed...
        </div>
      </div>
    );
  }

  const icon = useMemo(() => {
    if (mode === "monsoon") {
      if (weather.is_cloudburst) return "⛈️";
      if (weather.rainfall_mm_hr > 30) return "🌧️";
      if (weather.rainfall_mm_hr > 10) return "🌦️";
      return "☁️";
    } else {
      if (weather.is_heatwave) return "🔥";
      if (weather.temperature_c > 42) return "☀️";
      return "🌤️";
    }
  }, [weather, mode]);

  return (
    <div className="weather-widget glass-sm animate-fade-in">
      <div className="section-title">
        <span className="section-title-icon" />
        Weather Telemetry
      </div>

      <div className="weather-main">
        <div className="weather-icon">{icon}</div>
        <div>
          <div className="weather-temp">{weather.temperature_c}°</div>
          <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 2 }}>
            {mode === "monsoon" ? "Monsoon Active" : "Drought Season"}
          </div>
        </div>
      </div>

      <div className="weather-details">
        {mode === "monsoon" ? (
          <>
            <div className="weather-detail">
              <span className="weather-detail-label">Rainfall</span>
              <span className="weather-detail-value">{weather.rainfall_mm_hr} mm/hr</span>
            </div>
            <div className="weather-detail">
              <span className="weather-detail-label">Humidity</span>
              <span className="weather-detail-value">{weather.humidity_pct}%</span>
            </div>
            <div className="weather-detail">
              <span className="weather-detail-label">Wind</span>
              <span className="weather-detail-value">{weather.wind_speed_kmh} km/h</span>
            </div>
            <div className="weather-detail">
              <span className="weather-detail-label">Visibility</span>
              <span className="weather-detail-value">{weather.visibility_km} km</span>
            </div>
          </>
        ) : (
          <>
            <div className="weather-detail">
              <span className="weather-detail-label">UV Index</span>
              <span className="weather-detail-value">{weather.uv_index || "—"}</span>
            </div>
            <div className="weather-detail">
              <span className="weather-detail-label">Humidity</span>
              <span className="weather-detail-value">{weather.humidity_pct}%</span>
            </div>
            <div className="weather-detail">
              <span className="weather-detail-label">Wind</span>
              <span className="weather-detail-value">{weather.wind_speed_kmh} km/h</span>
            </div>
            <div className="weather-detail">
              <span className="weather-detail-label">Cloud Cover</span>
              <span className="weather-detail-value">{weather.cloud_cover_pct}%</span>
            </div>
          </>
        )}
      </div>

      {weather.is_cloudburst && (
        <div
          style={{
            marginTop: 12,
            padding: "8px 12px",
            background: "rgba(239, 68, 68, 0.15)",
            borderRadius: 8,
            fontSize: 12,
            fontWeight: 700,
            color: "#ef4444",
            display: "flex",
            alignItems: "center",
            gap: 6,
            animation: "pulse-danger 2s infinite",
          }}
        >
          ⚠️ CLOUDBURST ACTIVE — {weather.rainfall_mm_hr} mm/hr
        </div>
      )}

      {weather.is_heatwave && (
        <div
          style={{
            marginTop: 12,
            padding: "8px 12px",
            background: "rgba(239, 68, 68, 0.15)",
            borderRadius: 8,
            fontSize: 12,
            fontWeight: 700,
            color: "#ef4444",
            display: "flex",
            alignItems: "center",
            gap: 6,
            animation: "pulse-danger 2s infinite",
          }}
        >
          🔥 HEATWAVE — {weather.temperature_c}°C
        </div>
      )}
    </div>
  );
}
