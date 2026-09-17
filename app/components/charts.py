"""
FreightIQ Industrial Plotly Visual System Engine

Provides restrained industrial Plotly charts formatted in INR / Indian metrics without neon effects or emojis.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Optional, List
from app.components.helpers import usd_to_inr

# Industrial Palette
COLOR_HISTORICAL = "#9CA8B5"
COLOR_FORECAST = "#3B73B9"
COLOR_CONFIDENCE = "rgba(59, 115, 185, 0.14)"
COLOR_COMMODITY_A = "#B87945"
COLOR_COMMODITY_B = "#7694B3"
COLOR_POSITIVE = "#2E8B68"
COLOR_WARNING = "#C98226"
COLOR_BENCHMARK = "#7B8794"
COLOR_GRID = "rgba(255, 255, 255, 0.05)"


def apply_industrial_theme(fig: go.Figure, title: str = "", height: int = 380) -> go.Figure:
    """Applies clean industrial Plotly layout styling."""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(color="#E9EEF4", size=14, family="IBM Plex Sans"),
            x=0.0,
            y=0.95
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#151E28",
        margin=dict(l=40, r=40, t=45, b=40),
        height=height,
        font=dict(color="#A2ADBA", family="IBM Plex Sans"),
        xaxis=dict(
            gridcolor=COLOR_GRID,
            showgrid=True,
            zerolinecolor=COLOR_GRID,
            tickfont=dict(size=10, color="#71808F")
        ),
        yaxis=dict(
            gridcolor=COLOR_GRID,
            showgrid=True,
            zerolinecolor=COLOR_GRID,
            tickfont=dict(size=10, color="#71808F")
        ),
        legend=dict(
            bgcolor="#101720",
            bordercolor="#293541",
            borderwidth=1,
            font=dict(color="#A2ADBA", size=10),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hoverlabel=dict(
            bgcolor="#1A2531",
            font_size=11,
            font_family="IBM Plex Mono",
            bordercolor="#293541"
        )
    )
    return fig


def plot_freight_trend(df: pd.DataFrame, title: str = "Freight Rate Outlook (₹ / tonne)") -> go.Figure:
    """Plots historical freight rates converted to INR per tonne."""
    fig = go.Figure()

    inr_rates = df["freight_rate"].apply(usd_to_inr)

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=inr_rates,
        mode="lines",
        name="Freight Rate (₹/t)",
        line=dict(color=COLOR_FORECAST, width=2.0),
        hovertemplate="<b>Date:</b> %{x|%d-%b-%Y}<br><b>Freight Rate:</b> ₹%{y:,.0f}/t<extra></extra>"
    ))

    if "freight_ma_14" in df.columns:
        inr_ma = df["freight_ma_14"].apply(usd_to_inr)
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=inr_ma,
            mode="lines",
            name="14-Day Moving Average",
            line=dict(color=COLOR_WARNING, width=1.4, dash="dash")
        ))

    return apply_industrial_theme(fig, title=title)


def plot_forecast_with_ci(
    historical_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    title: str = "Freight Rate Forecast (₹ / tonne)",
    lookback_days: int = 60
) -> go.Figure:
    """Plots historical rates along with future predicted rates and 95% CI bands in INR per tonne."""
    fig = go.Figure()

    hist_sub = historical_df.tail(lookback_days)
    hist_inr = hist_sub["freight_rate"].apply(usd_to_inr)

    fc_inr = forecast_df["predicted_freight_rate"].apply(usd_to_inr)
    lower_inr = forecast_df["lower_ci"].apply(usd_to_inr)
    upper_inr = forecast_df["upper_ci"].apply(usd_to_inr)

    # 1. Historical Actuals
    fig.add_trace(go.Scatter(
        x=hist_sub["date"],
        y=hist_inr,
        mode="lines",
        name="Historical Observations",
        line=dict(color=COLOR_HISTORICAL, width=1.8),
        hovertemplate="<b>Date:</b> %{x|%d-%b-%Y}<br><b>Historical Rate:</b> ₹%{y:,.0f}/t<extra></extra>"
    ))

    # 2. Upper CI Bound
    fig.add_trace(go.Scatter(
        x=forecast_df["date"],
        y=upper_inr,
        mode="lines",
        name="Upper 95% CI",
        line=dict(color="rgba(0, 0, 0, 0)", width=0),
        showlegend=False
    ))

    # 3. Lower CI Bound (Shaded Area)
    fig.add_trace(go.Scatter(
        x=forecast_df["date"],
        y=lower_inr,
        mode="lines",
        name="95% Confidence Interval",
        fill="tonexty",
        fillcolor=COLOR_CONFIDENCE,
        line=dict(color="rgba(0, 0, 0, 0)", width=0)
    ))

    # 4. Forecast Mean
    fig.add_trace(go.Scatter(
        x=forecast_df["date"],
        y=fc_inr,
        mode="lines+markers",
        name="Forecast",
        line=dict(color=COLOR_FORECAST, width=2.4),
        marker=dict(size=4, color=COLOR_FORECAST),
        hovertemplate="<b>Date:</b> %{x|%d-%b-%Y}<br><b>Forecast Rate:</b> ₹%{y:,.0f}/t<extra></extra>"
    ))

    return apply_industrial_theme(fig, title=title)


def plot_commodity_signals(df: pd.DataFrame) -> go.Figure:
    """Plots commodity price signals converted to INR per tonne."""
    fig = go.Figure()

    coal_inr = df["coking_coal_price"].apply(usd_to_inr)
    ore_inr = df["iron_ore_price"].apply(usd_to_inr)

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=coal_inr,
        mode="lines",
        name="Coking Coal (₹/t)",
        line=dict(color=COLOR_COMMODITY_A, width=1.8)
    ))

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=ore_inr,
        mode="lines",
        name="Iron Ore (₹/t)",
        line=dict(color=COLOR_COMMODITY_B, width=1.8),
        yaxis="y2"
    ))

    fig.update_layout(
        yaxis2=dict(
            title=dict(text="Iron Ore (₹/t)", font=dict(color=COLOR_COMMODITY_B, size=10)),
            overlaying="y",
            side="right",
            showgrid=False
        )
    )

    return apply_industrial_theme(fig, title="Commodity Price Signals (Demo Benchmark Converted to INR)")


def plot_congestion_and_vessels(df: pd.DataFrame) -> go.Figure:
    """Plots port congestion score and regional vessel availability count."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["port_congestion_score"],
        mode="lines",
        name="Port Congestion Index",
        line=dict(color=COLOR_WARNING, width=1.8)
    ))

    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["vessel_availability_count"],
        mode="lines",
        name="Vessel Count",
        line=dict(color=COLOR_POSITIVE, width=1.8),
        yaxis="y2"
    ))

    fig.update_layout(
        yaxis2=dict(
            title=dict(text="Vessel Count", font=dict(color=COLOR_POSITIVE, size=10)),
            overlaying="y",
            side="right",
            showgrid=False
        )
    )

    return apply_industrial_theme(fig, title="Port Congestion Index & Vessel Availability")


