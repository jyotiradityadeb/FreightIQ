# FreightIQ – Decision-Support Prototype for Freight Rate Forecasting & Vessel Chartering

**FreightIQ** is a maritime freight decision-support prototype built for Indian bulk cargo procurement teams (coking coal and iron ore imports into India's East Coast ports: Paradip, Visakhapatnam, Kolkata/Haldia).

---

## 🚀 Quick Start & Local Development

### 1. Installation
```bash
# Clone repository and enter directory
cd FreightIQ

# Install required dependencies
pip install -r requirements.txt
```

### 2. Generate Demonstration Datasets
```bash
python -m data.generate_demo_data
```

### 3. Launch Application & Control Tower
```bash
streamlit run app/Home.py
```
*Access Streamlit UI at `http://localhost:8501`*

### 4. Launch FastAPI Server
```bash
uvicorn backend.main:app --port 8000
```
*Access API Docs at `http://localhost:8000/docs`*

### 5. Run Automated Test Suite
```bash
python -m pytest -v tests/
```

---

## ⚙️ Deployment Modes & Integration Architecture

FreightIQ operates in two deployment modes configured via environment variables:

1. **`DEMO` (Default)**: Uses synthetic, reproducible demonstration datasets (`IS_DEMO_DATA=True`). Operates 100% offline without requiring external API credentials.
2. **`LIVE_READY`**: Evaluates configured external API connectors (Baltic freight rate indices, AIS vessel tracking, commodity prices, port congestion, weather risk). Unconfigured connectors fall back gracefully (`status = "NOT_CONFIGURED"`) without crashing the decision engine.

### Environment Setup (`.env`)
Copy `.env.example` to `.env`:
```env
DATA_MODE=DEMO
SIH_DEMO_MODE=true

# Optional Live Connectors
FREIGHT_API_URL=
FREIGHT_API_KEY=

AIS_API_URL=
AIS_API_KEY=

COMMODITY_API_URL=
COMMODITY_API_KEY=

PORT_API_URL=
PORT_API_KEY=

WEATHER_API_URL=
WEATHER_API_KEY=
```

---

## 📊 Data Connector Schemas

Every normalized connector output implements data provenance tracking (`source_name`, `source_mode`, `retrieved_at`):

### Freight Rate Connector
```json
{
  "timestamp": "2026-09-16",
  "freight_rate": 26.14,
  "bdi": 1850.0,
  "capesize_index": 2450.0,
  "panamax_index": 1720.0,
  "source_name": "Freight Benchmarks API (Synthetic Demo)",
  "source_mode": "DEMO",
  "retrieved_at": "2026-09-16T17:33:00Z"
}
```

### AIS Vessel Supply Connector
```json
{
  "timestamp": "2026-09-16",
  "vessel_class": "Panamax",
  "available_count": 25,
  "region": "East Coast India",
  "source_name": "AIS Vessel Tracking API (Synthetic Demo)",
  "source_mode": "DEMO",
  "retrieved_at": "2026-09-16T17:33:00Z"
}
```

---

## 🐳 Docker Deployment

### Single Command Container Build
```bash
docker-compose up --build
```
*Streamlit UI: `http://localhost:8501`*  
*FastAPI: `http://localhost:8000`*

---

## 🔒 Security Guidelines

* API credentials are set via environment variables or secret managers.
* No API keys or commercial credentials should be committed to version control.
* Offline demo mode operates safely in isolated staging or competition environments.

---

## 📜 Prototype Disclosure & Disclaimers

1. **Software Prototype**: FreightIQ is a software decision-support prototype system.
2. **Demo Data**: Operates on synthetic demonstration data unless live adapters are configured.
3. **INR Presentation**: USD benchmark shipping rates are presented in INR for Indian procurement users using a configurable demonstration conversion rate ($1 \text{ USD} = \text{₹}84.0$).
4. **Non-Commercial**: Not a commercial charter commitment or financial advice.
