"""
AquaMesh Backend — FastAPI Server
Autonomous Urban Hydro-Sentinel & Micro-Grid
Team: Grey Coder
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from simulation import (
    CITY_ZONES, PIPE_SEGMENTS, TANKERS,
    SimulationClock, WeatherEngine, SensorEngine, TankerEngine, AgentEngine,
)

# ─── App Setup ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="AquaMesh API",
    description="Autonomous Urban Hydro-Sentinel & Micro-Grid — Backend API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Global Simulation State ───────────────────────────────────────────────
sim_clock = SimulationClock(speed_factor=30.0)
weather_engine = WeatherEngine()
sensor_engine = SensorEngine()
tanker_engine = TankerEngine()
agent_engine = AgentEngine()

current_mode = "monsoon"  # "monsoon" or "drought"
simulation_tick = 0
alert_history: List[Dict] = []
telemetry_history: List[Dict] = []


# ─── Models ─────────────────────────────────────────────────────────────────
class ModeSwitch(BaseModel):
    mode: str  # "monsoon" or "drought"

class TankerRequest(BaseModel):
    zone_id: str
    quantity_kl: float
    priority: str = "normal"

class AcknowledgeAlert(BaseModel):
    alert_id: str


# ─── REST Endpoints ─────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "name": "AquaMesh",
        "tagline": "Autonomous Urban Hydro-Sentinel & Micro-Grid",
        "team": "Grey Coder",
        "version": "1.0.0",
        "mode": current_mode,
        "uptime_ticks": simulation_tick,
    }


@app.get("/api/config")
async def get_config():
    """Returns city topology and infrastructure configuration."""
    return {
        "zones": CITY_ZONES,
        "pipes": PIPE_SEGMENTS,
        "tankers": TANKERS,
        "city_center": {"lat": 19.0760, "lng": 72.8777},
        "city_name": "Mumbai Metropolitan Region",
    }


@app.get("/api/mode")
async def get_mode():
    return {"mode": current_mode}


@app.post("/api/mode")
async def set_mode(body: ModeSwitch):
    global current_mode
    if body.mode not in ("monsoon", "drought"):
        return {"error": "Mode must be 'monsoon' or 'drought'"}
    current_mode = body.mode
    return {"mode": current_mode, "switched_at": datetime.now().isoformat()}


@app.get("/api/telemetry")
async def get_telemetry():
    """Returns current snapshot of all sensor data."""
    sim_time = sim_clock.now()
    weather = weather_engine.generate(sim_time, current_mode)

    zone_data = [
        sensor_engine.generate_zone_sensors(zone, weather, current_mode, 1.0)
        for zone in CITY_ZONES
    ]
    pipe_data = [
        sensor_engine.generate_pipe_sensors(pipe, weather, current_mode, 1.0)
        for pipe in PIPE_SEGMENTS
    ]
    tanker_data = tanker_engine.update(zone_data, 1.0) if current_mode == "drought" else []

    return {
        "timestamp": sim_time.isoformat(),
        "mode": current_mode,
        "weather": weather,
        "zones": zone_data,
        "pipes": pipe_data,
        "tankers": tanker_data,
        "tick": simulation_tick,
    }


@app.get("/api/agents")
async def get_agents():
    """Returns status of all AI agents."""
    return {
        "mode": current_mode,
        "agents": agent_engine.get_agent_status(current_mode),
    }


@app.get("/api/alerts")
async def get_alerts(limit: int = Query(default=50, le=200)):
    """Returns recent alerts."""
    return {"alerts": alert_history[-limit:]}


@app.get("/api/analytics")
async def get_analytics():
    """Returns aggregated analytics for dashboard."""
    sim_time = sim_clock.now()
    weather = weather_engine.generate(sim_time, current_mode)

    zone_data = [
        sensor_engine.generate_zone_sensors(zone, weather, current_mode, 0.1)
        for zone in CITY_ZONES
    ]

    if current_mode == "monsoon":
        flooded = sum(1 for z in zone_data if z.get("is_waterlogged"))
        avg_risk = sum(z.get("flood_risk_score", 0) for z in zone_data) / len(zone_data)
        return {
            "mode": "monsoon",
            "total_zones": len(zone_data),
            "zones_flooded": flooded,
            "zones_at_risk": sum(1 for z in zone_data if z.get("flood_risk_score", 0) > 0.3),
            "avg_flood_risk": round(avg_risk, 3),
            "rainfall_intensity": weather.get("rainfall_mm_hr", 0),
            "pump_stations_active": sum(1 for z in zone_data if z.get("pump_station_active")),
            "drainage_health_pct": round(100 - avg_risk * 100, 1),
        }
    else:
        critical = sum(1 for z in zone_data if z.get("is_critical"))
        total_deficit = sum(z.get("deficit_kl", 0) for z in zone_data)
        avg_gw = sum(z.get("groundwater_level_m", 0) for z in zone_data) / len(zone_data)
        return {
            "mode": "drought",
            "total_zones": len(zone_data),
            "zones_critical": critical,
            "total_deficit_kl": round(total_deficit, 0),
            "avg_groundwater_m": round(avg_gw, 2),
            "temperature": weather.get("temperature_c", 0),
            "tankers_active": sum(1 for t in TANKERS if t["status"] != "available"),
            "supply_health_pct": round(100 - (critical / len(zone_data)) * 100, 1),
        }


@app.post("/api/tanker/request")
async def request_tanker(req: TankerRequest):
    """Submit a water tanker request."""
    return {
        "status": "queued",
        "request_id": f"REQ-{int(time.time()) % 10000:04d}",
        "zone_id": req.zone_id,
        "quantity_kl": req.quantity_kl,
        "estimated_dispatch_min": 15,
    }


# ─── WebSocket for Real-Time Telemetry ─────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.active_connections.remove(d)


manager = ConnectionManager()


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Generate telemetry tick
            global simulation_tick
            simulation_tick += 1
            sim_time = sim_clock.now()
            weather = weather_engine.generate(sim_time, current_mode)

            zone_data = [
                sensor_engine.generate_zone_sensors(zone, weather, current_mode, 1.0)
                for zone in CITY_ZONES
            ]
            pipe_data = [
                sensor_engine.generate_pipe_sensors(pipe, weather, current_mode, 1.0)
                for pipe in PIPE_SEGMENTS
            ]
            tanker_data = tanker_engine.update(zone_data, 1.0) if current_mode == "drought" else []

            # Agent analysis
            if current_mode == "monsoon":
                agent_result = agent_engine.analyze_monsoon(zone_data, pipe_data, weather)
            else:
                agent_result = agent_engine.analyze_drought(zone_data, pipe_data, weather, tanker_data)

            # Store alerts
            new_alerts = agent_result.get("alerts", [])
            alert_history.extend(new_alerts)
            if len(alert_history) > 500:
                alert_history[:] = alert_history[-500:]

            payload = {
                "type": "telemetry",
                "timestamp": sim_time.isoformat(),
                "tick": simulation_tick,
                "mode": current_mode,
                "weather": weather,
                "zones": zone_data,
                "pipes": pipe_data,
                "tankers": tanker_data,
                "agents": agent_engine.get_agent_status(current_mode),
                "alerts": new_alerts,
                "reroutes": agent_result.get("reroutes", []),
                "allocations": agent_result.get("allocations", []),
                "work_orders": agent_result.get("work_orders", []),
            }

            await websocket.send_json(payload)
            await asyncio.sleep(2)  # Send updates every 2 seconds

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)


# ─── Startup ────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("  AquaMesh v1.0.0 — Autonomous Urban Hydro-Sentinel")
    print("  Team: Grey Coder")
    print("=" * 60)
    print(f"  Mode: {current_mode}")
    print(f"  Zones: {len(CITY_ZONES)}")
    print(f"  Pipe Segments: {len(PIPE_SEGMENTS)}")
    print(f"  Tankers: {len(TANKERS)}")
    print("=" * 60)
