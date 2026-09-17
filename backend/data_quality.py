"""
FreightIQ Data Quality & Freshness Engine Module
"""

import datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field


class DataMode(str, Enum):
    DEMO = "DEMO"
    PUBLIC_LIVE = "PUBLIC_LIVE"
    CONNECTED = "CONNECTED"


class FreshnessStatus(str, Enum):
    FRESH = "FRESH"
    AGING = "AGING"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"



class SignalMetadata(BaseModel):
    signal_id: str
    display_name: str
    category: str
    source_name: str
    mode: str = "DEMO"  # DEMO, PUBLIC_LIVE, CONNECTED, MANUAL_OVERRIDE
    retrieved_at: str
    age_minutes: float = 0.0
    freshness_status: str = "FRESH"  # FRESH, AGING, STALE, UNAVAILABLE
    is_demo: bool = True
    badge_label: str = "D"  # D = Demo, P = Public Live, C = Connected, M = Manual Override
    details: str = "Operating on FreightIQ Synthetic Demo Dataset"


class DataQualitySummary(BaseModel):
    data_mode: str = "DEMO"
    overall_coverage_pct: float = 88.0
    freshness_status: str = "FRESH"
    live_sources_count: int = 0
    public_sources_count: int = 1
    demo_sources_count: int = 4
    connected_sources_count: int = 0
    signal_matrix: List[SignalMetadata]
    confidence_explanation: str = "Decision Data Confidence evaluated based on active connector mode, signal freshness, and coverage."


def evaluate_signal_freshness(
    retrieved_timestamp: Optional[datetime.datetime] = None,
    data_type: str = "REALTIME"
) -> Tuple[float, str]:
    """
    Evaluates signal freshness given timestamp and policy data type.
    Returns (age_minutes, freshness_status).
    """
    if retrieved_timestamp is None:
        now = datetime.datetime.now()
        retrieved_timestamp = now - datetime.timedelta(minutes=3)

    now = datetime.datetime.now()
    delta = now - retrieved_timestamp
    age_min = max(0.0, delta.total_seconds() / 60.0)

    if data_type == "REALTIME":
        if age_min < 15.0:
            status = "FRESH"
        elif age_min < 60.0:
            status = "AGING"
        else:
            status = "STALE"
    elif data_type == "DAILY":
        if age_min < 1440.0:  # 24 hours
            status = "FRESH"
        elif age_min < 2880.0:  # 48 hours
            status = "AGING"
        else:
            status = "STALE"
    else:
        status = "FRESH"

    return round(age_min, 1), status


def get_system_data_quality(data_mode: str = "DEMO") -> DataQualitySummary:
    """
    Returns unified Data Quality & Signal Lineage matrix across all 5 prototype adapters.
    """
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M IST")
    
    signals = [
        SignalMetadata(
            signal_id="freight_benchmark",
            display_name="Freight Rate Benchmarks",
            category="Freight Market",
            source_name="Baltic Dry Index Synthetic Feed",
            mode="DEMO" if data_mode == "DEMO" else "CONNECTED",
            retrieved_at=now_str,
            age_minutes=5.0,
            freshness_status="FRESH",
            is_demo=(data_mode == "DEMO"),
            badge_label="D" if data_mode == "DEMO" else "C",
            details="Baltic Panamax & Capesize benchmark rates"
        ),
        SignalMetadata(
            signal_id="ais_vessel_supply",
            display_name="AIS Vessel Availability",
            category="Vessel Supply",
            source_name="East Coast India AIS Tracker",
            mode="DEMO" if data_mode == "DEMO" else "LIVE_READY",
            retrieved_at=now_str,
            age_minutes=12.0,
            freshness_status="FRESH",
            is_demo=(data_mode == "DEMO"),
            badge_label="D" if data_mode == "DEMO" else "C",
            details="Vessel availability counts by port node"
        ),
        SignalMetadata(
            signal_id="port_operations",
            display_name="Port Operations & Congestion",
            category="Port Infrastructure",
            source_name="Paradip/Vizag Port Queue Feed",
            mode="DEMO" if data_mode == "DEMO" else "CONNECTED",
            retrieved_at=now_str,
            age_minutes=8.0,
            freshness_status="FRESH",
            is_demo=(data_mode == "DEMO"),
            badge_label="D" if data_mode == "DEMO" else "C",
            details="Port congestion index & avg waiting hours"
        ),
        SignalMetadata(
            signal_id="weather_risk",
            display_name="Marine Weather & Route Risk",
            category="Route Environment",
            source_name="Open/Public Ocean Weather API",
            mode="PUBLIC_LIVE",
            retrieved_at=now_str,
            age_minutes=4.0,
            freshness_status="FRESH",
            is_demo=False,
            badge_label="P",
            details="Marine wind, wave height & cyclone risk"
        ),
        SignalMetadata(
            signal_id="commodity_prices",
            display_name="Commodity Price Benchmarks",
            category="Commodity Context",
            source_name="Coking Coal & Ore Feed",
            mode="DEMO" if data_mode == "DEMO" else "CONNECTED",
            retrieved_at=now_str,
            age_minutes=18.0,
            freshness_status="FRESH",
            is_demo=(data_mode == "DEMO"),
            badge_label="D" if data_mode == "DEMO" else "C",
            details="Coking coal & iron ore spot benchmarks"
        )
    ]

    demo_cnt = sum(1 for s in signals if s.mode == "DEMO")
    pub_cnt = sum(1 for s in signals if s.mode == "PUBLIC_LIVE")
    conn_cnt = sum(1 for s in signals if s.mode == "CONNECTED")

    return DataQualitySummary(
        data_mode=data_mode,
        overall_coverage_pct=92.0 if data_mode != "DEMO" else 85.0,
        freshness_status="FRESH",
        live_sources_count=pub_cnt + conn_cnt,
        public_sources_count=pub_cnt,
        demo_sources_count=demo_cnt,
        connected_sources_count=conn_cnt,
        signal_matrix=signals
    )


class ConfidenceScore(BaseModel):
    score: float
    confidence_tier: str
    explanation: str


def evaluate_freshness(signal_type: str, age_seconds: float) -> FreshnessStatus:
    """Evaluates freshness status for a given signal age in seconds."""
    age_min = age_seconds / 60.0
    _, status_str = evaluate_signal_freshness(
        retrieved_timestamp=datetime.datetime.now() - datetime.timedelta(minutes=age_min),
        data_type="REALTIME" if signal_type != "freight_benchmark" else "DAILY"
    )
    return FreshnessStatus(status_str)


def evaluate_decision_confidence(
    coverage_pct: float,
    live_signals_count: int,
    total_signals_count: int
) -> ConfidenceScore:
    """Evaluates overall decision data confidence."""
    ratio = live_signals_count / max(1, total_signals_count)
    score = round(coverage_pct * 0.6 + ratio * 40.0, 1)
    tier = "High" if score >= 80.0 else ("Medium" if score >= 60.0 else "Low")
    return ConfidenceScore(
        score=score,
        confidence_tier=tier,
        explanation=f"Confidence evaluated at {score}/100 based on {coverage_pct}% coverage and {live_signals_count}/{total_signals_count} live connectors."
    )


class DataQualityEngine:
    """Engine interface for data freshness & quality evaluation."""
    @staticmethod
    def get_summary(mode: str = "DEMO") -> DataQualitySummary:
        return get_system_data_quality(mode)

