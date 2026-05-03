# Executive Summary

Last updated: 2026-04-23

`SoilPulse-ET` is a SmallSat onboard-processing concept for regenerative
agriculture and land-resilience monitoring. The system helps a spacecraft decide
which candidate field observations deserve high-detail image chips, which should
be compressed into compact feature summaries, and which should be deferred
under cloud, downlink, energy, or compute constraints. Its central product is a
tile-level state ledger that tracks both event priority and evidence quality:
what looks important, how fresh the observation is, and how much cloud or
uncertainty limits interpretation.

The first target user is an irrigation district, conservation planner, or
regenerative agriculture technical-service provider supporting field teams under
water-stress conditions. The first use case is Central Valley-style irrigated
agriculture, where cover-cropped orchards, vineyards, pastures, riparian
buffers, and managed fallow trials can diverge quickly from expected
evapotranspiration behavior.

The primary NASA data anchor is ECOSTRESS Tiled Evapotranspiration
Instantaneous and Daytime L3 Global 70 m V002, DOI
`10.5067/ECOSTRESS/ECO_L3T_JET.002`. In Phase 1, ECOSTRESS supports the ET
logic, calibration path, and citation requirement. The current code artifact is
a transparent policy demonstrator with a hybrid fixture: one top-ranked
ECOSTRESS/AppEEARS-derived public micro-tile knowledge-gap row from a
five-window campaign plus labeled synthetic mission-scenario rows. It does not
claim flight readiness or validated agronomic prediction.

The demo scores candidate tiles by ET anomaly, vegetation-index change, cloud
fraction, revisit age, user priority, and confidence. It separately reports
evidence quality and knowledge states such as `clear_recent`, `stale`, and
`obscured`, so cloudy or incomplete observations become explicit operational
knowledge instead of silent missing data. The hybrid run selects two priority
chips and two feature summaries, deferring cloudy or low-threshold candidates
while using `224 KiB`, `720 ms`, `16 J`, and `4 packets` under a `384 KiB`
planning budget. It saves `560 KiB` / `71.43%` versus a full-chip baseline
while retaining `2/2` high-stress candidates.

The Phase 1 submission should emphasize systems value: measurable downlink
discipline, explainable onboard triage, degradation modes, and a path from NASA
data to user-facing water-stress follow-up.
