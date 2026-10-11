"""
AquaMesh Synthetic Data Engine
Generates realistic IoT sensor streams for urban water infrastructure.
"""

import math
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np


# ─── City Configuration (Mumbai-like topology) ─────────────────────────────
CITY_ZONES = [
    {"id": "zone-01", "name": "Andheri West",      "lat": 19.1364, "lng": 72.8296, "elevation": 8,  "drainage_capacity": 0.7, "population_density": 0.85},
    {"id": "zone-02", "name": "Bandra East",        "lat": 19.0596, "lng": 72.8495, "elevation": 5,  "drainage_capacity": 0.5, "population_density": 0.9},
    {"id": "zone-03", "name": "Kurla",              "lat": 19.0726, "lng": 72.8845, "elevation": 3,  "drainage_capacity": 0.4, "population_density": 0.95},
    {"id": "zone-04", "name": "Dadar",              "lat": 19.0178, "lng": 72.8478, "elevation": 6,  "drainage_capacity": 0.6, "population_density": 0.88},
    {"id": "zone-05", "name": "Sion",               "lat": 19.0452, "lng": 72.8622, "elevation": 4,  "drainage_capacity": 0.45,"population_density": 0.82},
    {"id": "zone-06", "name": "Worli",              "lat": 19.0176, "lng": 72.8152, "elevation": 7,  "drainage_capacity": 0.65,"population_density": 0.75},
    {"id": "zone-07", "name": "Chembur",            "lat": 19.0522, "lng": 72.8966, "elevation": 12, "drainage_capacity": 0.8, "population_density": 0.7},
    {"id": "zone-08", "name": "Goregaon East",      "lat": 19.1663, "lng": 72.8526, "elevation": 10, "drainage_capacity": 0.55,"population_density": 0.78},
    {"id": "zone-09", "name": "Malad West",         "lat": 19.1874, "lng": 72.8484, "elevation": 9,  "drainage_capacity": 0.6, "population_density": 0.8},
    {"id": "zone-10", "name": "Borivali East",      "lat": 19.2307, "lng": 72.8567, "elevation": 15, "drainage_capacity": 0.75,"population_density": 0.65},
    {"id": "zone-11", "name": "Powai",              "lat": 19.1176, "lng": 72.9060, "elevation": 20, "drainage_capacity": 0.85,"population_density": 0.6},
    {"id": "zone-12", "name": "Mulund",             "lat": 19.1726, "lng": 72.9565, "elevation": 18, "drainage_capacity": 0.7, "population_density": 0.55},
]

# ─── Pipe Network ───────────────────────────────────────────────────────────
PIPE_SEGMENTS = [
    {"id": "pipe-001", "from_zone": "zone-01", "to_zone": "zone-02", "diameter_mm": 600, "age_years": 25, "material": "CI"},
    {"id": "pipe-002", "from_zone": "zone-02", "to_zone": "zone-03", "diameter_mm": 450, "age_years": 35, "material": "CI"},
    {"id": "pipe-003", "from_zone": "zone-03", "to_zone": "zone-05", "diameter_mm": 500, "age_years": 30, "material": "DI"},
    {"id": "pipe-004", "from_zone": "zone-04", "to_zone": "zone-06", "diameter_mm": 800, "age_years": 15, "material": "DI"},
    {"id": "pipe-005", "from_zone": "zone-05", "to_zone": "zone-04", "diameter_mm": 400, "age_years": 40, "material": "CI"},
    {"id": "pipe-006", "from_zone": "zone-06", "to_zone": "zone-01", "diameter_mm": 700, "age_years": 20, "material": "HDPE"},
    {"id": "pipe-007", "from_zone": "zone-07", "to_zone": "zone-03", "diameter_mm": 550, "age_years": 28, "material": "CI"},
    {"id": "pipe-008", "from_zone": "zone-08", "to_zone": "zone-09", "diameter_mm": 600, "age_years": 22, "material": "DI"},
    {"id": "pipe-009", "from_zone": "zone-09", "to_zone": "zone-10", "diameter_mm": 500, "age_years": 18, "material": "HDPE"},
    {"id": "pipe-010", "from_zone": "zone-10", "to_zone": "zone-12", "diameter_mm": 450, "age_years": 32, "material": "CI"},
    {"id": "pipe-011", "from_zone": "zone-11", "to_zone": "zone-07", "diameter_mm": 650, "age_years": 12, "material": "DI"},
    {"id": "pipe-012", "from_zone": "zone-12", "to_zone": "zone-11", "diameter_mm": 550, "age_years": 25, "material": "CI"},
]

