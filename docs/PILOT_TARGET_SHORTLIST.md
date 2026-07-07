# Pilot Target Shortlist

## Purpose

This document defines a simple v0 process for identifying and prioritizing
the first pilot targets before more product development.

The shortlist is for internal planning only. It should use placeholders until
a real organization has been approved for direct outreach. FlexSignal AI v0.1
remains read-only decision support, uses public price signal only, and
requires human review before any customer-facing interpretation is shared.

## Why Target Selection Comes First

Pilot target selection comes before more product development because the next
useful product questions depend on real operational context:

- Which DK1/DK2 exposure matters to the target?
- Which historical data can the target share safely?
- Which flexibility or production constraints are relevant?
- Which operational contact can validate whether the analysis is meaningful?
- Which claims must be avoided in outreach and review?

The goal is to learn whether the current public-price-signal workflow can
support a useful read-only pilot conversation. It is not to design control
features, automate operational decisions, or build additional infrastructure
before the pilot need is clear.

## Target Customer Categories

### Renewable Producer/Developer

Examples include renewable asset owners, renewable developers, and site
operators with wind, solar, storage, PtX, or hybrid generation exposure.

Potential pilot fit:

- DK1/DK2 production or generation data is available.
- Operational context exists for curtailment, negative-price periods, outage
  periods, or export constraints.
- A human operational contact can review whether public risk windows align
  with historical site conditions.

### Flexible Energy Consumer

Examples include industrial loads, heat or process loads, cold storage, data
centers, electric boilers, district heating, PtX consumption, campuses, and
buildings with meaningful flexible demand.

Potential pilot fit:

- DK1/DK2 load, operating schedule, or flexible energy data is available.
- Runtime, comfort, process, storage, ramp, or lead-time constraints can be
  described.
- A human operational contact can review whether candidate windows are
  technically plausible.

### Grid/Distribution/System Operator

Examples include grid planning, distribution, system, or local flexibility
teams working with aggregated local areas.

Potential pilot fit:

- Aggregated local load, generation, or area-balance data can be shared safely.
- Known bottleneck, constraint, outage, or planning context can be described.
- A human reviewer can explain whether public DK1/DK2 price-signal windows are
  relevant to local planning questions.

### Hybrid Site

Examples include sites combining production, flexible consumption, storage,
PtX, or site-level net import/export.

Potential pilot fit:

- Separate production, consumption, storage, and flexibility time series can
  be shared safely.
- Site mode, operating windows, and technical constraints can be explained.
- A human reviewer can validate whether the indicative gross opportunity
  signal is operationally interpretable.

## Ideal Pilot Profile

An ideal pilot target has:

- Clear DK1 or DK2 exposure.
- Historical data available in CSV or another easy-to-review format.
- A plausible flexibility, production, curtailment, or planning question.
- A named operational role or team that can validate assumptions.
- Permission to share anonymized historical data for read-only analysis.
- A short decision path for agreeing to a limited pilot review.
- Compliance and safety expectations that fit the v0.1 read-only boundary.
- Interest in learning from an indicative gross opportunity signal without
  treating it as a customer value claim.

Customer-specific assessment requires tariff, constraints, operating costs,
and human validation.

## Bad-Fit/Red-Flag Profile

A target is a poor fit for v0 if:

- The expected pitch depends on verified customer value.
- The target expects automatic control, dispatch, activation, live control
  signals, or direct asset integration.
- No operational reviewer is available.
- Data cannot be shared safely, even in anonymized or aggregated form.
- The use case requires critical operational availability.
- The target needs regulated advice, procurement recommendations, or
  customer-specific outcome guarantees.
- The pilot cannot be explained as public price signal only and read-only
  decision support.

## Scoring Model

Score each target from `1` to `5` for each dimension.

| Score | Meaning |
| ---: | --- |
| 1 | Weak fit or unknown. |
| 2 | Some fit, but major gaps remain. |
| 3 | Plausible fit with manageable gaps. |
| 4 | Strong fit with few gaps. |
| 5 | Excellent fit and ready for focused outreach. |

Scoring dimensions:

| Dimension | What To Check |
| --- | --- |
| DK1/DK2 relevance | The target has clear exposure to Danish price areas. |
| Data availability | Historical data is likely available and shareable. |
| Flexibility relevance | The target has relevant flexible load, production, curtailment, storage, planning, or hybrid-site questions. |
| Operational contact availability | A human reviewer or team can validate interpretation. |
| Decision speed | The target can quickly decide on a limited read-only pilot review. |
| Compliance/safety fit | The target accepts the v0.1 read-only boundary and safe data handling. |
| Commercial learning value | The target can teach the team which product questions matter next without requiring new unsafe scope. |

Suggested interpretation:

- `30-35`: strong candidate.
- `23-29`: plausible candidate, research before outreach.
- `16-22`: weak candidate, keep for later review.
- `7-15`: not a v0 priority.

## Suggested Priority Tiers

| Tier | Label | Use When |
| --- | --- | --- |
| Tier 1 | Contact first | High score, clear data path, clear operational reviewer, safe pitch. |
| Tier 2 | Keep warm | Plausible fit, but one or more gaps need research before outreach. |
| Tier 3 | Later/not now | Low score, unclear data, unclear reviewer, or poor v0 safety fit. |

## Required Notes Before Contacting

Before moving a target to `ready_to_contact`, write notes for:

- What problem might they have?
- What data might they have?
- What would make the pilot useful?
- What must we avoid claiming?

The notes should explicitly state that the pilot is read-only decision support,
uses public price signal only, reports an indicative gross opportunity signal
only, is not a customer value claim, and requires human review.

## Go/No-Go Rule

Do not contact a target if the pitch requires claiming verified customer value,
automated control, dispatch, activation, or a guaranteed financial outcome.

Proceed only when the outreach can stay within read-only decision support,
public price signal only, human review required, and no automatic control,
dispatch, activation, live control signals, or asset integration.
