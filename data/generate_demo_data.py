"""
FreightIQ Synthetic Demo Data Generator

Generates ~2.5 years of daily time-series data with realistic trends,
seasonality, commodity correlations, congestion spikes, weather events,
and stochastic noise. Uses a fixed seed (42) for exact reproducibility.
"""

import os
import numpy as np
import pandas as pd
from backend.config import RANDOM_SEED

def generate_demo_dataset():
    np.random.seed(RANDOM_SEED)

    # Date range: Jan 1, 2024 to Aug 31, 2026 (~974 days)
    dates = pd.date_range(start="2024-01-01", end="2026-08-31", freq="D")
    n_days = len(dates)

    t = np.arange(n_days)

    # Macro trend & seasonal components
    macro_trend = 22.0 + 0.005 * t + 2.5 * np.sin(2 * np.pi * t / 365.25)
    
    # Stochastic random walk with mean reversion for freight rate (USD / tonne)
    noise = np.random.normal(0, 0.4, n_days)
    freight_rate = np.zeros(n_days)
    freight_rate[0] = 22.5

    for i in range(1, n_days):
        # mean reversion to macro trend + seasonal bump in Q3 (monsoon / coal demand)
        season_bump = 1.2 if (dates[i].month in [7, 8, 9]) else 0.0
        shock = 3.5 if (i in [120, 310, 580, 810]) else 0.0  # occasional event shocks
        freight_rate[i] = freight_rate[i-1] + 0.15 * (macro_trend[i] + season_bump - freight_rate[i-1]) + noise[i] + shock

    freight_rate = np.clip(freight_rate, 12.0, 48.0)

    # Baltic Dry Index & Vessel Indices correlated with freight_rate
    bdi = freight_rate * 75.0 + np.random.normal(0, 40, n_days)
    capesize_index = bdi * 1.35 + np.random.normal(0, 60, n_days)
    panamax_index = bdi * 0.95 + np.random.normal(0, 30, n_days)

    # Commodity Prices (correlated with global industrial demand & freight)
    iron_ore_price = 105.0 + 0.015 * t + 8.0 * np.cos(2 * np.pi * t / 365.25) + freight_rate * 0.6 + np.random.normal(0, 1.8, n_days)
    coking_coal_price = 220.0 + 0.03 * t + 15.0 * np.sin(2 * np.pi * t / 365.25 + 0.5) + freight_rate * 1.5 + np.random.normal(0, 3.5, n_days)

    # Port Congestion & Waiting Hours (spikes in monsoon months July-September)
    base_congestion = 45.0 + 15.0 * np.sin(2 * np.pi * (t - 150) / 365.25)
    congestion_noise = np.random.exponential(scale=6.0, size=n_days)
    port_congestion_score = np.clip(base_congestion + congestion_noise, 15.0, 98.0)
    avg_waiting_hours = port_congestion_score * 0.65 + np.random.normal(0, 2.0, n_days)
    avg_waiting_hours = np.clip(avg_waiting_hours, 8.0, 96.0)

    # Vessel Availability Count (inverse to congestion & peak freight)
    base_availability = 35.0 - (freight_rate - 20.0) * 0.5 - (port_congestion_score - 40.0) * 0.25
    vessel_availability_count = np.clip(base_availability + np.random.normal(0, 2.5, n_days), 10, 60).astype(int)

    # Risk Scores
    weather_risk_score = np.clip(np.sin(2 * np.pi * (t - 180) / 365.25) * 4.0 + 4.0 + np.random.normal(0, 1.0, n_days), 0.0, 10.0)
    
    # Event Risk (discrete spikes for geopolitical/labor events)
    event_risk_score = np.ones(n_days) * 1.5
    event_risk_score[115:125] = 7.5  # Event shock 1
    event_risk_score[305:315] = 8.0  # Event shock 2
    event_risk_score[575:585] = 8.5  # Event shock 3
    event_risk_score[805:815] = 9.0  # Event shock 4
    event_risk_score = np.clip(event_risk_score + np.random.normal(0, 0.3, n_days), 0.0, 10.0)

    # Create directory if missing
    os.makedirs("data", exist_ok=True)

    # 1. freight_rates.csv
    df_freight = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "freight_rate": np.round(freight_rate, 2),
        "bdi": np.round(bdi, 1),
        "capesize_index": np.round(capesize_index, 1),
        "panamax_index": np.round(panamax_index, 1)
    })
    df_freight.to_csv("data/freight_rates.csv", index=False)

    # 2. commodity_prices.csv
    df_commodity = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "iron_ore_price": np.round(iron_ore_price, 2),
        "coking_coal_price": np.round(coking_coal_price, 2)
    })
    df_commodity.to_csv("data/commodity_prices.csv", index=False)

    # 3. port_congestion.csv
    df_congestion = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "port_congestion_score": np.round(port_congestion_score, 1),
        "avg_waiting_hours": np.round(avg_waiting_hours, 1)
    })
    df_congestion.to_csv("data/port_congestion.csv", index=False)

    # 4. vessel_availability.csv
    df_vessels = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "vessel_availability_count": vessel_availability_count
    })
    df_vessels.to_csv("data/vessel_availability.csv", index=False)

    # 5. events.csv
    df_events = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "weather_risk_score": np.round(weather_risk_score, 1),
        "event_risk_score": np.round(event_risk_score, 1)
    })
    df_events.to_csv("data/events.csv", index=False)

    print(f"Generated synthetic demo data with {n_days} daily rows (Jan 2024 - Aug 2026).")

if __name__ == "__main__":
    generate_demo_dataset()
