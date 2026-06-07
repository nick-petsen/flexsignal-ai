# Agent Instructions

These instructions apply to Codex and future coding agents working on FlexSignal AI.

## Scope Discipline

- Build small modules one at a time.
- Do not expand scope without explicit instruction.
- Keep the MVP simple.
- Preserve the `v0.1` read-only decision-support boundary.

## Prohibited in v0.1

- Do not implement automatic control.
- Do not implement live control signals.
- Do not implement dispatch, activation, or closed-loop control workflows.
- Do not connect the platform to assets, plants, devices, or energy infrastructure for control purposes.
- Do not make the platform a critical operational system.

## AI and Forecasting

- Keep LLM usage limited to explanation and reporting.
- Do not use LLMs as the primary forecasting engine.
- Do not use LLMs as the sole decision-making component.
- Prefer simple, testable, explainable baseline models first.

## Engineering Priorities

- Prioritize tests, documentation, and security.
- Use clear module boundaries.
- Keep auditability and traceability in mind.
- Avoid premature infrastructure or schema work unless explicitly requested.
- Document assumptions and limitations when adding new behavior.

