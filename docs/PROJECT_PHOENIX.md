# Project Phoenix: implemented decision-intelligence slice

## Existing project assessment

FreightIQ already had synthetic route histories, SARIMA and naive forecasts, a vessel/date cost optimizer, a Scenario Lab, Decision Twin simulations, sensitivity and walk-forward backtests, local SQLite decision versions, a Plotly web interface, and an illustrative Voyage Intelligence map. Forecast, cost and scenario computations live in Python; the browser presents their outputs. The local Node server proxies `/api/*` to FastAPI.

The missing part of the requested demonstration was a fair side-by-side comparison of charter policies with inspectable downside costs and a numerical break-even question. Scenario Lab also submitted the Hay Point route and cargo even when another route was selected. These gaps were addressed in this slice.

## Working innovations

- **Decision Arena:** compares early charter, optimizer forecast window, a deferred date benchmark, and a downside-aware action. All four are evaluated with the existing cost evaluator on the *same* seeded synthetic future draws. Policies can choose the same action; this is shown, not hidden. The downside-aware action minimizes CVaR90 over a feasible shortlist, and the UI plots mean cost against CVaR90 with Pareto flags.
- **Future replay subset:** the slider inspects one shared simulated future at a time across policies. It is a cost-outcome replay, not a vessel timeline or live voyage simulation.
- **INR impact and explanation:** the arena reports selected versus earliest modeled savings, selected versus deferred cost of waiting, and a cost-component comparison. The counterfactual uses repeated calls to the optimizer to find a selected-date freight-rate increase that changes the winning charter date.
- **What-if integration:** Scenario Lab now uses the active shipment route and cargo. The demurrage control is exposed, and destination port shocks match a route port ID as well as its name. Its unshocked confidence comparison now calculates both sides, instead of using a fixed baseline.
- **Evidence export:** the downloadable Decision Arena PDF contains the same strategy comparisons, cost drivers, counterfactual, experiment settings, and limitations shown in the UI.

The prior Voyage Intelligence map remains explicitly illustrative. The new work does not create tracking data, verified route geometry, commercial port observations, or autonomous booking actions.

## Calculation and data integrity

`backend/strategy_arena.py` calls `optimize_charter_timing` for the baseline candidate set and `evaluate_charter_candidate` for each simulated outcome. Operational forecast context is the **last synthetic observation for the selected route**, carried forward; it is not a newly forecast port or weather condition. Synthetic uncertainty scales are standard deviations of the last 90 daily changes, with bounded floors and caps. The draws are independent across the six modeled factors and shared across policies. They do not encode real-world correlations, temporal market dynamics, or calibrated probabilities.

Infeasible outcomes are excluded from the *shared feasible set* for cost comparison. Each strategy separately reports its feasible share across all sampled futures. The sample seed, count, common feasible count, forecast period, source history period, model name, and an uncertainty description travel with the API and PDF result. The presentation conversion is a fixed demo assumption of **INR 84 per USD**, not a live exchange rate. The model only includes components supported by the current evaluator: freight, demurrage, port/congestion, and weather/event penalty. It does not claim a complete landed cargo cost.

The counterfactual tests a single selected-date freight increase in the interval 0–50%, holding other modeled inputs fixed. It uses 20 bisection iterations, rounds upward to a displayed 0.01% step, and verifies that the reported step itself changes the optimizer's charter date. It does not prove that every market perturbation would have the same effect. CVaR90 is the mean cost in the highest-cost decile of shared feasible synthetic futures.

## Local demonstration flow

1. Start FastAPI and the Node web server using the commands in the README; open `http://localhost:3000`.
2. In **Decision Arena**, select **Gladstone → Paradip**, **Coking Coal**, and **75,000 tonnes**, then run the comparison.
3. Inspect the cost/downside frontier, policy table, cost drivers, counterfactual, and future replay slider. If policies converge on the same action, explain that their assumptions led to the same date and vessel.
4. Choose **Configure disruption**. In Scenario Lab, raise destination congestion or use **East Coast Disruption**, then run the simulation. Compare baseline and stressed recommendation and cost.
5. Choose **Compare strategies under this scenario**. Inspect the new shared-future distributions and export the evidence PDF.

## Validation

Run `python -m pytest -q`, `npm test`, and `npm run build`. New tests cover route port shock propagation without mutating the baseline, reproducible shared samples, financial component arithmetic, invalid simulation input, unshocked confidence consistency, and PDF contents. Browser checks exercised route changes and the future replay slider.

## Remaining work

The broader Phoenix brief asks for calibrated real-market forecasts, anomaly detection, a voyage-stage timeline, decision snapshot replay, and a full executive report covering all modules. These require additional data, model validation, and/or product work. The current PDF is a **Decision Arena evidence report**, not a complete end-to-end intelligence dossier. Risk labels and sampled win shares should not be treated as validated likelihoods or commercial advice.