# ─── Tanker Fleet ───────────────────────────────────────────────────────────
TANKERS = [
    {"id": "TK-001", "capacity_liters": 10000, "base_zone": "zone-01", "status": "available"},
    {"id": "TK-002", "capacity_liters": 15000, "base_zone": "zone-04", "status": "available"},
    {"id": "TK-003", "capacity_liters": 10000, "base_zone": "zone-07", "status": "available"},
    {"id": "TK-004", "capacity_liters": 20000, "base_zone": "zone-10", "status": "available"},
    {"id": "TK-005", "capacity_liters": 12000, "base_zone": "zone-08", "status": "available"},
    {"id": "TK-006", "capacity_liters": 10000, "base_zone": "zone-03", "status": "available"},
    {"id": "TK-007", "capacity_liters": 18000, "base_zone": "zone-11", "status": "en_route"},
    {"id": "TK-008", "capacity_liters": 10000, "base_zone": "zone-06", "status": "available"},
]


class SimulationClock:
    """Manages a virtual clock that can be accelerated."""
    def __init__(self, speed_factor: float = 60.0):
        self.start_real = time.time()
        self.start_virtual = datetime.now()
        self.speed_factor = speed_factor

    def now(self) -> datetime:
        elapsed = time.time() - self.start_real
        return self.start_virtual + timedelta(seconds=elapsed * self.speed_factor)


class WeatherEngine:
    """Generates realistic weather patterns with seasonal variation."""

    def __init__(self):
        self._rain_event_active = False
        self._rain_intensity = 0.0
        self._rain_start = None
        self._base_temp = 32.0

    def generate(self, sim_time: datetime, mode: str) -> Dict:
        hour = sim_time.hour
        month = sim_time.month

        if mode == "monsoon":
            return self._monsoon_weather(sim_time, hour)
        else:
            return self._drought_weather(sim_time, hour)

    def _monsoon_weather(self, sim_time: datetime, hour: int) -> Dict:
        # Simulate realistic monsoon rainfall bursts
        t = sim_time.timestamp()
        
        # Multi-frequency rain pattern
        rain_base = max(0, 20 * math.sin(t / 3600) + 15 * math.sin(t / 1800) + 10 * math.sin(t / 600))
        
        # Random cloudburst events
        if random.random() < 0.005:
            self._rain_event_active = True
            self._rain_intensity = random.uniform(60, 120)  # mm/hr
            self._rain_start = t
        
        if self._rain_event_active:
            elapsed = t - self._rain_start
            if elapsed > random.uniform(1800, 7200):
                self._rain_event_active = False
                self._rain_intensity *= 0.85
            rain = self._rain_intensity * math.exp(-elapsed / 5000) + rain_base * 0.3
        else:
            rain = max(0, rain_base + random.gauss(0, 5))

        # Temperature inversely correlates with rain
        temp = 26 + 4 * math.sin(hour * math.pi / 12) - rain * 0.05 + random.gauss(0, 0.5)
        humidity = min(99, 75 + rain * 0.3 + random.gauss(0, 3))
        wind_speed = 8 + rain * 0.15 + random.gauss(0, 2)

        return {
            "timestamp": sim_time.isoformat(),
            "rainfall_mm_hr": round(max(0, rain), 1),
            "temperature_c": round(temp, 1),
            "humidity_pct": round(min(100, max(40, humidity)), 1),
            "wind_speed_kmh": round(max(0, wind_speed), 1),
            "visibility_km": round(max(0.5, 10 - rain * 0.08), 1),
            "cloud_cover_pct": round(min(100, 60 + rain * 0.4), 0),
            "is_cloudburst": self._rain_event_active,
        }

    def _drought_weather(self, sim_time: datetime, hour: int) -> Dict:
        # Scorching heat with diurnal variation
        temp_base = 38 + 8 * math.sin((hour - 6) * math.pi / 12)
        temp = temp_base + random.gauss(0, 1.5)
        humidity = max(15, 35 - (temp - 38) * 2 + random.gauss(0, 3))

        return {
            "timestamp": sim_time.isoformat(),
            "rainfall_mm_hr": 0.0,
            "temperature_c": round(temp, 1),
            "humidity_pct": round(humidity, 1),
            "wind_speed_kmh": round(max(0, 12 + random.gauss(0, 4)), 1),
            "visibility_km": round(max(2, 8 + random.gauss(0, 1)), 1),
            "cloud_cover_pct": round(max(0, 15 + random.gauss(0, 8)), 0),
            "uv_index": round(max(1, 9 + 3 * math.sin((hour - 6) * math.pi / 12) + random.gauss(0, 0.5)), 1),
            "is_heatwave": temp > 44,
        }


