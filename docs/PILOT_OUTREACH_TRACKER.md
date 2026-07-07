# Pilot Outreach Tracker

## Purpose

Use `docs/templates/pilot_target_tracker.csv` to manage a small internal
shortlist of placeholder or approved pilot targets. The tracker supports
manual prioritization only. It does not create customer records, automate
outreach, calculate customer-specific outcomes, or change product behavior.

FlexSignal AI v0.1 remains read-only decision support. Pilot conversations
must use public price signal only, describe an indicative gross opportunity
signal only, avoid customer value claims, and require human review.

## How To Use The CSV Tracker

1. Add a placeholder row for each target under review.
2. Keep `organization_placeholder` generic until a real organization is
   approved for direct outreach.
3. Select one `customer_category`:
   `renewable_producer_developer`, `flexible_energy_consumer`,
   `grid_distribution_system_operator`, or `hybrid_site`.
4. Fill the qualitative fields before scoring:
   `price_area_relevance`, `suspected_flexibility_type`,
   `likely_data_available`, and `operational_contact_known`.
5. Score each scoring column from `1` to `5`.
6. Set `total_score` to the manual sum of the seven score columns.
7. Assign `priority_tier` using the target-shortlist guidance:
   `tier_1_contact_first`, `tier_2_keep_warm`, or `tier_3_later_not_now`.
8. Update `outreach_stage` as the target moves through the manual process.
9. Keep `do_not_claim_notes` explicit before any contact is made.

Do not add raw customer data, personal contact details, secrets, credentials,
control-system details, or unapproved real organization names to the tracker.

## Outreach Stages

Use one of these values in `outreach_stage`:

- `identified`
- `researched`
- `ready_to_contact`
- `contacted`
- `replied`
- `meeting_booked`
- `data_requested`
- `data_received`
- `pilot_review`
- `closed_no_fit`

Stage guidance:

| Stage | Meaning |
| --- | --- |
| `identified` | Placeholder target has been added. |
| `researched` | Public or approved internal research has been summarized. |
| `ready_to_contact` | Required notes and safe wording have been reviewed. |
| `contacted` | Outreach has been sent through an approved channel. |
| `replied` | Target has responded. |
| `meeting_booked` | First call has been scheduled. |
| `data_requested` | Safe data request has been shared after human review. |
| `data_received` | Data has been received through an approved process. |
| `pilot_review` | Read-only pilot analysis is under human review. |
| `closed_no_fit` | Target is not a fit for v0. |

## First-Call Goal

The first call should test whether a limited read-only pilot review is useful
and safe. The call should confirm the operational question, likely data
availability, DK1/DK2 relevance, human reviewer, and boundaries before any
data request is sent.

Do not present the pilot as verified customer value, automatic control,
dispatch, activation, or a guaranteed financial outcome.

## First-Call Questions

- What DK1/DK2 exposure is relevant to your operations or planning?
- Which historical data could you share for a read-only pilot review?
- Do you have flexible load, flexible production, curtailment history, storage,
  or other flexibility-relevant context?
- Which operational constraints would affect interpretation of candidate
  windows?
- Who is the decision owner for approving a limited pilot review?
- Would you be willing to share anonymized historical data for human-reviewed
  analysis?

Customer-specific assessment requires tariff, constraints, operating costs,
and human validation.

## Safe Wording Reminders

Use these phrases consistently:

- Read-only pilot analysis.
- Public price signal only.
- Indicative gross opportunity signal only.
- Not a customer value claim.
- Human review required.

Also state that FlexSignal AI v0.1 is read-only decision support and does not
perform automatic control, dispatch, activation, live control signals, or
asset integration.

## What Not To Say

- No verified customer savings.
- No profit or revenue claim.
- No guaranteed value.
- No automatic control.
- No dispatch.
- No activation.

If the conversation requires any of the above claims, close the target as
`closed_no_fit` for v0.
