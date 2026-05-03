# SoilPulse-ET

SoilPulse-ET is a NASA Space to Soil Challenge Phase 1 software artifact for a
SmallSat onboard triage concept supporting regenerative-agriculture
water-stress follow-up.

The core idea is resource discipline under a limited satellite contact window.
SoilPulse-ET scores candidate tiles, tracks event priority and evidence
quality, then chooses one of three packet actions:

- `priority_chip`: send a higher-detail observation chip
- `feature_summary`: send compact statistics and metadata
- `defer`: send nothing for this contact

The current artifact is a transparent policy demonstrator. It includes runnable
policy code, demo fixtures, tests, budget metrics, paper documentation, and the
video slide deck used for the Phase 1 pitch.

## NASA Data Anchor

The NASA data anchor is:

```text
ECOSTRESS Tiled Evapotranspiration Instantaneous and Daytime L3 Global 70 m V002
DOI: 10.5067/ECOSTRESS/ECO_L3T_JET.002
```

The best current demo fixture combines one ECOSTRESS/AppEEARS-derived
knowledge-gap row with labeled synthetic mission-scenario rows so reviewers can
inspect both NASA data lineage and the onboard resource policy.

## Submission Paper

The Phase 1 paper is included here:

```text
docs/PAPER_FINAL_CANDIDATE.pdf
```

## Video Slide Deck

The slide deck used for the submitted pitch video is included here:

```text
docs/VIDEO_SLIDE_DECK.pdf
docs/VIDEO_SLIDE_DECK.typ
docs/assets/starry_night_far.svg
```

Supporting docs:

- `docs/EXECUTIVE_SUMMARY.md`
- `docs/MISSION_CONCEPT.md`
- `docs/ARCHITECTURE.md`
- `docs/RESOURCE_BUDGET.md`
- `docs/CODE_WALKTHROUGH.md`
- `docs/REPRODUCIBILITY.md`
- `docs/NEAR_TERM_VALIDATION_AND_HARDENING.md`

## Quick Start

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
make hybrid-demo
```

Expected headline metric from the hybrid demo:

```text
224.0 KiB used versus 784.0 KiB full-chip baseline
560.0 KiB / 71.43% downlink saved
2/2 high-stress candidates retained
1/1 cloudy candidates deferred
```

The `71.43%` figure is byte savings, not the percentage of tiles deferred. In
the hybrid fixture, the policy selects two full chips plus two compact feature
summaries and defers four tiles.

## Verification

Run the non-credentialed verification path:

```bash
make final-check
```

This runs import smoke checks, local data manifest generation, synthetic demo,
hybrid demo, fixture builders, event-hunt scoring, and tests.

## Optional Credentialed ECOSTRESS Path

The AppEEARS integration is present but requires Earthdata credentials. Raw
downloads and credentials are intentionally not committed.

```bash
EARTHDATA_USERNAME='YOUR_USERNAME' EARTHDATA_PASSWORD='YOUR_PASSWORD' make appeears-campaign
```

## Repository Scope

This repository is the public-facing challenge artifact. It contains the
runnable policy demo, tests, selected documentation, final Phase 1 paper, and
video slide deck. Lab notes, private process files, local submission videos,
raw data, and credentials are intentionally excluded.
