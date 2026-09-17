"""
FreightIQ Synthetic Demo Data Generator — v2 (Batch E)

DESIGN: Every observed series is derived independently from HIDDEN LATENT FACTORS.
No observed series is a function of freight_rate (the forecast target) or of any
series derived from it.  Correlations emerge from shared latent drivers — that is
realistic and intentional.

Latent factors (all normalised to roughly mean≈0, std≈0.3–0.5 for easy scaling):
  demand    – global dry-bulk trade cycle: AR(1) + annual seasonality + slow trend
  supply    – vessel fleet tightness: very slow AR(1) + biannual fleet cycle
  bunker    – fuel cost cycle: AR(1) + upward drift
  port      – port stress (congestion / weather combined): AR(1) + monsoon spike
  commodity – steel / coal industrial demand: AR(1) + seasonal + trend
  macro     – broad economic cycle: slow AR(1)
  weather   – seasonal (Jun–Sep) + stochastic disruption
  shock     – discrete geopolitical / labour events (same timing as v1)

Fixed seed (42) guarantees full reproducibility.  Values differ from v1 — intended.
"""

import os
import numpy as np
import pandas as pd
from backend.config import RANDOM_SEED


def generate_demo_dataset():
    np.random.seed(RANDOM_SEED)

    dates = pd.date_range(start="2024-01-01", end="2026-08-31", freq="D")
    n_days = len(dates)
    t = np.arange(n_days, dtype=float)

    # ── Pre-draw ALL noise in a fixed order (determinism guarantee) ────────────
    # Latent factor innovations
    n_demand    = np.random.normal(0, 0.055, n_days)
    n_supply    = np.random.normal(0, 0.030, n_days)
    n_bunker    = np.random.normal(0, 0.080, n_days)
    n_port      = np.random.normal(0, 0.120, n_days)
    n_commodity = np.random.normal(0, 0.075, n_days)
    n_macro     = np.random.normal(0, 0.050, n_days)
    n_weather   = np.random.exponential(0.25, n_days)
    # Observed-series idiosyncratic noise
    n_freight   = np.random.normal(0, 0.45, n_days)
    n_bdi       = np.random.normal(0, 55.0, n_days)
    n_capesize  = np.random.normal(0, 100.0, n_days)
    n_panamax   = np.random.normal(0, 42.0, n_days)
    n_iron_ore  = np.random.normal(0, 2.2, n_days)
    n_coal      = np.random.normal(0, 4.0, n_days)
    n_cong      = np.random.exponential(6.0, n_days)
    n_vessel    = np.random.normal(0, 2.5, n_days)
    n_waiting   = np.random.normal(0, 2.0, n_days)
    n_wrisk     = np.random.normal(0, 0.6, n_days)
    n_event     = np.random.normal(0, 0.3, n_days)

    # ── LATENT FACTORS ─────────────────────────────────────────────────────────

    # 1. Global dry-bulk demand: slow AR(1) + annual seasonality + mild trend
    demand = np.zeros(n_days)
    for i in range(1, n_days):
        demand[i] = 0.97 * demand[i - 1] + n_demand[i]
    demand = (demand
              + 0.40 * np.sin(2 * np.pi * t / 365.25)
              + 0.15 * np.cos(4 * np.pi * t / 365.25)
              + 0.0015 * t)

    # 2. Vessel supply tightness: very slow AR(1) + biannual fleet cycle
    supply = np.zeros(n_days)
    for i in range(1, n_days):
        supply[i] = 0.99 * supply[i - 1] + n_supply[i]
    supply = supply + 0.25 * np.sin(2 * np.pi * (t - 90) / 365.25)

    # 3. Bunker fuel cost index: AR(1) + upward drift
    bunker = np.zeros(n_days)
    for i in range(1, n_days):
        bunker[i] = 0.95 * bunker[i - 1] + n_bunker[i]
    bunker = bunker + 0.0008 * t

    # 4. Port stress: AR(1) + seasonal monsoon spike (Jul–Sep peaks)
    port = np.zeros(n_days)
    for i in range(1, n_days):
        port[i] = 0.90 * port[i - 1] + n_port[i]
    monsoon = np.clip(1.8 * np.sin(2 * np.pi * (t - 150) / 365.25), 0.0, None)
    port = port + monsoon

    # 5. Commodity (steel / coal) demand: AR(1) + seasonal + mild trend
    commodity = np.zeros(n_days)
    for i in range(1, n_days):
        commodity[i] = 0.96 * commodity[i - 1] + n_commodity[i]
    commodity = (commodity
                 + 0.30 * np.sin(2 * np.pi * t / 365.25 + 0.5)
                 + 0.0008 * t)

    # 6. Macro cycle: very slow AR(1)
    macro = np.zeros(n_days)
    for i in range(1, n_days):
        macro[i] = 0.98 * macro[i - 1] + n_macro[i]

    # 7. Weather disruption: Jun–Sep seasonal peak + stochastic
    weather_seasonal = np.maximum(0.0, np.sin(2 * np.pi * (t - 180) / 365.25))
    weather = weather_seasonal + n_weather * 0.6

    # 8. Discrete shock events (same timing as v1)
    shock = np.zeros(n_days)
    for day, magnitude in [(120, 2.5), (310, 2.8), (580, 3.0), (810, 3.2)]:
        if day < n_days:
            decay_len = min(12, n_days - day)
            shock[day:day + decay_len] += magnitude * np.exp(-np.arange(decay_len))

    # Q3 monsoon bump (Jul / Aug / Sep)
    q3_bump = np.array([1.2 if dates[i].month in [7, 8, 9] else 0.0
                        for i in range(n_days)])

    # ── OBSERVED SERIES — every one is a function of LATENTS only ─────────────
    # freight_rate is computed first but is NOT referenced by any subsequent series.

    # freight_rate: f(demand, supply, bunker, port, shock, q3_bump)
    fr_raw = (24.0
              + 4.0 * demand
              + 2.5 * supply
              + 2.0 * bunker
              + 1.5 * port
              + 0.8 * shock
              + q3_bump
              + n_freight)
    freight_rate = np.clip(fr_raw, 12.0, 48.0)

    # bdi: g(demand, supply, bunker)  — NOT derived from freight_rate
    bdi_raw = (1100.0
               + 280.0 * demand
               + 140.0 * supply
               + 65.0  * bunker
               + n_bdi)
    bdi = np.clip(bdi_raw, 300.0, 3500.0)

    # capesize_index: own latent function — NOT derived from bdi or freight_rate
    capesize_raw = (2200.0
                    + 520.0 * demand
                    + 240.0 * supply
                    + 90.0  * bunker
                    + n_capesize)
    capesize_index = np.clip(capesize_raw, 500.0, 7000.0)

    # panamax_index: own latent function — NOT derived from bdi or freight_rate
    panamax_raw = (1150.0
                   + 245.0 * demand
                   + 115.0 * supply
                   + 42.0  * bunker
                   + n_panamax)
    panamax_index = np.clip(panamax_raw, 350.0, 3000.0)

    # iron_ore_price: h(commodity, macro)  — NOT derived from freight_rate
    iron_raw = (108.0
                + 13.0 * commodity
                + 6.0  * macro
                + 8.0  * np.cos(2 * np.pi * t / 365.25)
                + 0.014 * t
                + n_iron_ore)
    iron_ore_price = np.clip(iron_raw, 60.0, 200.0)

    # coking_coal_price: k(commodity, macro)  — NOT derived from freight_rate
    coal_raw = (228.0
                + 20.0 * commodity
                + 9.0  * macro
                + 15.0 * np.sin(2 * np.pi * t / 365.25 + 0.5)
                + 0.025 * t
                + n_coal)
    coking_coal_price = np.clip(coal_raw, 130.0, 400.0)

    # port_congestion_score: p(port latent)  — NOT derived from freight_rate
    cong_raw = 45.0 + 18.0 * port + n_cong
    port_congestion_score = np.clip(cong_raw, 15.0, 98.0)

    # avg_waiting_hours: from congestion (NOT from freight_rate)
    wait_raw = port_congestion_score * 0.65 + n_waiting
    avg_waiting_hours = np.clip(wait_raw, 8.0, 96.0)

    # vessel_availability_count: r(supply, demand, congestion)  — NOT from freight_rate
    avail_raw = (35.0
                 - 3.5 * supply
                 - 2.0 * demand
                 - (port_congestion_score - 45.0) * 0.12
                 + n_vessel)
    vessel_availability_count = np.clip(avail_raw, 10, 60).astype(int)

    # weather_risk_score: seasonal disruption latent
    wrisk_raw = 4.0 * weather + 4.0 + n_wrisk
    weather_risk_score = np.clip(wrisk_raw, 0.0, 10.0)

    # event_risk_score: discrete shocks (same timing as v1)
    event_risk_score = np.ones(n_days) * 1.5
    event_risk_score[115:125] = 7.5
    event_risk_score[305:315] = 8.0
    event_risk_score[575:585] = 8.5
    event_risk_score[805:815] = 9.0
    event_risk_score = np.clip(event_risk_score + n_event, 0.0, 10.0)

    # ── SANITY CHECK — print min/max/mean for every series ────────────────────
    def _stats(arr, name):
        print(f"  {name:36s}  min={arr.min():.2f}  max={arr.max():.2f}  mean={arr.mean():.2f}")

    print(f"\nGenerated {n_days} daily rows (Jan 2024 – Aug 2026) — latent-factor generator v2.")
    print("Series ranges:")
    _stats(freight_rate,              "freight_rate (USD/t)")
    _stats(bdi,                       "bdi")
    _stats(capesize_index,            "capesize_index")
    _stats(panamax_index,             "panamax_index")
    _stats(iron_ore_price,            "iron_ore_price (USD/t)")
    _stats(coking_coal_price,         "coking_coal_price (USD/t)")
    _stats(port_congestion_score,     "port_congestion_score")
    _stats(avg_waiting_hours,         "avg_waiting_hours")
    _stats(vessel_availability_count.astype(float), "vessel_availability_count")
    _stats(weather_risk_score,        "weather_risk_score")
    _stats(event_risk_score,          "event_risk_score")

    # Pearson correlations (leakage audit)
    def _r(a, b):
        return float(np.corrcoef(a, b)[0, 1])

    print("\nLeakage audit — Pearson r with freight_rate:")
    print(f"  r(freight_rate, bdi)             = {_r(freight_rate, bdi):.4f}")
    print(f"  r(freight_rate, capesize_index)  = {_r(freight_rate, capesize_index):.4f}")
    print(f"  r(freight_rate, panamax_index)   = {_r(freight_rate, panamax_index):.4f}")
    print(f"  r(freight_rate, iron_ore_price)  = {_r(freight_rate, iron_ore_price):.4f}")
    print(f"  r(freight_rate, coking_coal)     = {_r(freight_rate, coking_coal_price):.4f}")

    # ── WRITE CSVs ─────────────────────────────────────────────────────────────
    os.makedirs("data", exist_ok=True)

    pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "freight_rate": np.round(freight_rate, 2),
        "bdi": np.round(bdi, 1),
        "capesize_index": np.round(capesize_index, 1),
        "panamax_index": np.round(panamax_index, 1),
    }).to_csv("data/freight_rates.csv", index=False)

    pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "iron_ore_price": np.round(iron_ore_price, 2),
        "coking_coal_price": np.round(coking_coal_price, 2),
    }).to_csv("data/commodity_prices.csv", index=False)

    pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "port_congestion_score": np.round(port_congestion_score, 1),
        "avg_waiting_hours": np.round(avg_waiting_hours, 1),
    }).to_csv("data/port_congestion.csv", index=False)

    pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "vessel_availability_count": vessel_availability_count,
    }).to_csv("data/vessel_availability.csv", index=False)

    pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "weather_risk_score": np.round(weather_risk_score, 1),
        "event_risk_score": np.round(event_risk_score, 1),
    }).to_csv("data/events.csv", index=False)


if __name__ == "__main__":
    generate_demo_dataset()
