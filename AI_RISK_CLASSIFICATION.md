# AI Risk Classification

## v0.1 Classification

FlexSignal AI `v0.1` is decision support only. It may forecast, visualize, explain, and recommend, but it must not autonomously control electricity consumption or send control signals to any assets, plants, devices, or energy infrastructure.

## No Autonomous Control

- No automatic activation.
- No dispatch instructions sent to infrastructure.
- No closed-loop control.
- No critical operational dependency in `v0.1`.

## Human-in-the-Loop Requirement

All recommendations require human review before any operational action is taken outside the platform. Users remain responsible for interpreting recommendations, validating assumptions, and deciding whether to act.

## High-Risk-Ready Design Principle

Although `v0.1` is not intended to be a critical operational system, the platform should be designed with traceability, auditability, transparency, security, and human oversight so future risk assessments are easier to perform.

## LLM Limitations

- LLMs may be used for explanation, reporting, and recommendation text.
- LLMs must not be the primary forecasting engine.
- LLMs must not be the sole decision-making component.
- LLM output should be grounded in forecast outputs and source data.
- LLM output should be reviewable and auditable.

## Key Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Incorrect forecast | Backtesting, monitoring, confidence scoring, and clear limitations |
| Incorrect recommendation | Human review, audit logs, conservative recommendation wording |
| Data quality failure | Source validation, ingestion checks, data freshness monitoring |
| Model drift | Scheduled evaluation and drift monitoring |
| Overreliance on AI text | Clear UI labels, human-in-the-loop process, source references |
| Accidental control scope expansion | No control interfaces, agent instructions, security reviews |
| Security compromise | Entra ID, Key Vault, least privilege, logging, incident response |