class SensorEngine:
    """Generates sensor data for all city zones."""

    def __init__(self):
        self._zone_states: Dict[str, Dict] = {}
        self._pipe_states: Dict[str, Dict] = {}
        self._anomaly_active: Dict[str, bool] = {}
        self._initialize_states()

    def _initialize_states(self):
        for zone in CITY_ZONES:
            self._zone_states[zone["id"]] = {
                "water_level_m": 0.0,
                "drain_flow_rate": 0.0,
                "groundwater_level_m": random.uniform(8, 15),
                "water_demand_kl": zone["population_density"] * random.uniform(800, 1200),
                "supply_pressure_bar": random.uniform(1.5, 3.0),
            }
        for pipe in PIPE_SEGMENTS:
            self._pipe_states[pipe["id"]] = {
                "flow_rate_lps": random.uniform(20, 80),
                "pressure_bar": random.uniform(1.5, 3.5),
                "leak_probability": 0.0,
                "integrity_pct": max(30, 100 - pipe["age_years"] * 1.5 + random.gauss(0, 5)),
            }
            self._anomaly_active[pipe["id"]] = False

    def generate_zone_sensors(self, zone: Dict, weather: Dict, mode: str, dt: float) -> Dict:
        zid = zone["id"]
        state = self._zone_states[zid]
        rain = weather.get("rainfall_mm_hr", 0)
        temp = weather.get("temperature_c", 30)

        if mode == "monsoon":
            return self._monsoon_zone(zone, state, rain, temp, dt)
        else:
            return self._drought_zone(zone, state, temp, dt)

    def _monsoon_zone(self, zone: Dict, state: Dict, rain: float, temp: float, dt: float) -> Dict:
        # Water level rises with rain, drains based on capacity
        inflow = rain * 0.001 * (1 - zone["elevation"] / 30)  # lower elevation = more accumulation
        drainage = state["water_level_m"] * zone["drainage_capacity"] * 0.1
        
        # Update water level
        state["water_level_m"] = max(0, state["water_level_m"] + (inflow - drainage) * dt)
        
        # Drain flow rate
        state["drain_flow_rate"] = min(100, rain * zone["drainage_capacity"] * 1.5 + random.gauss(0, 2))
        
        # Risk score based on water level and drainage capacity
        flood_risk = min(1.0, state["water_level_m"] / (zone["drainage_capacity"] * 2))

        return {
            "zone_id": zone["id"],
            "zone_name": zone["name"],
            "lat": zone["lat"],
            "lng": zone["lng"],
            "water_level_m": round(state["water_level_m"], 3),
            "drain_flow_rate_lps": round(max(0, state["drain_flow_rate"]), 1),
            "flood_risk_score": round(flood_risk, 3),
            "is_waterlogged": state["water_level_m"] > 0.3,
            "predicted_peak_hours": round(max(0, 3 - flood_risk * 3), 1) if flood_risk > 0.3 else None,
            "drainage_capacity_pct": round(zone["drainage_capacity"] * 100 * (1 - flood_risk * 0.5), 1),
            "pump_station_active": flood_risk > 0.6,
        }

    def _drought_zone(self, zone: Dict, state: Dict, temp: float, dt: float) -> Dict:
        # Groundwater depletes, demand increases with temperature
        heat_factor = max(1, (temp - 35) / 5)
        demand = state["water_demand_kl"] * heat_factor * (1 + random.gauss(0, 0.05))
        
        # Groundwater depletion
        depletion_rate = 0.002 * heat_factor * zone["population_density"]
        state["groundwater_level_m"] = max(2, state["groundwater_level_m"] - depletion_rate * dt)
        
        # Supply pressure drops with demand
        state["supply_pressure_bar"] = max(0.3, state["supply_pressure_bar"] - 0.001 * heat_factor * dt + random.gauss(0, 0.01))
        
        # Deficit calculation
        supply_capacity = state["supply_pressure_bar"] * 500  # simplified
        deficit = max(0, demand - supply_capacity)
        deficit_index = min(1.0, deficit / (demand + 1))

        return {
            "zone_id": zone["id"],
            "zone_name": zone["name"],
            "lat": zone["lat"],
            "lng": zone["lng"],
            "groundwater_level_m": round(state["groundwater_level_m"], 2),
            "water_demand_kl": round(demand, 0),
            "supply_pressure_bar": round(state["supply_pressure_bar"], 2),
            "deficit_index": round(deficit_index, 3),
            "deficit_kl": round(deficit, 0),
            "is_critical": deficit_index > 0.5,
            "tanker_requests_pending": max(0, int(deficit / 500)) if deficit_index > 0.3 else 0,
            "temperature_stress": temp > 42,
        }

    def generate_pipe_sensors(self, pipe: Dict, weather: Dict, mode: str, dt: float) -> Dict:
        pid = pipe["id"]
        state = self._pipe_states[pid]
        temp = weather.get("temperature_c", 30)

        # Pipe stress from heat (expansion) or pressure (rain surge)
        if mode == "monsoon":
            rain = weather.get("rainfall_mm_hr", 0)
            state["flow_rate_lps"] = max(0, pipe["diameter_mm"] * 0.1 * (1 + rain * 0.02) + random.gauss(0, 3))
            state["pressure_bar"] += rain * 0.005 * dt - 0.01 * dt
        else:
            heat_stress = max(0, (temp - 40) * 0.05)
            state["pressure_bar"] = max(0.5, state["pressure_bar"] - heat_stress * 0.01 * dt + random.gauss(0, 0.02))

        # Random anomaly injection
        age_risk = pipe["age_years"] / 50
        if random.random() < age_risk * 0.002 and not self._anomaly_active[pid]:
            self._anomaly_active[pid] = True
            state["leak_probability"] = random.uniform(0.5, 0.95)
            state["pressure_bar"] *= 0.6  # Sudden pressure drop

        # Leak detection signal
        if self._anomaly_active[pid]:
            state["integrity_pct"] = max(10, state["integrity_pct"] - 0.5 * dt)
            if random.random() < 0.01:
                self._anomaly_active[pid] = False
                state["leak_probability"] *= 0.5

        state["pressure_bar"] = max(0.2, min(5.0, state["pressure_bar"]))

        return {
            "pipe_id": pipe["id"],
            "from_zone": pipe["from_zone"],
            "to_zone": pipe["to_zone"],
            "diameter_mm": pipe["diameter_mm"],
            "age_years": pipe["age_years"],
            "material": pipe["material"],
            "flow_rate_lps": round(state["flow_rate_lps"], 1),
            "pressure_bar": round(state["pressure_bar"], 2),
            "leak_probability": round(state["leak_probability"], 3),
            "integrity_pct": round(state["integrity_pct"], 1),
            "anomaly_detected": self._anomaly_active[pid],
            "estimated_loss_lph": round(state["leak_probability"] * state["flow_rate_lps"] * 36, 0) if self._anomaly_active[pid] else 0,
        }


