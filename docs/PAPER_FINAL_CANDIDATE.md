# SoilPulse-ET: SmallSat Onboard Triage For Regenerative Agriculture Water-Stress Follow-Up

Submission date: 2026-04-23

Evidence boundary: this Phase 1 artifact is a concept and policy demonstrator,
not flight software or validated agronomic prediction.

## Introduction

SoilPulse-ET is a SmallSat onboard-processing concept for regenerative
agriculture and land-resilience monitoring. The system maintains a tile-level
state ledger, then helps a spacecraft decide which candidate field observations
should receive high-detail image chips, which should be compressed into compact
feature summaries, and which should be deferred during constrained operations.

The first target user is an irrigation district, conservation planner, or
regenerative agriculture technical-service provider supporting field teams under
water-stress conditions. In a Central Valley-style pilot scenario, an analyst
may need to prioritize cover-cropped orchards, deficit-irrigated vineyards,
rotational pastures, riparian buffers, and managed fallow trials after a hot dry
week. The operational challenge is not a lack of Earth-observation data. It is
deciding which data are worth collecting, processing, and returning first under
SmallSat power, compute, storage, and bandwidth limits.

SoilPulse-ET addresses the challenge as a systems problem. For creativity, it
uses an onboard chip-versus-summary-versus-defer policy rather than a ground-only
dashboard. For technical feasibility, it uses explicit resource budgets and
degradation modes. For impact, it reports downlink saved, high-stress retention,
and cloud-waste avoidance. For business model evaluation, it names institutional
agricultural decision-support users and extension markets. For presentation,
the paper, software artifact, and video evidence packet use the same dataflow
and metrics.

## Solution Architecture

The architecture begins with user priorities and field history on the ground. An
observation planner converts those goals into candidate tile tasks. After
acquisition, an onboard feature extractor produces a compact feature row for
each tile: evapotranspiration anomaly proxy, vegetation-index change, cloud
fraction, days since last useful observation, user priority, confidence, and
resource estimates. A tile state ledger derives both a priority score and an
evidence-quality score, so stale, cloudy, or low-confidence observations remain
visible as operational knowledge. The triage policy then selects one of three
packet actions.

![SoilPulse-ET architecture](docs/diagrams/soilpulse_architecture_paper.png){height=2.8in}

Priority chips send higher-detail crops for immediate review. Feature summaries
send compact evidence and metadata when the signal is useful but a full chip is
not justified. Deferred tiles send nothing during the current contact, either
because the tile is cloudy, below threshold, or does not fit available
resources.

![Packet decision flow](docs/diagrams/packet_decision_flow.png){height=3.4in}

The current code artifact implements this policy as a transparent Python demo.
It is intentionally small: each tile receives a priority score, evidence score,
knowledge-state label, action, reason code, and resource cost. The policy can
downgrade a high-score chip to a summary if the chip does not fit the current
budget.

## NASA Data Anchor And Demo

The primary NASA data anchor is ECOSTRESS Tiled Evapotranspiration
Instantaneous and Daytime L3 Global 70 m V002, DOI
`10.5067/ECOSTRESS/ECO_L3T_JET.002`. ECOSTRESS supports the evapotranspiration
logic and future calibration path. The implemented AppEEARS path produced a
tiny ECOSTRESS-derived public micro-tile fixture without claiming validation on
ECOSTRESS. The current submission-style demo uses a hybrid fixture: one
ECOSTRESS-derived knowledge-gap row plus labeled synthetic mission-scenario
rows for planned onboard behavior.

The demo maps ECOSTRESS and mission concepts to feature fields: ET estimates to
`et_anomaly_mm_day`, uncertainty to `confidence`, cloud mask to
`cloud_fraction`, water mask to excluded pixels, revisit history to
`days_since_seen`, and user planning value to `user_priority`.

Hybrid demo result:

| tile | action | priority | evidence | knowledge | KiB | reason |
| --- | --- | ---: | ---: | --- | ---: | --- |
| cv-covercrop-013 | priority_chip | 0.7394 | 0.7744 | clear_recent | 96.0 | selected_by_score |
| cv-vineyard-032 | priority_chip | 0.7075 | 0.7291 | stale | 112.0 | selected_by_score |
| cv-pasture-021 | feature_summary | 0.5523 | 0.7776 | clear_recent | 8.0 | selected_by_score |
| cv-orchard-044 | feature_summary | 0.4371 | 0.6241 | stale | 8.0 | selected_by_score |
| cv-riparian-016 | defer | 0.3191 | 0.5110 | obscured | 0.0 | cloud_screen |
| cv-riparian-016-ecostress | defer | 0.2789 | 0.2775 | low_confidence | 0.0 | below_event_threshold |
| cv-rangeland-008 | defer | 0.2732 | 0.6085 | stale | 0.0 | below_event_threshold |
| cv-fallow-003 | defer | 0.1086 | 0.8264 | clear_recent | 0.0 | below_event_threshold |

## Feasibility And Impact

