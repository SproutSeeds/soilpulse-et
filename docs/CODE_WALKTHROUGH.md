# Code Walkthrough

Last updated: 2026-04-23

The software artifact demonstrates one key capability: adaptive onboard triage
under SmallSat-style resource limits. It also includes a credentialed AppEEARS
path for creating a tiny ECOSTRESS-derived interface fixture.

## What To Run

```bash
make demo
```

This prints:

- packet decisions
- resource usage
- baseline comparison metrics
- budget sensitivity rows

To run the best current submission-style demo with one real ECOSTRESS
knowledge-gap row plus synthetic mission-scenario rows:

```bash
make hybrid-demo
```

To rank real ECOSTRESS-derived windows for event usefulness:

```bash
make event-hunt
```

To inspect the live ECOSTRESS AppEEARS layers:

```bash
make appeears-discover
```

To submit, poll, download, and derive the optional ECOSTRESS fixture:

```bash
make appeears-run
```

`make appeears-run` defaults to a grouped public micro-tile request: four tile
proxies with three AppEEARS points each. The output remains a small CSV fixture,
not bulky rasters.

To run the default multi-window event-hunt campaign:

```bash
EARTHDATA_USERNAME='YOUR_USERNAME' EARTHDATA_PASSWORD='YOUR_PASSWORD' make appeears-campaign
```

To build the no-network support fixtures for the next data lanes:

```bash
make hls-fixture
make terrain-fixture
```

## Main Files

| file | purpose |
| --- | --- |
| `src/nasa_space_to_soil_challenge/onboard_triage.py` | scoring, planning, baseline, metrics, fixture loading |
| `src/nasa_space_to_soil_challenge/appeears.py` | Earthdata credential parsing, AppEEARS API client, ECOSTRESS fixture transformation |
| `scripts/run_onboard_triage_demo.py` | CLI for Markdown, JSON, CSV, metrics, and sensitivity output |
| `scripts/appeears_ecostress_sample.py` | CLI for AppEEARS discovery, submit, status, download, and derive |
| `scripts/run_appeears_event_campaign.py` | CLI for running multiple AppEEARS windows into separate fixtures |
| `scripts/score_event_hunt_candidates.py` | ranks real/sample rows by stress-event or knowledge-gap usefulness |
| `scripts/build_hybrid_demo_fixture.py` | builds the labeled real-plus-synthetic hybrid fixture |
| `src/nasa_space_to_soil_challenge/hls_vegetation.py` | synthetic HLS-shaped vegetation-index support helpers |
| `src/nasa_space_to_soil_challenge/terrain_context.py` | synthetic NASADEM / SRTM-style terrain context helpers |
| `scripts/build_hls_vegetation_fixture.py` | writes the HLS vegetation support fixture |
| `scripts/build_terrain_context_fixture.py` | writes the terrain context support fixture |
| `tests/test_onboard_triage.py` | behavior tests |
| `tests/test_appeears.py` | AppEEARS request and transformation tests |
| `tests/fixtures/candidate_tiles.synthetic.csv` | clearly labeled synthetic candidate tile fixture |
| `tests/fixtures/ecostress_derived_sample.csv` | real ECOSTRESS/AppEEARS-derived public micro-tile fixture |
| `tests/fixtures/ecostress_derived_*.csv` | five-window ECOSTRESS/AppEEARS event-hunt fixtures |
| `tests/fixtures/candidate_tiles.hybrid.csv` | hybrid fixture combining one real knowledge-gap row with synthetic mission rows |
| `tests/fixtures/hls_vegetation_sample.csv` | synthetic HLS-shaped vegetation fixture; not real HLS validation |
| `tests/fixtures/terrain_context_sample.csv` | synthetic NASADEM / SRTM-style context fixture; not a hydrology model |

## Core Data Model

`CandidateTile` represents one candidate observation after lightweight onboard
feature extraction. It includes:

- ET anomaly proxy
- vegetation-index delta
- cloud fraction
- days since last useful observation
- user priority
- confidence
- packet size estimates
- processing and energy estimates

The demo also derives:

- `stress_score`: how urgently the tile deserves water-stress follow-up
- `evidence_quality_score`: how fresh, clear, and reliable the evidence is
- `knowledge_state`: a review label such as `clear_recent`, `stale`, or
  `obscured`

`ResourceBudget` bounds the triage cycle:

- downlink KiB
- packet count
- processing milliseconds
- energy joules

## Scoring

`stress_score()` rewards:

- stronger ET deficit
- vegetation decline
- older revisit age
- higher user priority
- higher confidence

It penalizes cloud fraction.

The score is a policy score, not a crop-health model.

`evidence_quality_score()` is intentionally separate from `stress_score()`.
This lets the demo represent cases where a tile is important but the latest
evidence is stale, cloud-limited, or low confidence. In the packet table, that
appears as a separate evidence score and knowledge-state label.

## Actions

`plan_downlink()` assigns each tile one action:

| action | meaning |
| --- | --- |
| `priority_chip` | send higher-detail chip |
| `feature_summary` | send compact statistics and metadata |
| `defer` | do not downlink this contact |

The policy downgrades high-score chips to summaries if chip packets do not fit
the current resource budget.

## Metrics

`compute_metrics()` reports:

- full-chip baseline size
- used downlink
- downlink saved
- high-stress retention
- cloudy candidates deferred
- packet, processing, and energy budget utilization

Default synthetic result from `make demo`:

- full-chip baseline: `688 KiB`
- used downlink: `224 KiB`
- downlink saved: `464 KiB` / `67.44%`
- high-stress retention: `2/2`
- cloudy candidates deferred: `1/1`
- the cloudy riparian buffer is labeled `obscured`, and stale but useful tiles
  remain visible in the plan

Submission-style hybrid result from `make hybrid-demo`:

- full-chip baseline: `784 KiB`
- used downlink: `224 KiB`
- downlink saved: `560 KiB` / `71.43%`
- high-stress retention: `2/2`
- cloudy candidates deferred: `1/1`
- one top-ranked real ECOSTRESS/AppEEARS-derived campaign row is preserved as a
  low-confidence / stale knowledge-gap example

## Fixture Loading

The CLI can load CSV or JSON fixtures:

```bash
PYTHONPATH=src python3 scripts/run_onboard_triage_demo.py \
  --input tests/fixtures/candidate_tiles.synthetic.csv \
  --include-metrics \
  --sensitivity
```

The current fixture is synthetic and must not be described as real ECOSTRESS
data.

If `tests/fixtures/ecostress_derived_sample.csv` is generated, it may be
described as a small ECOSTRESS-derived public micro-tile interface check. It
still must not be described as model validation.

`tests/fixtures/candidate_tiles.hybrid.csv` is labeled row by row:

- `ecostress_derived`: real NASA data fields for the knowledge-gap row
- `synthetic_mission_scenario`: synthetic rows for planned onboard behavior and
  resource-constrained mission demonstration

## Why This Substantiates The Submission

The code is intentionally small:

- a judge can inspect it quickly
- every decision has a reason code
- every packet consumes budget
- the output maps directly to the paper and architecture diagrams
- limitations are explicit
