"use client";

import { useEffect, useRef, useMemo } from "react";
import type { ZoneData, TankerData, PipeData } from "@/hooks/useTelemetry";

// We'll use dynamic imports for Leaflet to avoid SSR issues
let L: typeof import("leaflet") | null = null;

interface MapProps {
  zones: ZoneData[];
  pipes: PipeData[];
  tankers: TankerData[];
  mode: string;
  weather: { rainfall_mm_hr?: number; temperature_c?: number } | null;
}

export default function AquaMap({ zones, pipes, tankers, mode, weather }: MapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const zoneMarkersRef = useRef<L.CircleMarker[]>([]);
  const pipeLayersRef = useRef<L.Polyline[]>([]);
  const tankerMarkersRef = useRef<L.Marker[]>([]);
  const initRef = useRef(false);

  // Initialize map once
  useEffect(() => {
    if (initRef.current || !mapContainerRef.current) return;
    initRef.current = true;

    const initMap = async () => {
      const leaflet = await import("leaflet");
      L = leaflet;

      // Fix default icon path
      leaflet.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      const map = leaflet.map(mapContainerRef.current!, {
        center: [19.0760, 72.8777],
        zoom: 12,
        zoomControl: true,
        attributionControl: false,
      });

      // Dark tile layer
      leaflet.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 19,
      }).addTo(map);

      mapRef.current = map;
    };

    initMap();

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        initRef.current = false;
      }
    };
  }, []);

  // Update zone markers
  useEffect(() => {
    if (!mapRef.current || !L || !zones.length) return;

    // Remove old markers
    zoneMarkersRef.current.forEach((m) => m.remove());
    zoneMarkersRef.current = [];

    zones.forEach((zone) => {
      let color: string;
      let radius: number;
      let opacity: number;
      let pulseClass = "";

      if (mode === "monsoon") {
        const risk = zone.flood_risk_score || 0;
        if (risk > 0.7) {
          color = "#ef4444";
          radius = 18 + risk * 12;
          opacity = 0.8;
        } else if (risk > 0.4) {
          color = "#f59e0b";
          radius = 14 + risk * 8;
          opacity = 0.6;
        } else {
          color = "#3b82f6";
          radius = 10;
          opacity = 0.4;
        }
      } else {
        const deficit = zone.deficit_index || 0;
        if (deficit > 0.5) {
          color = "#ef4444";
          radius = 18 + deficit * 10;
          opacity = 0.8;
        } else if (deficit > 0.2) {
          color = "#f97316";
          radius = 14 + deficit * 8;
          opacity = 0.6;
        } else {
          color = "#10b981";
          radius = 10;
          opacity = 0.4;
        }
      }

      const marker = L!.circleMarker([zone.lat, zone.lng], {
        radius: radius,
        fillColor: color,
        fillOpacity: opacity,
        color: color,
        weight: 2,
        opacity: 0.9,
      }).addTo(mapRef.current!);

      // Popup content
      const popupContent = mode === "monsoon"
        ? `<div style="font-family: Inter, sans-serif; min-width: 200px;">
            <div style="font-weight: 700; font-size: 14px; margin-bottom: 8px;">${zone.zone_name}</div>
            <div style="display: grid; gap: 4px; font-size: 12px;">
              <div>🌊 Water Level: <strong>${zone.water_level_m?.toFixed(3)}m</strong></div>
              <div>⚠️ Flood Risk: <strong style="color: ${color}">${((zone.flood_risk_score || 0) * 100).toFixed(0)}%</strong></div>
              <div>🔄 Drain Flow: <strong>${zone.drain_flow_rate_lps?.toFixed(1)} L/s</strong></div>
              <div>💧 Drainage Capacity: <strong>${zone.drainage_capacity_pct?.toFixed(0)}%</strong></div>
              ${zone.is_waterlogged ? '<div style="color: #ef4444; font-weight: 700;">🚨 WATERLOGGED</div>' : ''}
              ${zone.pump_station_active ? '<div style="color: #3b82f6; font-weight: 600;">⚡ Pump Station Active</div>' : ''}
            </div>
          </div>`
        : `<div style="font-family: Inter, sans-serif; min-width: 200px;">
            <div style="font-weight: 700; font-size: 14px; margin-bottom: 8px;">${zone.zone_name}</div>
            <div style="display: grid; gap: 4px; font-size: 12px;">
              <div>💧 Groundwater: <strong>${zone.groundwater_level_m?.toFixed(1)}m</strong></div>
              <div>📊 Deficit Index: <strong style="color: ${color}">${((zone.deficit_index || 0) * 100).toFixed(0)}%</strong></div>
              <div>🏠 Demand: <strong>${zone.water_demand_kl?.toFixed(0)} kL</strong></div>
              <div>🔧 Pressure: <strong>${zone.supply_pressure_bar?.toFixed(2)} bar</strong></div>
              ${zone.is_critical ? '<div style="color: #ef4444; font-weight: 700;">🚨 CRITICAL SHORTAGE</div>' : ''}
              ${zone.tanker_requests_pending ? `<div style="color: #f59e0b;">🚛 ${zone.tanker_requests_pending} tankers requested</div>` : ''}
            </div>
          </div>`;

      marker.bindPopup(popupContent);
      zoneMarkersRef.current.push(marker);
    });
  }, [zones, mode]);

  // Update pipe lines
  useEffect(() => {
    if (!mapRef.current || !L || !pipes.length || !zones.length) return;

    pipeLayersRef.current.forEach((p) => p.remove());
    pipeLayersRef.current = [];

    const zoneMap = new Map(zones.map(z => [z.zone_id, z]));

    pipes.forEach((pipe) => {
      const fromZone = zoneMap.get(pipe.from_zone);
      const toZone = zoneMap.get(pipe.to_zone);
      if (!fromZone || !toZone) return;

      let color = "#334155";
      let weight = 2;
      let dashArray = "5, 10";

      if (pipe.anomaly_detected) {
        color = "#ef4444";
        weight = 4;
        dashArray = "8, 4";
      } else if (pipe.integrity_pct < 50) {
        color = "#f59e0b";
        weight = 3;
      } else {
        color = mode === "monsoon" ? "#1e40af" : "#92400e";
        weight = 2;
      }

      const polyline = L!.polyline(
        [[fromZone.lat, fromZone.lng], [toZone.lat, toZone.lng]],
        { color, weight, opacity: 0.6, dashArray }
      ).addTo(mapRef.current!);

      polyline.bindPopup(`
        <div style="font-family: Inter, sans-serif; min-width: 180px;">
          <div style="font-weight: 700; font-size: 13px; margin-bottom: 6px;">
            ${pipe.pipe_id} (${pipe.material})
          </div>
          <div style="font-size: 12px; display: grid; gap: 3px;">
            <div>📏 Diameter: ${pipe.diameter_mm}mm</div>
            <div>🕐 Age: ${pipe.age_years} years</div>
            <div>📊 Flow: ${pipe.flow_rate_lps} L/s</div>
            <div>⬇️ Pressure: ${pipe.pressure_bar} bar</div>
            <div>🛡️ Integrity: <strong style="color: ${pipe.integrity_pct > 70 ? '#10b981' : pipe.integrity_pct > 40 ? '#f59e0b' : '#ef4444'}">${pipe.integrity_pct}%</strong></div>
            ${pipe.anomaly_detected ? `<div style="color: #ef4444; font-weight: 700;">⚠️ ANOMALY - Loss: ${pipe.estimated_loss_lph} L/hr</div>` : ''}
          </div>
        </div>
      `);

      pipeLayersRef.current.push(polyline);
    });
  }, [pipes, zones, mode]);

  // Update tanker markers (drought mode)
  useEffect(() => {
    if (!mapRef.current || !L) return;

    tankerMarkersRef.current.forEach((m) => m.remove());
    tankerMarkersRef.current = [];

    if (mode !== "drought" || !tankers.length) return;

    tankers.forEach((tanker) => {
      const statusColors: Record<string, string> = {
        available: "#10b981",
        en_route: "#3b82f6",
        delivering: "#f59e0b",
        returning: "#8b5cf6",
      };

      const color = statusColors[tanker.status] || "#94a3b8";

      const icon = L!.divIcon({
        className: "",
        html: `<div style="
          width: 28px; height: 28px;
          background: ${color};
          border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          font-size: 14px;
          border: 2px solid white;
          box-shadow: 0 2px 8px rgba(0,0,0,0.4);
          transition: all 0.5s ease;
        ">🚛</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const marker = L!.marker([tanker.lat, tanker.lng], { icon }).addTo(mapRef.current!);

      marker.bindPopup(`
        <div style="font-family: Inter, sans-serif; min-width: 170px;">
          <div style="font-weight: 700; font-size: 13px; margin-bottom: 6px;">
            ${tanker.tanker_id}
          </div>
          <div style="font-size: 12px; display: grid; gap: 3px;">
            <div>📦 Capacity: ${(tanker.capacity_liters / 1000).toFixed(0)}kL</div>
            <div>💧 Fill: ${tanker.fill_level_pct.toFixed(0)}%</div>
            <div>📍 Status: <strong style="color: ${color}">${tanker.status.toUpperCase()}</strong></div>
            ${tanker.eta_minutes ? `<div>⏱️ ETA: ${tanker.eta_minutes.toFixed(0)} min</div>` : ''}
          </div>
        </div>
      `);

      tankerMarkersRef.current.push(marker);
    });
  }, [tankers, mode]);

  return (
    <div className="map-container glass" style={{ position: "relative" }}>
      {/* Map Overlay */}
      <div className="map-overlay">
        <div className="map-mode-badge">
          {mode === "monsoon" ? "🌧️" : "☀️"}
          <span>MODE: {mode.toUpperCase()}</span>
        </div>
        {weather && (
          <div className="glass-sm map-legend">
            {mode === "monsoon" ? (
              <>
                <div className="legend-item">
                  <div className="legend-dot" style={{ background: "#ef4444" }} />
                  <span>Critical Flood Risk (&gt;70%)</span>
                </div>
                <div className="legend-item">
                  <div className="legend-dot" style={{ background: "#f59e0b" }} />
                  <span>Warning (&gt;40%)</span>
                </div>
                <div className="legend-item">
                  <div className="legend-dot" style={{ background: "#3b82f6" }} />
                  <span>Normal</span>
                </div>
                <div className="legend-item" style={{ marginTop: 4 }}>
                  <div className="legend-dot" style={{ background: "#ef4444", borderRadius: 2, width: 16, height: 4 }} />
                  <span>Pipe Anomaly</span>
                </div>
              </>
            ) : (
              <>
                <div className="legend-item">
                  <div className="legend-dot" style={{ background: "#ef4444" }} />
                  <span>Critical Deficit (&gt;50%)</span>
                </div>
                <div className="legend-item">
                  <div className="legend-dot" style={{ background: "#f97316" }} />
                  <span>Warning (&gt;20%)</span>
                </div>
                <div className="legend-item">
                  <div className="legend-dot" style={{ background: "#10b981" }} />
                  <span>Adequate Supply</span>
                </div>
                <div className="legend-item">
                  <div className="legend-dot" style={{ background: "#3b82f6", borderRadius: "50%" }} />
                  <span>🚛 Water Tanker</span>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Leaflet Map Container */}
      <div ref={mapContainerRef} style={{ height: "100%", width: "100%", borderRadius: 16 }} />
    </div>
  );
}
