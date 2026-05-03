# SoilPulse-ET Mission Concept

Last updated: 2026-04-10

## One-Line Concept

SoilPulse-ET is a SmallSat onboard triage layer that maintains a tile-level
state of knowledge, then prioritizes image chips and compact feature summaries
for irrigated and regenerative farm landscapes showing evapotranspiration
deficit, vegetation decline, stale evidence, or high user value.

## Target User

Primary user: an irrigation district, conservation planner, or regenerative
agriculture technical-service provider supporting growers under water-stress
and soil-cover decisions.

Initial scenario: Central Valley-style irrigated agriculture where field teams
need earlier warning that a cover-cropped orchard, pasture, vineyard, riparian
buffer, or managed fallow trial is diverging from expected water-use behavior.

## Hardware Stance

The working hardware story should stay disciplined without turning the ratio
itself into a slogan. The right posture is to think far ahead while stating
clearly what is defensible now and what still belongs to future engineering.

- current baseline: a conservative, defensible `6U` rail-based CubeSat
  planning anchor that fits CubeSat Design Specification Rev. `14.1` without
  relying on dispenser-specific extras
- forward engineering path: dispenser-specific packaging, licensing,
  qualification, and possible compute or payload expansion as the concept is
  pushed further over the next `24` months and beyond

Current planning anchor from CDS Rev. `14.1`:

- `6U` body envelope: `100.0 x 226.3 x 366.0 mm`
- typical maximum mass: `12.00 kg`
- center-of-gravity range relative to geometric center: `X +/- 4.5 cm`,
  `Y +/- 2 cm`, `Z +/- 7 cm`
- allowable protrusion from the rail plane on constrained faces: `6.5 mm max`
- rail clearance to first protrusion on each face: `8.5 mm min`

This keeps the current story disciplined. The current concept does not need
propulsion, does not rely on optional extra volume ("tuna can"), and does not
require deployable structures to explain the Phase 1 software artifact.

## Problem

Land managers do not need every scene at full fidelity. They need the right
evidence soon enough to adjust scouting, irrigation, conservation incentives,
or restoration attention.

A fixed SmallSat collection and downlink plan can spend bandwidth on cloudy,
low-change, or low-priority scenes while field conditions are changing quickly.
The challenge fit is to improve the onboard sensing and downlink layer, not to
claim new crop science.

## NASA Data Anchor

Primary anchor:

- ECOSTRESS Tiled Evapotranspiration Instantaneous and Daytime L3 Global
  70 m V002
- DOI: `10.5067/ECOSTRESS/ECO_L3T_JET.002`
- use in Phase 1: ground-truthing and calibration source for tile-level ET
  anomaly logic, not a claim that ECOSTRESS itself flies on the proposed
  SmallSat

Relevant AppEEARS layers for the concept include `ETdaily`,
`ETinstUncertainty`, `cloud`, and `water`. The default demo uses synthetic
features shaped like a future onboard feature table, and the repo now includes
a credentialed AppEEARS path for a tiny ECOSTRESS-derived interface sample.

## Onboard Loop

1. Receive a planned observation list with user priorities and recent history.
2. Acquire a candidate land tile.
3. Run lightweight onboard feature extraction:
   - ET-proxy anomaly against expected condition
   - vegetation-index delta
   - cloud fraction
   - days since last useful observation
   - confidence / uncertainty proxy
4. Score the tile for water-stress follow-up and evidence quality:
   - priority score: how urgently the tile deserves attention
   - evidence quality: how fresh, complete, and reliable the current evidence is
   - knowledge state: `clear_recent`, `stale`, `partial_cloud`, `obscured`, or
     `low_confidence`
5. Select one of three actions:
   - `priority_chip`: downlink a higher-detail image chip
   - `feature_summary`: downlink compact statistics and metadata
   - `defer`: hold or drop the tile for this contact
6. Ground system merges packets with ECOSTRESS-calibrated context and user
   thresholds.

## Tile State Ledger

The core product is not just a stress alert. It is a timestamped state ledger
for each tile or management unit. The ledger can distinguish:

- high priority and high confidence: send a priority chip
- useful signal but limited budget: send a feature summary
- high uncertainty because of clouds or stale observations: mark the knowledge
  gap and prioritize a future clean look
- low signal and recent evidence: defer without wasting downlink

This is valuable because missing or cloudy data becomes explicit operational
knowledge. The system can say, in effect: this tile looked risky recently, but
the latest observation is obscured or stale, so the mission should avoid
overclaiming and plan the next useful observation.

## Demo Result

Command:

```bash
PYTHONPATH=src python3 scripts/run_onboard_triage_demo.py
```

Current best hybrid result (`make hybrid-demo`):

| tile | action | priority | evidence | knowledge | downlink KiB | reason |
| --- | --- | ---: | ---: | --- | ---: | --- |
| cv-covercrop-013 | priority_chip | 0.7394 | 0.7744 | clear_recent | 96.0 | selected_by_score |
| cv-vineyard-032 | priority_chip | 0.7075 | 0.7291 | stale | 112.0 | selected_by_score |
| cv-pasture-021 | feature_summary | 0.5523 | 0.7776 | clear_recent | 8.0 | selected_by_score |
| cv-orchard-044 | feature_summary | 0.4371 | 0.6241 | stale | 8.0 | selected_by_score |
| cv-riparian-016 | defer | 0.3191 | 0.5110 | obscured | 0.0 | cloud_screen |
| cv-riparian-016-ecostress | defer | 0.2789 | 0.2775 | low_confidence | 0.0 | below_event_threshold |
| cv-rangeland-008 | defer | 0.2732 | 0.6085 | stale | 0.0 | below_event_threshold |
| cv-fallow-003 | defer | 0.1086 | 0.8264 | clear_recent | 0.0 | below_event_threshold |

Used: `224.0 KiB`, `720 ms`, `16.0 J`, `4 packets`.

Versus a full-chip-all-candidates baseline of `784 KiB`, the hybrid demo saves
`560 KiB` / `71.43%` while retaining `2/2` high-stress candidates and deferring
`1/1` cloudy candidates. The `cv-riparian-016-ecostress` row is real
ECOSTRESS-derived lineage evidence; the other mission-scenario rows are labeled
synthetic.

## What This Proves

- The software artifact demonstrates an adaptive onboard decision under explicit
  resource limits.
- The scoring inputs are inspectable and traceable to the planned data story.
- The output separates event priority from evidence quality, so stale or
  cloud-limited observations are surfaced instead of silently disappearing.
- The output can support a paper table, video visual, and code repository link.

## What This Does Not Prove Yet

- It is not a calibrated crop-stress model.
- It is not flight software.
- The AppEEARS sample path is an interface check, not agronomic validation.
- The resource assumptions are concept-planning values that need references and
  sensitivity analysis before submission.

## Forward Engineering Path

The longer-horizon path should be described as the engineering follow-on, not as
a current capability:

- select an actual flight bus, power system, radio, and compute board within a
  specific `6U` or mission-approved dispenser path
- decide whether access ports, extra volume, or deployables are worth the added
  interface and inhibit complexity
- perform licensing and safety work: radio licensing, orbital-debris
  compliance, and remote-sensing review if required
- plan dispenser fit checks, random vibration, thermal-vacuum bakeout, and any
  protoflight or qualification flow required by the launch provider
- refine the onboard feature-extraction hardware from a representative CPU-only
  concept toward a chosen CPU plus optional FPGA/NPU stack