def plot_backtest_cost_comparison(res_df: pd.DataFrame) -> go.Figure:
    """Plots simulated cost comparison in INR."""
    fig = go.Figure()

    bm_inr = res_df["benchmark_simulated_cost"].apply(usd_to_inr)
    fiq_inr = res_df["freightiq_simulated_cost"].apply(usd_to_inr)

    fig.add_trace(go.Bar(
        x=res_df["decision_date"],
        y=bm_inr,
        name="Benchmark Strategy",
        marker_color=COLOR_BENCHMARK
    ))

    fig.add_trace(go.Bar(
        x=res_df["decision_date"],
        y=fiq_inr,
        name="FreightIQ Strategy",
        marker_color=COLOR_FORECAST
    ))

    fig.update_layout(barmode="group")
    return apply_industrial_theme(fig, title="Simulated Logistics Cost Comparison per Decision Period (₹)")


def plot_cumulative_simulated_savings(res_df: pd.DataFrame) -> go.Figure:
    """Plots cumulative simulated cost difference curve in INR."""
    fig = go.Figure()

    cum_savings_usd = res_df["simulated_cost_difference"].cumsum()
    cum_savings_inr = cum_savings_usd.apply(usd_to_inr)

    fig.add_trace(go.Scatter(
        x=res_df["decision_date"],
        y=cum_savings_inr,
        mode="lines+markers",
        name="Cumulative Simulated Cost Difference (₹)",
        line=dict(color=COLOR_POSITIVE, width=2.2),
        fill="tozeroy",
        fillcolor="rgba(46, 139, 104, 0.12)",
        marker=dict(size=4, color=COLOR_POSITIVE)
    ))

    return apply_industrial_theme(fig, title="Cumulative Simulated Cost Difference Curve (₹)")
