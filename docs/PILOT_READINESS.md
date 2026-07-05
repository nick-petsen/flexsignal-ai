# Customer Pilot Readiness

## Purpose

N&O Predict / FlexSignal AI has a public DK1/DK2 backtest that shows the
deterministic signal can identify historical surplus-risk windows at the
public system and market level.

For pilot readiness, that public backtest is evidence that the signal works at
the public DK1/DK2 system and market level. It is not evidence of
customer-specific value by itself.

A customer pilot has a different purpose: it tests whether those public signal
windows are relevant for a specific customer when compared with that
customer's load, assets, constraints, price context, and operational reality.
The customer pilot is the evidence step for whether the signal creates
validated potential value for that specific customer.

The pilot remains read-only decision support. It prepares analysis and
recommendations for human review only.

The customer-facing intake template is available in
[PILOT_INTAKE_TEMPLATE.md](PILOT_INTAKE_TEMPLATE.md). A structured request
sheet is available at
[templates/customer_pilot_data_request.csv](templates/customer_pilot_data_request.csv).
Use these materials after the public proof-of-work report when requesting
customer data for a read-only pilot.

## Pilot Scope

- Read-only analysis.
- No automatic control.
- No dispatch.
- No activation.
- No live control signals.
- No asset integration.
- Human review required for all recommendations.

## Required Customer Data

| Data category | Examples | Preferred format | Required/optional | Why it is needed |
| --- | --- | --- | --- | --- |
| Historical electricity load/consumption time series | Site import/export, process load, metered consumption | CSV, Parquet, or Excel with timestamp, timezone, value, unit, and meter/site id | Required | Compares public risk windows with actual customer demand and timing. |
| Asset/flexible load capacity in MW/MWh | Flexible process load, thermal storage, battery capacity, interruptible load range | Structured table with asset name, max MW, usable MWh, duration, and site id | Required | Estimates the flexible energy volume that could be considered during candidate windows. |
| Operating constraints | Minimum run times, ramp limits, product quality limits, comfort limits, restart limits | Structured table or documented operating rules | Required | Filters public signal windows against practical operating limits. |
| Operating schedule or availability windows | Production shifts, opening hours, batch windows, planned idle periods | Calendar export, CSV, or table with start/end timestamps and timezone | Required | Identifies when flexibility could realistically be reviewed. |
| Tariff/price agreement context | Spot exposure, fixed-price components, grid tariffs, taxes, fees, imbalance terms | Contract summary or structured tariff table | Required | Determines which price or opportunity signal is economically relevant. |
| Historical production/consumption decisions if available | Previous curtailment, batch timing, load-shift decisions | CSV, operations log export, or annotated timeline | Required if available | Helps validate whether candidate windows align with prior operational choices. |
| Site/location/price area mapping | Site address, metering point, DK1/DK2 price area, grid connection context | Site list or mapping table | Required | Ensures the public DK1/DK2 signal is matched to the right customer area. |
| Contact person for operational interpretation | Operations lead, energy manager, production planner | Name, role, email, phone, review availability | Required | Provides human validation of assumptions, constraints, and interpretation. |
| Asset telemetry | State of charge, temperature, process state, availability flags | Time series export with timestamps and units | Optional | Improves validation of actual asset availability during candidate windows. |
| Planned maintenance | Maintenance windows, outages, known downtime | Calendar export or table with start/end timestamps | Optional | Excludes windows where flexibility was unavailable for non-market reasons. |
| Internal forecast | Customer load, production, or availability forecasts | CSV, Parquet, API export, or forecast report | Optional | Compares public signal timing with the customer's own planning view. |
| Curtailment/constraint logs | Grid constraints, local constraints, process interruptions | Log export or annotated timeline | Optional | Explains why apparently attractive windows may not have been actionable. |
| Operational notes | Shift notes, planning notes, exceptions, known anomalies | Text export, spreadsheet, or reviewed notes | Optional | Adds context for interpreting false positives and missed opportunities. |
| Commercial settlement assumptions | Settlement period, currency, fees, internal allocation rules | Contract summary or structured assumptions table | Optional | Supports a more precise customer-specific potential estimate when validated. |

## Minimum Pilot Dataset

A practical first pilot can start with:

- 3-12 months of historical hourly or sub-hourly load data.
- Confirmed DK1/DK2 price area.
- Rough flexible MWh estimate.
- Known operational constraints.
- Tariff or price context if available.

This minimum dataset supports an initial read-only comparison. It does not
support customer-specific conclusions until the data has been checked with the
customer reviewer.

## Pilot Success Criteria

The pilot should be evaluated with measurable criteria:

- Number of public risk windows matched to customer availability.
- Number of actionable candidate windows after constraints are applied.
- False positive review rate.
- Missed opportunity review.
- Estimated gross market opportunity per flexible MWh.
- Customer-specific potential only after customer data is validated.

## Economic Potential Method

The pilot estimates economic potential in a controlled, auditable sequence:

1. The public DK1/DK2 signal identifies historical surplus-risk or
   price-opportunity windows.
2. Customer data estimates usable flexible MWh during those windows.
3. Gross opportunity equals flexible MWh multiplied by the relevant
   price/opportunity signal.
4. Customer-specific value requires validated tariff terms, operating
   constraints, operating costs, and customer review.

This method is an estimate for decision support. It must be reviewed with the
customer before being used for planning.

## Deliverables

- Pilot input checklist.
- Public-vs-customer signal comparison.
- Candidate opportunity windows.
- Customer-specific potential estimate if the validated data supports it.
- Final pilot report.
- Recommendation for next phase.

## Security And Data Handling

- Use least-privilege access for all customer data.
- Do not commit secrets to the repository.
- Do not commit customer data to git.
- Minimize collected data to what the pilot needs.
- Delete or anonymize customer data after the pilot unless the contract says
  otherwise.
- Keep customer data separate from public demo artifacts.

## Human Oversight

- All outputs are decision support.
- A customer reviewer must approve interpretation of results.
- No automatic operational action is performed or implied.

## Out Of Scope

- Production deployment.
- Autonomous control.
- Dispatch or activation.
- Live asset integration.
- Guaranteed savings.
- Financial advice.
- Grid operation responsibility.
