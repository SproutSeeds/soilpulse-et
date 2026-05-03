# Near-Term Validation And Mission Hardening

Last updated: 2026-05-03

This document defines the practical next phase for SoilPulse-ET after the Phase
1 submission. The goal is to keep the pitch honest: the core onboard triage
pattern is buildable now, while validation and mission hardening are the next
work.

## What We Have Now

Claim level: demonstrated Phase 1 concept artifact.

- A reproducible onboard triage policy that scores candidate land tiles and
  chooses `priority_chip`, `feature_summary`, or `defer`.
- A constrained demo budget covering downlink, packet count, processing time,
  and energy.
- A NASA data anchor: ECOSTRESS L3T JET V002, DOI
  `10.5067/ECOSTRESS/ECO_L3T_JET.002`.
- A small ECOSTRESS/AppEEARS-derived knowledge-gap row that proves data lineage,
  not stress-event validation.
- Synthetic HLS vegetation and terrain support fixtures that show the intended
  data contract for future ingestion.
- A paper, reproducible code path, and video story aligned around the same
  architecture.

## What We Are Working Toward Next

Claim level: near-term validation and mission-hardening roadmap.

The next phase is not inventing the idea. It is turning the current concept
artifact into a better-validated mission prototype.

## Workstream 1: Real-Data Validation

Purpose:

```text
Replace "policy demo works on a hybrid fixture" with "policy behavior is tested
against multiple real event and non-event windows."
```

Near-term tasks:

- Add more ECOSTRESS windows across hot / dry periods and calmer comparison
  periods.
- Integrate real HLS vegetation-index data instead of synthetic HLS support
  fixtures.
- Add real terrain context from NASADEM / SRTM-style sources where useful.
- Label outcomes as stress candidate, knowledge gap, obscured, or normal
  comparison.
- Report false positives, misses, and ambiguous cases instead of only wins.

Exit criterion:

```text
The policy has been exercised against real multi-window data with documented
successes, failures, and ambiguous cases.
```

## Workstream 2: User Calibration

Purpose:

```text
Tune chip / summary / defer thresholds against the actual decision needs of
irrigation districts, groundwater agencies, or conservation providers.
```

Near-term tasks:

- Pick one pilot user persona and one pilot geography.
- Define what counts as a useful alert or useful deferred observation.
- Tune weights for ET deficit, vegetation change, cloud, revisit age, user
  priority, and confidence.
- Add user-priority scenarios: water-scarce season, field-team overload, cloudy
  window, low-confidence signal.

Exit criterion:

```text
The policy thresholds are tied to explicit user priorities rather than only
developer-chosen scores.
```

## Workstream 3: 6U Mission Hardening

Purpose:

```text
Map the software concept onto a specific 6U CubeSat planning stack without
claiming flight readiness.
```

Near-term tasks:

- Select candidate onboard compute classes and memory / storage assumptions.
- Sketch power modes for sensing, processing, idle, and downlink.
- Add a contact-window / downlink-rate model.
- Define thermal, radiation, fault-handling, and watchdog assumptions at concept
  level.
- Clarify what runs onboard versus what remains on the ground.

Exit criterion:

```text
The resource budget is traceable to a candidate 6U architecture and operating
mode set.
```

## Workstream 4: Reproducible Prototype

Purpose:

```text
Make the demo easy for a reviewer or collaborator to rerun, extend, and audit.
```

Near-term tasks:

- Keep `make final-check` passing.
- Add a one-command real-data sample refresh when credentials are available.
- Produce small dashboard or notebook views for tile decisions and resource
  budgets.
- Version fixture provenance and keep real/synthetic rows clearly labeled.
- Record failure cases as useful evidence.

Exit criterion:

```text
A collaborator can reproduce the fixture, run the policy, inspect decisions,
and understand the evidence boundary.
```

## Pitch Language

Use:

```text
The core onboard triage pattern is buildable now. The next phase is validation
and mission hardening: more real data, user calibration, and mapping the policy
onto a specific 6U compute, power, thermal, storage, and downlink stack.
```

Avoid:

```text
40 percent not doable
flight ready
validated crop-stress model
NASA approved
```
