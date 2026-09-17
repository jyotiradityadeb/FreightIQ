import datetime
import urllib.request
import json
from typing import Dict, Any, List
from backend.integrations.base_adapter import BaseAdapter
from backend.data_loader import load_raw_datasets


class WeatherAdapter(BaseAdapter):
    def __init__(self, mode: str = "DEMO"):
        super().__init__(
            source_name="Public Marine Weather Connector (Open-Meteo)",
            mode=mode,
            api_url_env_var="WEATHER_API_URL",
            api_key_env_var="WEATHER_API_KEY",
            purpose="Weather penalty calculation & route risk adjustment"
        )

    def get_latest(self) -> Dict[str, Any]:
        provenance = self._get_provenance_metadata()
        
        # If PUBLIC_LIVE mode requested, attempt genuine open API query for Paradip port coordinates
        if self.mode == "PUBLIC_LIVE":
            try:
                url = "https://api.open-meteo.com/v1/forecast?latitude=20.26&longitude=86.67&current_weather=true"
                req = urllib.request.Request(url, headers={"User-Agent": "FreightIQ/1.0"})
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    curr = data.get("current_weather", {})
                    wind = float(curr.get("windspeed", 15.0))
                    # Map wind speed (km/h) to 1.0 - 10.0 risk score
                    weather_risk = float(round(min(10.0, max(1.0, wind / 5.0)), 1))
                    return {
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "weather_risk_score": weather_risk,
                        "event_risk_score": 1.5,
                        "source_name": "Open-Meteo Public Weather API",
                        "source_mode": "PUBLIC_LIVE",
                        "retrieved_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M IST")
                    }
            except Exception:
                pass  # Fallback to demo data on network error

        df = load_raw_datasets()
        latest = df.iloc[-1]

        return {
            "timestamp": latest["date"].strftime("%Y-%m-%d"),
            "weather_risk_score": float(latest["weather_risk_score"]),
            "event_risk_score": float(latest["event_risk_score"]),
            **provenance
        }

    def get_history(self, horizon_days: int = 30) -> List[Dict[str, Any]]:
        provenance = self._get_provenance_metadata()
        df = load_raw_datasets().tail(horizon_days)
        records = []
        for _, row in df.iterrows():
            records.append({
                "timestamp": row["date"].strftime("%Y-%m-%d"),
                "weather_risk_score": float(row["weather_risk_score"]),
                "event_risk_score": float(row["event_risk_score"]),
                **provenance
            })
        return records
