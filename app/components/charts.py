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

# Light SaaS Palette
COLOR_HISTORICAL = "#64748B"
COLOR_FORECAST = "#1667D9"
COLOR_CONFIDENCE = "rgba(22, 103, 217, 0.10)"
COLOR_COMMODITY_A = "#D97706"
COLOR_COMMODITY_B = "#0284C7"
COLOR_POSITIVE = "#10B981"
COLOR_WARNING = "#F59E0B"
COLOR_BENCHMARK = "#94A3B8"
COLOR_GRID = "#F1F5F9"


def apply_industrial_theme(fig: go.Figure, title: str = "", height: int = 380, theme: Optional[str] = None) -> go.Figure:
    """Applies clean SaaS Plotly layout styling matching active Light / Dark theme."""
    if theme is None:
        try:
            import streamlit as st
            theme = st.session_state.get("fiq_theme", "light")
        except Exception:
            theme = "light"

    is_dark = (theme == "dark")

    bg_plot = "#151A22" if is_dark else "#FFFFFF"
    text_color = "#F5F7FA" if is_dark else "#111827"
    subtext_color = "#98A2B3" if is_dark else "#6B7280"
    grid_color = "#2A3240" if is_dark else "#F1F5F9"
    legend_bg = "#151A22" if is_dark else "#FFFFFF"
    legend_border = "#2A3240" if is_dark else "#E5E7EB"

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(color=text_color, size=14, family="Inter"),
            x=0.0,
            y=0.95
        ) if title else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=bg_plot,
        margin=dict(l=40, r=40, t=35 if title else 20, b=40),
        height=height,
        font=dict(color=subtext_color, family="Inter"),
        xaxis=dict(
            gridcolor=grid_color,
            showgrid=True,
            zerolinecolor=grid_color,
            tickfont=dict(size=10, color=subtext_color)
        ),
        yaxis=dict(
            gridcolor=grid_color,
            showgrid=True,
            zerolinecolor=grid_color,
            tickfont=dict(size=10, color=subtext_color)
        ),
        legend=dict(
            bgcolor=legend_bg,
            bordercolor=legend_border,
            borderwidth=1,
            font=dict(color=text_color, size=10),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hoverlabel=dict(
            bgcolor=legend_bg,
            font_size=11,
            font_family="Inter",
            bordercolor=legend_border,
            font_color=text_color
        )
    )
    return fig



def plot_freight_trend(df: pd.DataFrame, title: str = "") -> go.Figure:
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
    title: str = "",
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

    return apply_industrial_theme(fig, title="")


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

    return apply_industrial_theme(fig, title="")


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
    return apply_industrial_theme(fig, title="")


def plot_cumulative_simulated_savings(res_df: pd.DataFrame) -> go.Figure:
    """Plots cumulative simulated cost difference curve in INR."""
    fig = go.Figure()

    cum_savings_usd = res_df["simulated_cost_difference"].cumsum()
    cum_savings_inr = cum_savings_usd.apply(usd_to_inr)

    fig.add_trace(go.Scatter(
        x=res_df["decision_date"],
        y=cum_savings_inr,
        mode="lines+markers",
        name="Cumulative Cost Difference (₹)",
        line=dict(color=COLOR_POSITIVE, width=2.2),
        fill="tozeroy",
        fillcolor="rgba(16, 185, 129, 0.10)",
        marker=dict(size=4, color=COLOR_POSITIVE)
    ))

    return apply_industrial_theme(fig, title="Difference Curve (₹)")

