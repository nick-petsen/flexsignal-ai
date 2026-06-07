# Model Card

## Model Overview

The first FlexSignal AI model must be simple, transparent, and easy to backtest. It should support read-only decision support for DK1 and DK2 surplus-risk forecasting.

Suggested initial approaches:

- Rules-based baseline
- Statistical model
- Regression model
- XGBoost
- LightGBM

LLMs must not be used as the primary forecasting engine or the sole decision-making component.

## Intended Use

The model estimates surplus-risk windows and related decision-support information for human review. It is not intended for automatic control or critical operations in `v0.1`.

## Input Features

Candidate input features include:

- DK1/DK2 electricity prices
- Historical consumption
- Historical production by type
- Wind production indicators
- Solar production indicators
- Import/export flow indicators
- Weather observations and forecasts
- Calendar features
- Time-of-day and seasonality features
- Data freshness and quality indicators

## Output Format

Each forecast output should include:

- Surplus risk: low, medium, or high
- Expected time window
- Confidence score
- Recommended action for human review
- Estimated economic potential
- Key drivers or explanation references
- Model version and generation timestamp

## Model Limitations

- Forecasts may be wrong during unusual market, weather, or grid conditions.
- Data delays or source errors may reduce reliability.
- Simple models may miss complex system dynamics.
- Confidence scores are estimates and require validation.
- Recommendations are not instructions for automatic activation.

## Evaluation and Backtesting Plan

Planned evaluation should include:

- Historical backtesting by DK1 and DK2.
- Precision and recall for surplus-risk classification.
- False positive and false negative analysis.
- MAE and RMSE where numeric forecasts are produced.
- Calibration review for confidence scores.
- Error analysis by season, time of day, and weather regime.
- Comparison against simple baseline rules.