class TankerEngine:
    """Simulates tanker fleet movements and allocations."""

    def __init__(self):
        self._tanker_states = {}
        for t in TANKERS:
            zone = next(z for z in CITY_ZONES if z["id"] == t["base_zone"])
            self._tanker_states[t["id"]] = {
                "lat": zone["lat"] + random.gauss(0, 0.005),
                "lng": zone["lng"] + random.gauss(0, 0.005),
                "fill_level_pct": random.uniform(60, 100),
                "status": t["status"],
                "destination_zone": None,
                "eta_minutes": None,
            }

    def update(self, zone_data: List[Dict], dt: float) -> List[Dict]:
        # Find zones with highest deficit
        critical_zones = sorted(
            [z for z in zone_data if z.get("deficit_index", 0) > 0.3],
            key=lambda x: x.get("deficit_index", 0),
            reverse=True,
        )

        results = []
        for tanker in TANKERS:
            tid = tanker["id"]
            state = self._tanker_states[tid]

            # Dispatch available tankers to critical zones
            if state["status"] == "available" and critical_zones:
                target = critical_zones.pop(0)
                state["status"] = "en_route"
                state["destination_zone"] = target["zone_id"]
                state["eta_minutes"] = random.uniform(15, 45)

            # Simulate movement
            if state["status"] == "en_route" and state["destination_zone"]:
                target_zone = next((z for z in CITY_ZONES if z["id"] == state["destination_zone"]), None)
                if target_zone:
                    state["lat"] += (target_zone["lat"] - state["lat"]) * 0.05 * dt
                    state["lng"] += (target_zone["lng"] - state["lng"]) * 0.05 * dt
                    state["fill_level_pct"] = max(5, state["fill_level_pct"] - 0.3 * dt)
                    if state["eta_minutes"]:
                        state["eta_minutes"] = max(0, state["eta_minutes"] - dt * 0.5)
                        if state["eta_minutes"] <= 0:
                            state["status"] = "delivering"
                            state["eta_minutes"] = None

            # Delivering -> return cycle
            if state["status"] == "delivering":
                state["fill_level_pct"] = max(0, state["fill_level_pct"] - 2 * dt)
                if state["fill_level_pct"] <= 5:
                    state["status"] = "returning"
                    base_zone = next(z for z in CITY_ZONES if z["id"] == tanker["base_zone"])
                    state["destination_zone"] = tanker["base_zone"]

            if state["status"] == "returning":
                base_zone = next(z for z in CITY_ZONES if z["id"] == tanker["base_zone"])
                state["lat"] += (base_zone["lat"] - state["lat"]) * 0.08 * dt
                state["lng"] += (base_zone["lng"] - state["lng"]) * 0.08 * dt
                dist = abs(state["lat"] - base_zone["lat"]) + abs(state["lng"] - base_zone["lng"])
                if dist < 0.002:
                    state["status"] = "available"
                    state["fill_level_pct"] = 100
                    state["destination_zone"] = None

            results.append({
                "tanker_id": tid,
                "capacity_liters": tanker["capacity_liters"],
                "lat": round(state["lat"], 6),
                "lng": round(state["lng"], 6),
                "fill_level_pct": round(state["fill_level_pct"], 1),
                "status": state["status"],
                "destination_zone": state["destination_zone"],
                "eta_minutes": round(state["eta_minutes"], 1) if state["eta_minutes"] else None,
            })

        return results


