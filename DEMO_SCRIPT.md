# FreightIQ Demo Talking Points

Honest framing for anyone presenting or demonstrating this prototype.

---

## What FreightIQ Is

FreightIQ is a **decision-support prototype** that shows how statistical freight rate models,
Monte Carlo scenario simulation, and structured cost accounting could be combined to help
a bulk cargo procurement team think through charter timing decisions.

It is **not** a production system, a licensed data service, or a commercial chartering tool.

---

## Honest Framing — Use These Words

| Instead of saying... | Say this instead |
|---|---|
| "The AI predicts freight rates accurately" | "The time-series model (SARIMA / Naive Baseline) generates a probabilistic forecast estimate on synthetic demo data" |
| "LP finds the global optimum" | "The optimizer enumerates charter date candidates and selects the lowest simulated-cost option under the configured assumptions" |
| "83% real savings" | "In historical-style simulation on synthetic demo data, the system matched or outperformed an immediate-charter benchmark in a portion of simulated decision windows" |
| "Robustness score means it always works" | "The robustness score measures the fraction of Monte Carlo draws on synthetic data that keep the same recommendation — a relative stability indicator, not a real-market guarantee" |
| "Industry-grade / production-ready" | "This is a functional prototype demonstrating the decision workflow" |
| "Validated on real data" | "All metrics are computed on synthetic demonstration data seeded from realistic statistical distributions, except external weather validation" |

---

## What the Demo Shows Well

- **Workflow completeness**: the full procurement decision loop from signal ingestion → forecast → cost model → scenario lab → PDF export is connected end-to-end.
- **Scenario sensitivity**: the scenario lab shows how perturbations affect candidate selection and logistics cost.
- **Audit trail**: recorded manual overrides and key decision saves are logged with provenance.
- **Connector architecture**: the integration layer is designed to structure synthetic data and live API feeds without changing the decision engine.

---

## What the Demo Does NOT Show

- Real Baltic Exchange freight rate data.
- Real AIS vessel supply or port congestion readings.
- Calibrated cost weights — demurrage rates, congestion penalties, and risk factors use illustrative defaults.
- Real-market backtest results — simulation win-rate figures are on synthetic data only.
- A licensed or compliant data pipeline for production deployment.

---

## Correct Way to Present Key Metrics

**Forecast MAE / RMSE / MAPE**
> "The model's demo-series error is computed on the synthetic demonstration dataset, not a claim about real-market accuracy."

**Simulated Win Rate**
> "In the simulation backtest on synthetic data, the system's recommended charter date is compared to an immediate-charter benchmark. This is a relative indicator on demo data, not a guaranteed savings figure."

**Decision Robustness Score**
> "Monte Carlo draws on synthetic futures evaluate recommendation stability under parameter uncertainty in the demo, not a real-world probability."


---

## Deployment Requirements Before Real Use

1. Licensed data feeds: Baltic Exchange freight indices, MarineTraffic AIS, commodity pricing APIs.
2. Calibration: cost weights (demurrage, congestion, risk) must be fit to real shipment records and contractual terms.
3. Forecast validation: models must be re-trained and validated on real historical data.
4. Legal review: charter recommendations must be confirmed by a licensed chartering broker.
5. IT integration: connector authentication, data refresh scheduling, and audit logging must be configured for the live environment.
