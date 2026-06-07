# FlexSignal AI Specification

## Product Goal

FlexSignal AI helps users understand and act on electricity system flexibility opportunities in Denmark by forecasting surplus risk and producing transparent, human-reviewed recommendations for DK1 and DK2.

The first release is read-only decision support. It is not an operational control system.

## Target Users

- Energy analysts
- Flexibility aggregators
- Industrial energy managers
- Operational planning teams
- Commercial teams evaluating flexible consumption opportunities

## Core Capabilities

- Forecast likely surplus electricity periods for DK1 and DK2.
- Classify surplus risk as low, medium, or high.
- Estimate relevant time windows and confidence levels.
- Recommend human-reviewed actions.
- Explain forecast drivers and recommendation rationale.
- Log recommendations, explanations, inputs, and user review events.

## MVP Features

- DK1 and DK2 market-area focus.
- Read-only dashboards and forecast views.
- Basic forecast model using rules, statistics, regression, XGBoost, or LightGBM.
- Recommendation text for human review.
- Confidence scoring.
- Estimated economic potential for each forecast window.
- Audit trail for generated recommendations.
- Documentation-first project structure.

## Non-Functional Requirements

- Secure secret storage through Azure Key Vault.
- Authentication through Microsoft Entra ID.
- Observability through Application Insights and Log Analytics.
- Database suitable for time-series data using PostgreSQL and TimescaleDB.
- Clear separation between forecasting, explanation, and presentation layers.
- Human-in-the-loop workflows for all recommendations.
- No direct connection to control interfaces in `v0.1`.

## Out of Scope for v0.1

- Automatic dispatch, activation, curtailment, or consumption control.
- Live control signals to assets, plants, devices, or grid infrastructure.
- Critical operational dependencies.
- LLM-based primary forecasting.
- LLM-only decision-making.
- Production-grade infrastructure deployment.
- Database schema implementation.
- Backend and frontend application implementation.