class AgentEngine:
    """Multi-agent decision engine for AquaMesh."""

    def __init__(self):
        self._alerts: List[Dict] = []
        self._work_orders: List[Dict] = []
        self._reroute_suggestions: List[Dict] = []
        self._alert_counter = 0

    def _make_alert(self, severity: str, agent: str, title: str, description: str, zone_id: Optional[str] = None, pipe_id: Optional[str] = None) -> Dict:
        self._alert_counter += 1
        return {
            "id": f"ALT-{self._alert_counter:04d}",
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "agent": agent,
            "title": title,
            "description": description,
            "zone_id": zone_id,
            "pipe_id": pipe_id,
            "acknowledged": False,
        }

    def analyze_monsoon(self, zone_data: List[Dict], pipe_data: List[Dict], weather: Dict) -> Dict:
        alerts = []
        reroutes = []

        for zone in zone_data:
            if zone.get("flood_risk_score", 0) > 0.7:
                alerts.append(self._make_alert(
                    "critical", "Monsoon Agent",
                    f"FLOOD WARNING: {zone['zone_name']}",
                    f"Water level at {zone['water_level_m']:.2f}m. Predicted peak in {zone.get('predicted_peak_hours', 'N/A')}h. Activating pump stations.",
                    zone_id=zone["zone_id"],
                ))
                reroutes.append({
                    "zone_id": zone["zone_id"],
                    "zone_name": zone["zone_name"],
                    "action": "REROUTE_TRAFFIC",
                    "alternative_routes": [f"Via {CITY_ZONES[(i+2) % len(CITY_ZONES)]['name']}" for i in range(2)],
                    "estimated_delay_min": random.randint(15, 45),
                })
            elif zone.get("flood_risk_score", 0) > 0.4:
                alerts.append(self._make_alert(
                    "warning", "Monsoon Agent",
                    f"Waterlogging Risk: {zone['zone_name']}",
                    f"Drainage at {zone.get('drainage_capacity_pct', 0):.0f}% capacity. Monitoring closely.",
                    zone_id=zone["zone_id"],
                ))

        if weather.get("is_cloudburst"):
            alerts.append(self._make_alert(
                "critical", "Monsoon Agent",
                "CLOUDBURST DETECTED",
                f"Rainfall intensity: {weather['rainfall_mm_hr']}mm/hr. All drainage systems on high alert.",
            ))

        # Pipe anomalies
        for pipe in pipe_data:
            if pipe.get("anomaly_detected"):
                alerts.append(self._make_alert(
                    "critical", "Infrastructure Agent",
                    f"PIPE ANOMALY: {pipe['pipe_id']}",
                    f"Pressure drop to {pipe['pressure_bar']} bar. Leak probability: {pipe['leak_probability']*100:.0f}%. Auto-isolating zone.",
                    pipe_id=pipe["pipe_id"],
                ))

        return {"alerts": alerts, "reroutes": reroutes}

    def analyze_drought(self, zone_data: List[Dict], pipe_data: List[Dict], weather: Dict, tanker_data: List[Dict]) -> Dict:
        alerts = []
        allocations = []

        for zone in zone_data:
            if zone.get("is_critical"):
                alerts.append(self._make_alert(
                    "critical", "Drought Agent",
                    f"WATER CRISIS: {zone['zone_name']}",
                    f"Deficit index: {zone['deficit_index']:.2f}. Demand: {zone['water_demand_kl']:.0f}kL. Dispatching tankers.",
                    zone_id=zone["zone_id"],
                ))
                allocations.append({
                    "zone_id": zone["zone_id"],
                    "zone_name": zone["zone_name"],
                    "deficit_kl": zone.get("deficit_kl", 0),
                    "tankers_needed": zone.get("tanker_requests_pending", 0),
                    "priority": "HIGH" if zone["deficit_index"] > 0.7 else "MEDIUM",
                })
            elif zone.get("deficit_index", 0) > 0.2:
                alerts.append(self._make_alert(
                    "warning", "Drought Agent",
                    f"Supply Pressure Low: {zone['zone_name']}",
                    f"Pressure at {zone['supply_pressure_bar']} bar. Groundwater: {zone['groundwater_level_m']}m.",
                    zone_id=zone["zone_id"],
                ))

        if weather.get("is_heatwave"):
            alerts.append(self._make_alert(
                "critical", "Drought Agent",
                "HEATWAVE ALERT",
                f"Temperature: {weather['temperature_c']}°C. Water demand surge expected. Activating conservation protocols.",
            ))

        # Pipe anomalies in drought → burst risk
        for pipe in pipe_data:
            if pipe.get("anomaly_detected"):
                work_order = {
                    "id": f"WO-{random.randint(1000,9999)}",
                    "pipe_id": pipe["pipe_id"],
                    "type": "EMERGENCY_REPAIR",
                    "estimated_loss_lph": pipe.get("estimated_loss_lph", 0),
                    "isolation_zone": pipe["from_zone"],
                    "priority": "CRITICAL",
                    "auto_generated": True,
                    "status": "PENDING_DISPATCH",
                    "alternatives_simulated": 3,
                }
                self._work_orders.append(work_order)
                alerts.append(self._make_alert(
                    "critical", "Infrastructure Agent",
                    f"PIPE BURST RISK: {pipe['pipe_id']}",
                    f"Heat stress detected. Integrity at {pipe['integrity_pct']}%. Work order {work_order['id']} auto-generated.",
                    pipe_id=pipe["pipe_id"],
                ))

        return {"alerts": alerts, "allocations": allocations, "work_orders": self._work_orders[-5:]}

    def get_agent_status(self, mode: str) -> List[Dict]:
        """Returns status of all AI agents."""
        if mode == "monsoon":
            return [
                {"name": "Flood Prediction Agent", "status": "active", "icon": "🌊", "tasks_completed": random.randint(40, 120), "accuracy_pct": round(random.uniform(88, 96), 1)},
                {"name": "Traffic Rerouting Agent", "status": "active", "icon": "🚦", "tasks_completed": random.randint(10, 50), "accuracy_pct": round(random.uniform(90, 98), 1)},
                {"name": "Pump Station Controller", "status": "standby", "icon": "⚡", "tasks_completed": random.randint(5, 20), "accuracy_pct": round(random.uniform(92, 99), 1)},
                {"name": "Infrastructure Sentinel", "status": "active", "icon": "🔧", "tasks_completed": random.randint(15, 60), "accuracy_pct": round(random.uniform(85, 95), 1)},
            ]
        else:
            return [
                {"name": "Drought Analysis Agent", "status": "active", "icon": "☀️", "tasks_completed": random.randint(30, 100), "accuracy_pct": round(random.uniform(87, 95), 1)},
                {"name": "Tanker Dispatch Agent", "status": "active", "icon": "🚛", "tasks_completed": random.randint(20, 80), "accuracy_pct": round(random.uniform(89, 97), 1)},
                {"name": "Leak Detection Swarm", "status": "scanning", "icon": "🔍", "tasks_completed": random.randint(50, 200), "accuracy_pct": round(random.uniform(91, 98), 1)},
                {"name": "Infrastructure Sentinel", "status": "active", "icon": "🔧", "tasks_completed": random.randint(15, 60), "accuracy_pct": round(random.uniform(85, 95), 1)},
            ]
