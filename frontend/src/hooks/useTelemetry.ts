// WebSocket hook for real-time telemetry
"use client";

import { useEffect, useRef, useState, useCallback } from "react";

export interface TelemetryData {
  type: string;
  timestamp: string;
  tick: number;
  mode: string;
  weather: Weather;
  zones: ZoneData[];
  pipes: PipeData[];
  tankers: TankerData[];
  agents: AgentData[];
  alerts: AlertData[];
  reroutes: RerouteData[];
  allocations: AllocationData[];
  work_orders: WorkOrderData[];
}

export interface Weather {
  timestamp: string;
  rainfall_mm_hr: number;
  temperature_c: number;
  humidity_pct: number;
  wind_speed_kmh: number;
  visibility_km: number;
  cloud_cover_pct: number;
  is_cloudburst?: boolean;
  uv_index?: number;
  is_heatwave?: boolean;
}

export interface ZoneData {
  zone_id: string;
  zone_name: string;
  lat: number;
  lng: number;
  // Monsoon fields
  water_level_m?: number;
  drain_flow_rate_lps?: number;
  flood_risk_score?: number;
  is_waterlogged?: boolean;
  predicted_peak_hours?: number | null;
  drainage_capacity_pct?: number;
  pump_station_active?: boolean;
  // Drought fields
  groundwater_level_m?: number;
  water_demand_kl?: number;
  supply_pressure_bar?: number;
  deficit_index?: number;
  deficit_kl?: number;
  is_critical?: boolean;
  tanker_requests_pending?: number;
  temperature_stress?: boolean;
}

export interface PipeData {
  pipe_id: string;
  from_zone: string;
  to_zone: string;
  diameter_mm: number;
  age_years: number;
  material: string;
  flow_rate_lps: number;
  pressure_bar: number;
  leak_probability: number;
  integrity_pct: number;
  anomaly_detected: boolean;
  estimated_loss_lph: number;
}

export interface TankerData {
  tanker_id: string;
  capacity_liters: number;
  lat: number;
  lng: number;
  fill_level_pct: number;
  status: string;
  destination_zone: string | null;
  eta_minutes: number | null;
}

export interface AgentData {
  name: string;
  status: string;
  icon: string;
  tasks_completed: number;
  accuracy_pct: number;
}

export interface AlertData {
  id: string;
  timestamp: string;
  severity: string;
  agent: string;
  title: string;
  description: string;
  zone_id?: string;
  pipe_id?: string;
  acknowledged: boolean;
}

export interface RerouteData {
  zone_id: string;
  zone_name: string;
  action: string;
  alternative_routes: string[];
  estimated_delay_min: number;
}

export interface AllocationData {
  zone_id: string;
  zone_name: string;
  deficit_kl: number;
  tankers_needed: number;
  priority: string;
}

export interface WorkOrderData {
  id: string;
  pipe_id: string;
  type: string;
  estimated_loss_lph: number;
  isolation_zone: string;
  priority: string;
  auto_generated: boolean;
  status: string;
  alternatives_simulated: number;
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/telemetry";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useTelemetry() {
  const [data, setData] = useState<TelemetryData | null>(null);
  const [connected, setConnected] = useState(false);
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      setConnected(true);
      console.log("[AquaMesh] WebSocket connected");
    };

    ws.onmessage = (event) => {
      try {
        const payload: TelemetryData = JSON.parse(event.data);
        setData(payload);

        if (payload.alerts && payload.alerts.length > 0) {
          setAlerts((prev) => {
            const newAlerts = [...payload.alerts, ...prev].slice(0, 100);
            return newAlerts;
          });
        }
      } catch (e) {
        console.error("[AquaMesh] Parse error:", e);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log("[AquaMesh] WebSocket disconnected, reconnecting...");
      reconnectRef.current = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
    };
  }, [connect]);

  const switchMode = useCallback(async (mode: string) => {
    try {
      await fetch(`${API_URL}/api/mode`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode }),
      });
    } catch (e) {
      console.error("[AquaMesh] Mode switch error:", e);
    }
  }, []);

  return { data, connected, alerts, switchMode };
}
