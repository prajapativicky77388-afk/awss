# 🌊 AquaMesh — Autonomous Urban Hydro-Sentinel & Micro-Grid
### Team: Grey Coder

> *"Cities don't drown because of rain; they drown because their infrastructure is blind. And when the heatwaves hit, those same cities run dry because their water distribution is broken. Meet AquaMesh—the world's first autonomous multi-agent urban hydro-sentinel that dynamically defends cities against the extremes of monsoon floods and summer droughts."*

---

## 🏗 Architecture

```
[IoT Sensors / CCTV / Weather API]
               │
               ▼ (Live Telemetry Stream)
┌──────────────────────────────────────────────┐
│ FastAPI Backend & Spatial-Temporal Engine     │
└──────────────┬───────────────────────────────┘
               │
               ▼ (State & Context Query)
┌──────────────────────────────────────────────┐
│ Multi-Agent Swarm                            │
│  ├── Flood Prediction & Routing Agent        │
│  ├── Drought & Tanker Allocation Agent       │
│  └── Infrastructure Self-Healing Agent       │
└──────────────┬───────────────────────────────┘
               │
               ▼ (Actionable Output)
[Interactive GIS Map / Automated Alert Dispatch / Tanker Grid]
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate     # Windows
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Then open **http://localhost:3000** in your browser.

## 🎯 Features

### Monsoon Mode 🌧️
- Real-time flood risk prediction per zone
- Drainage bottleneck analysis
- Automated pump station activation
- Traffic rerouting suggestions
- Cloudburst detection & alerting

### Drought Mode ☀️
- Groundwater level monitoring
- Water deficit index per zone
- Smart tanker fleet dispatch & tracking
- Pipeline leak detection
- Heatwave early warning

### Infrastructure Digital Twin 🔧
- Pipe network integrity monitoring
- Anomaly detection & auto-isolation
- Automated work order generation
- Predictive maintenance scoring

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, TypeScript, Tailwind CSS, Leaflet.js |
| Backend | Python, FastAPI, WebSocket |
| Simulation | Custom IoT data generator (numpy) |
| Agents | Multi-agent swarm (Monsoon, Drought, Infrastructure) |
| Map Tiles | CartoDB Dark Matter |

## 📜 License
Built with ❤️ for hackathon by **Team Grey Coder**
