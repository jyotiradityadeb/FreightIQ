"""
FreightIQ FastAPI Pydantic Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional


class HealthResponse(BaseModel):
    status: str = "ok"
    app_title: str
    is_demo_data: bool = True
    message: str = "FreightIQ API is healthy"


class MarketLatestResponse(BaseModel):
    latest_date: str
    freight_rate: float
    bdi: float
    capesize_index: float
    panamax_index: float
    iron_ore_price: float
    coking_coal_price: float
    port_congestion_score: float
    avg_waiting_hours: float
    vessel_availability_count: int
    weather_risk_score: float
    event_risk_score: float
    is_demo_data: bool = True


class ForecastRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    horizon: int = Field(default=14, ge=1, le=60, description="Forecast horizon in days")
    model_name: str = Field(default="Auto", description="Auto, SARIMA, Naive Baseline, or Prophet")


class ForecastResponse(BaseModel):
    selected_model: str
    metrics: Dict[str, Any]
    selection_reason: str
    forecast_records: List[Dict[str, Any]]
    comparison_table: List[Dict[str, Any]]
    is_demo_data: bool = True


class OptimizeRequest(BaseModel):
    cargo_type: str = Field(default="Coking Coal", description="Iron Ore or Coking Coal")
    quantity_tonnes: float = Field(default=75000.0, ge=10000, le=250000)
    origin: str = Field(default="Australia", description="Australia, Indonesia, or South Africa")
    destination: str = Field(default="Paradip", description="Paradip, Visakhapatnam, or Kolkata/Haldia")
    earliest_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    latest_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    vessel_class: str = Field(default="Auto", description="Auto, Capesize, Panamax, or Supramax")
    demurrage_rate: Optional[float] = None
    risk_tolerance: str = Field(default="Medium", description="Low, Medium, or High")


class OptimizeResponse(BaseModel):
    success: bool
    recommendation: Dict[str, Any]
    best_option: Dict[str, Any]
    scenarios: Dict[str, Any]
    is_demo_data: bool = True


class BacktestRequest(BaseModel):
    start_date: str = Field(default="2025-01-01", description="YYYY-MM-DD")
    end_date: str = Field(default="2026-06-30", description="YYYY-MM-DD")
    horizon: int = Field(default=14, ge=7, le=30)
    step_days: int = Field(default=14, ge=1, le=30)
    cargo_type: str = Field(default="Coking Coal")
    quantity_tonnes: float = Field(default=75000.0)
    origin: str = Field(default="Australia")
    destination: str = Field(default="Paradip")
    vessel_class: str = Field(default="Panamax")


class BacktestResponse(BaseModel):
    success: bool
    historical_simulation_title: str
    benchmark_name: str
    test_periods_count: int
    win_count: int
    win_rate_percentage: float
    benchmark_simulated_cost_total: float
    freightiq_simulated_cost_total: float
    simulated_cost_difference_total: float
    simulated_savings_percentage: float
    forecast_accuracy_metrics: Dict[str, Any]
    period_results_table: List[Dict[str, Any]]
    disclaimer: str
    is_demo_data: bool = True


class ScenarioShock(BaseModel):
    freight_rate_shock_pct: float = Field(default=0.0, ge=-20.0, le=30.0, description="Freight Rate Change (-20% to +30%)")
    port_congestion_shock_pct: float = Field(default=0.0, ge=-50.0, le=100.0, description="Congestion Change (-50% to +100%)")
    target_port: str = Field(default="Paradip", description="Paradip, Visakhapatnam, Kolkata/Haldia, or All East Coast Ports")
    vessel_availability_shock_pct: float = Field(default=0.0, ge=-60.0, le=50.0, description="Availability Change (-60% to +50%)")
    commodity_price_shock_pct: float = Field(default=0.0, ge=-20.0, le=30.0, description="Commodity Price Change (-20% to +30%)")
    weather_risk_level: str = Field(default="Low", description="Low, Moderate, High, or Severe")
    geopolitical_risk_level: str = Field(default="Normal", description="Normal, Elevated, or Major Disruption")
    demurrage_rate_shock_pct: float = Field(default=0.0, ge=-20.0, le=50.0, description="Demurrage Rate Change (-20% to +50%)")


class ScenarioRequest(BaseModel):
    cargo_type: str = Field(default="Coking Coal")
    quantity_tonnes: float = Field(default=75000.0, ge=10000, le=250000)
    origin: str = Field(default="Australia")
    destination: str = Field(default="Paradip")
    earliest_date: Optional[str] = None
    latest_date: Optional[str] = None
    vessel_class: str = Field(default="Auto")
    risk_tolerance: str = Field(default="Medium")
    shock: ScenarioShock = Field(default_factory=ScenarioShock)


class ScenarioResponse(BaseModel):
    success: bool
    baseline_recommendation: Dict[str, Any]
    stressed_recommendation: Dict[str, Any]
    comparison_table: List[Dict[str, Any]]
    decision_status: str
    explanation: str
    sensitivity_analysis: List[Dict[str, Any]]
    threshold_analysis: List[Dict[str, Any]]
    confidence_score: float
    confidence_breakdown: Dict[str, Any]
    port_alternative_analysis: List[Dict[str, Any]]
    is_demo_data: bool = True


class ControlTowerResponse(BaseModel):
    success: bool
    current_recommendation: Dict[str, Any]
    signal_states: Dict[str, Any]
    active_alerts: List[Dict[str, Any]]
    port_status: List[Dict[str, Any]]
    route_status: List[Dict[str, Any]]
    decision_stability: Dict[str, Any]
    market_stress_index: Dict[str, Any]
    recommended_action: Dict[str, Any]
    event_log_summary: List[Dict[str, Any]]
    disruption_simulated: bool = False
    is_demo_data: bool = True


class DecisionTwinRequest(BaseModel):
    cargo_type: str = Field(default="Coking Coal")
    quantity_tonnes: float = Field(default=75000.0, ge=10000, le=250000)
    origin: str = Field(default="Australia")
    destination: str = Field(default="Paradip")
    vessel_class: str = Field(default="Auto")
    risk_tolerance: str = Field(default="Medium")
    simulations_count: int = Field(default=1000, ge=50, le=5000)
    seed: int = Field(default=42)
    shock: Optional[ScenarioShock] = None


class DecisionTwinResponse(BaseModel):
    success: bool
    simulations_count: int
    seed: int
    hero_summary: Dict[str, Any]
    robust_choice_comparison: Dict[str, Any]
    cost_of_waiting: List[Dict[str, Any]]
    heatmap_matrix: List[Dict[str, Any]]
    validity_thresholds: Dict[str, Any]
    counterfactuals: List[Dict[str, Any]]
    pareto_candidates: List[Dict[str, Any]]
    fan_chart_data: Dict[str, Any]
    win_frequency_distribution: List[Dict[str, Any]]
    all_candidates: List[Dict[str, Any]]
    disclaimer: str
    is_demo_data: bool = True