The default demo budget is `384 KiB`, `6 packets`, `1500 ms`, and `42 J`, with
planning envelopes of `128 MiB` memory and `512 MiB` temporary storage. The
current baseline is anchored to a CDS Rev. `14.1` rail-based `6U` envelope
(`100.0 x 226.3 x 366.0 mm`, typical max mass `12 kg`) without relying on
optional extra volume, propulsion, or required deployables. The forward
engineering path covers component selection, dispenser-specific refinement,
qualification work, and the unresolved details that would be worked out as the
concept is pushed further over the next `24` months. The representative compute
stack is a radiation-tolerant CPU for control and policy execution, with
optional FPGA or NPU acceleration for feature extraction.

Metrics versus a full-chip-all-candidates baseline:

| metric | value |
| --- | ---: |
| full-chip baseline | 784.0 KiB |
| used downlink | 224.0 KiB |
| downlink saved | 560.0 KiB / 71.43% |
| high-stress retention | 2/2 / 100% |
| cloudy candidates deferred | 1/1 |
| cloud waste avoided | 96.0 KiB |
| processing budget used | 48.00% |
| energy budget used | 38.10% |

Budget sensitivity:

| downlink KiB | packets | used KiB | selected | saved % | high-stress retained |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 3 | 24.0 | 3 | 96.94 | 100.00% |
| 128 | 4 | 120.0 | 4 | 84.69 | 100.00% |
| 384 | 6 | 224.0 | 4 | 71.43 | 100.00% |

The smaller budgets force the policy toward compact summaries, which is the
intended degraded behavior. The system does not make autonomous irrigation
recommendations or guarantee yield outcomes. It creates a smaller, better
prioritized analyst worklist.

## Market, Execution, And Next Steps

The first adopter is an institutional user responsible for many fields:
irrigation districts, conservation planners, regenerative agriculture program
managers, or technical-service providers. NASA Harvest provides context for
satellite-driven agricultural monitoring across policy and regional workflows.
OpenET provides useful ET-market context for water budgets, groundwater
management, water trading, and ET-based irrigation practices, while reinforcing
that ET data supports decisions rather than directly issuing irrigation
commands.

Fractal Research Group builds public research infrastructure for targeted,
evidence-bounded work, with current artifacts in longevity, biomedical evidence
systems, and auditable research operations. SoilPulse-ET extends that operating
style into land and water resilience, connecting FRG's broader mission around
health, longevity, and fresh filtered water access for underserved communities
to a NASA-grounded SmallSat concept. The team's role in Phase 1 is to make the
system inspectable: reproducible code, explicit resource budgets, real
ECOSTRESS lineage, and clear claim boundaries.

The MVP path is practical: expand the ECOSTRESS/AppEEARS event hunt across
public windows and locations, calibrate thresholds with user feedback, extend
the resource model to raw scene sizes and contact windows, and test degraded
operations. Extension markets include forestry drought stress, restoration
monitoring, post-fire recovery, and water-resource risk analytics.

Execution risk is controlled by keeping the Phase 1 artifact narrow: NASA data
lineage, explicit resource accounting, transparent policy code, and clear
separation between real observations and synthetic mission-scenario rows.

If selected as a finalist, the next steps are:

1. Expand the ECOSTRESS-derived event hunt across additional public date
   windows and locations.
2. Promote strong real stress-event rows into the hybrid fixture when evidence
   is clear enough to explain.
3. Calibrate thresholds with user priorities and field-scouting feedback.
4. Extend resource modeling to memory, storage, raw scene sizes, and contact
   windows.
5. Prepare a partner pilot with a district or conservation-service workflow.

## Conclusion

SoilPulse-ET is a systems-first answer to the Space to Soil challenge. It uses a
NASA evapotranspiration dataset as the scientific anchor, but centers the
submission on onboard decision-making: what to sense, what to summarize, what to
downlink, and what to defer under realistic SmallSat constraints. The code
artifact gives judges a concrete view of the adaptive policy while preserving
honest boundaries around flight readiness and agronomic validation.

\newpage

## References

- NASA Space to Soil Challenge. https://nasa-space-to-soil.org/
- Hook, Simon, and Gregory Halverson. ECOSTRESS Tiled Evapotranspiration
  Instantaneous and Daytime L3 Global 70 m v002. NASA Land Processes Distributed
  Active Archive Center, 2024. doi:10.5067/ECOSTRESS/ECO_L3T_JET.002.
- NASA Earthdata ECOSTRESS catalog.
  https://www.earthdata.nasa.gov/data/catalog/lpcloud-eco-l3t-jet-002
- NASA SmallSats and CubeSats.
  https://www.nasa.gov/what-are-smallsats-and-cubesats/
- CubeSat Design Specification Rev 14.1.
  https://www.nasa.gov/wp-content/uploads/2018/01/cubesatdesignspecificationrev14_12022-02-09.pdf
- JPL Artificial Intelligence Group ASPEN.
  https://ai.jpl.nasa.gov/public/projects/aspen/
- NASA Harvest. https://www.nasaharvest.org/
- OpenET FAQ. https://openetdata.org/faq/
