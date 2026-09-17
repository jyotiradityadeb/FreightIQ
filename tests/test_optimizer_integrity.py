"""
Optimizer integrity and sensitivity-wiring tests.
"""

import pytest
import pandas as pd
from backend.data_loader import load_raw_datasets
from backend.features import generate_features
from backend.forecasting import generate_freight_forecast
from backend.optimizer import optimize_charter_timing, evaluate_charter_candidate
from backend.config_model import (
    DEMURRAGE_EXPOSURE_FACTOR,
    CONGESTION_COST_MULTIPLIER,
    WEATHER_RISK_PENALTY_PER_POINT,
    EVENT_RISK_PENALTY_PER_POINT,
)


@pytest.fixture(scope="module")
def forecast_df():
    raw_df = load_raw_datasets()
    feat_df = generate_features(raw_df)
    fc_res = generate_freight_forecast(feat_df, horizon=14, selected_model="Auto")
    return fc_res["forecast_df"]


@pytest.fixture(scope="module")
def std_res(forecast_df):
    """Standard demo shipment result used as the oracle for multiple tests."""
    return optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        vessel_class="Auto",
    )


# ── Selected candidate has minimum feasible cost ─────────────────────────────

def test_winner_has_minimum_total_cost(std_res):
    """The selected candidate must have the lowest total_logistics_cost among all feasible ones."""
    assert std_res["success"]
    candidates = std_res["all_evaluated_candidates"]
    assert len(candidates) > 0
    winner_cost = std_res["best_option"]["total_logistics_cost_usd"]
    for c in candidates:
        assert c["total_logistics_cost_usd"] >= winner_cost - 0.01, (
            f"Candidate {c['vessel_class']} on {c['charter_date']} costs "
            f"{c['total_logistics_cost_usd']:.2f} < winner {winner_cost:.2f}"
        )


# ── Infeasible vessel can never be selected ───────────────────────────────────

def test_infeasible_capacity_never_selected(forecast_df):
    """A cargo exceeding Supramax max capacity must not produce a Supramax recommendation."""
    res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Iron Ore",
        quantity_tonnes=80000.0,  # > Supramax max (65 000 t)
        origin="Australia",
        destination="Paradip",
        vessel_class="Auto",
    )
    if res["success"]:
        for c in res["all_evaluated_candidates"]:
            assert c["vessel_class"] != "Supramax", (
                "Supramax should be infeasible for 80 000 t cargo"
            )


def test_infeasible_capesize_haldia(forecast_df):
    """Capesize is draft-incompatible with Kolkata/Haldia — must never appear in feasible candidates."""
    res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Kolkata/Haldia",
        vessel_class="Auto",
    )
    if res["success"]:
        for c in res["all_evaluated_candidates"]:
            assert c["vessel_class"] != "Capesize", (
                "Capesize must be infeasible for Kolkata/Haldia due to draft limits"
            )


# ── WIRING TEST — perturbation reaches the cost function ─────────────────────

def test_demurrage_factor_perturbation_changes_cost(forecast_df):
    """
    Critical wiring test: tripling the demurrage exposure factor must change at least
    one candidate's total cost.  A perturbation that changes nothing is a bug.
    """
    normal_res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
    )
    assert normal_res["success"]
    normal_costs = {c["charter_date"]: c["total_logistics_cost_usd"]
                    for c in normal_res["all_evaluated_candidates"]}

    perturbed_res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
        cost_factor_overrides={"demurrage_factor": DEMURRAGE_EXPOSURE_FACTOR * 3.0},
    )
    assert perturbed_res["success"]
    perturbed_costs = {c["charter_date"]: c["total_logistics_cost_usd"]
                       for c in perturbed_res["all_evaluated_candidates"]}

    changed = any(
        abs(perturbed_costs.get(d, 0) - normal_costs.get(d, 0)) > 0.01
        for d in normal_costs
    )
    assert changed, (
        "Tripling the demurrage exposure factor did not change any candidate cost — "
        "the sensitivity override is not wired into the cost function"
    )


def test_congestion_multiplier_perturbation_changes_cost(forecast_df):
    """Halving the congestion multiplier must change at least one candidate's cost."""
    normal_res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
    )
    perturbed_res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
        cost_factor_overrides={"congestion_multiplier": CONGESTION_COST_MULTIPLIER * 0.5},
    )
    normal_total = normal_res["best_option"]["total_logistics_cost_usd"]
    perturbed_total = perturbed_res["best_option"]["total_logistics_cost_usd"]
    assert abs(perturbed_total - normal_total) > 0.01, (
        "Halving the congestion multiplier did not change the total cost"
    )


def test_weather_penalty_perturbation_changes_cost(forecast_df):
    """Doubling the weather risk penalty must change at least one candidate's cost."""
    normal_res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
    )
    perturbed_res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        vessel_class="Panamax",
        cost_factor_overrides={"weather_penalty": WEATHER_RISK_PENALTY_PER_POINT * 2.0},
    )
    normal_total = normal_res["best_option"]["total_logistics_cost_usd"]
    perturbed_total = perturbed_res["best_option"]["total_logistics_cost_usd"]
    assert abs(perturbed_total - normal_total) > 0.01


# ── Changing an assumption can change candidate rankings ─────────────────────

def test_large_perturbation_can_change_costs(forecast_df):
    """A ×5 weather penalty must produce different candidate costs (not necessarily different winner)."""
    normal_res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        vessel_class="Auto",
    )
    stressed_res = optimize_charter_timing(
        forecast_df=forecast_df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        vessel_class="Auto",
        cost_factor_overrides={
            "weather_penalty": WEATHER_RISK_PENALTY_PER_POINT * 5.0,
            "event_penalty": EVENT_RISK_PENALTY_PER_POINT * 5.0,
        },
    )
    normal_total = normal_res["best_option"]["total_logistics_cost_usd"]
    stressed_total = stressed_res["best_option"]["total_logistics_cost_usd"]
    assert stressed_total != normal_total, (
        "x5 risk penalties must change total cost"
    )


# ── Determinism ──────────────────────────────────────────────────────────────

def test_optimizer_is_deterministic(forecast_df):
    """Same inputs → byte-identical output across two runs."""
    kwargs = dict(
        forecast_df=forecast_df,
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        origin="Australia",
        destination="Paradip",
        vessel_class="Auto",
    )
    r1 = optimize_charter_timing(**kwargs)
    r2 = optimize_charter_timing(**kwargs)
    assert r1["recommendation"]["recommended_charter_date"] == r2["recommendation"]["recommended_charter_date"]
    assert r1["recommendation"]["recommended_vessel"] == r2["recommendation"]["recommended_vessel"]
    assert r1["recommendation"]["expected_total_logistics_cost_usd"] == r2["recommendation"]["expected_total_logistics_cost_usd"]


# ── Explainability matches actual numbers ────────────────────────────────────

def test_explainability_winner_cost_matches_best_option(std_res):
    """The explainability winner total_cost_usd must equal best_option's total cost."""
    expl = std_res.get("explainability", {})
    assert expl, "Optimizer result must include 'explainability' key"
    winner = expl["winner"]
    assert abs(winner["total_cost_usd"] - std_res["best_option"]["total_logistics_cost_usd"]) < 0.01


def test_explainability_breakdown_sums_to_total(std_res):
    """The four cost components in explainability must sum to the winner's total cost."""
    expl = std_res["explainability"]
    bd = expl["winner"]["cost_breakdown_usd"]
    component_sum = sum(bd.values())
    total = expl["winner"]["total_cost_usd"]
    assert abs(component_sum - total) < 1.0, (
        f"Cost component sum {component_sum:.2f} does not match total {total:.2f}"
    )


def test_explainability_alternatives_cost_exceeds_winner(std_res):
    """All alternative costs in explainability must be >= winner cost."""
    expl = std_res["explainability"]
    winner_cost = expl["winner"]["total_cost_usd"]
    for alt in expl["alternatives"]:
        assert alt["total_cost_usd"] >= winner_cost - 0.01, (
            f"Alternative {alt['candidate']} has lower cost than winner"
        )


def test_explainability_delta_matches_costs(std_res):
    """delta_vs_winner_usd must equal alternative total - winner total."""
    expl = std_res["explainability"]
    winner_cost = expl["winner"]["total_cost_usd"]
    for alt in expl["alternatives"]:
        expected_delta = round(alt["total_cost_usd"] - winner_cost, 2)
        assert abs(alt["delta_vs_winner_usd"] - expected_delta) < 0.02, (
            f"Delta mismatch for {alt['candidate']}: "
            f"stated {alt['delta_vs_winner_usd']:.2f} vs computed {expected_delta:.2f}"
        )


# ── evaluate_charter_candidate unit tests ────────────────────────────────────

def _sample_date():
    return pd.Timestamp("2026-09-18")


def test_evaluate_candidate_infeasible_capacity():
    """Cargo exceeding max capacity must return feasible=False."""
    res = evaluate_charter_candidate(
        charter_date=_sample_date(),
        vessel_class="Supramax",
        origin="Australia",
        destination="Paradip",
        cargo_type="Coking Coal",
        quantity_tonnes=80000.0,  # > Supramax max 65 000
        freight_rate_forecast=25.0,
        congestion_score=45.0,
        waiting_hours=24.0,
        vessel_avail_count=25,
        weather_risk=3.0,
        event_risk=2.0,
    )
    assert res["feasible"] is False


def test_evaluate_candidate_demurrage_override_reaches_cost():
    """cost_factor_overrides demurrage_factor=0.0 must produce demurrage_cost_usd=0."""
    res = evaluate_charter_candidate(
        charter_date=_sample_date(),
        vessel_class="Panamax",
        origin="Australia",
        destination="Paradip",
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        freight_rate_forecast=25.0,
        congestion_score=45.0,
        waiting_hours=24.0,
        vessel_avail_count=25,
        weather_risk=3.0,
        event_risk=2.0,
        cost_factor_overrides={"demurrage_factor": 0.0},
    )
    assert res["feasible"] is True
    assert res["demurrage_cost_usd"] == 0.0, (
        "Zero demurrage factor must produce zero demurrage cost"
    )


def test_evaluate_candidate_congestion_override_reaches_cost():
    """cost_factor_overrides congestion_multiplier=0.0 must produce congestion_cost_usd=0."""
    res = evaluate_charter_candidate(
        charter_date=_sample_date(),
        vessel_class="Panamax",
        origin="Australia",
        destination="Paradip",
        cargo_type="Coking Coal",
        quantity_tonnes=75000.0,
        freight_rate_forecast=25.0,
        congestion_score=45.0,
        waiting_hours=24.0,
        vessel_avail_count=25,
        weather_risk=3.0,
        event_risk=2.0,
        cost_factor_overrides={"congestion_multiplier": 0.0},
    )
    assert res["feasible"] is True
    assert res["congestion_cost_usd"] == 0.0
