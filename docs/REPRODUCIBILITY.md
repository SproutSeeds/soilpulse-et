# Reproducibility

Last updated: 2026-04-23

## Environment

Requires Python `3.11+`.

```bash
python3 -m venv .venv
```

```bash
.venv/bin/python -m pip install -e '.[dev]'
```

## Submission Verification

Run the full non-credentialed verification pass with one command:

```bash
make final-check
```

This runs:

- `make smoke`
- `make manifest`
- `make demo`
- `make hls-fixture`
- `make terrain-fixture`
- `make hybrid-demo`
- `make event-hunt`
- `make test`

Expected current test status:

```text
43 passed
```

## Best Current Demo

The strongest judge-facing demo is:

```bash
make hybrid-demo
```

Current expected metrics:

- `8` candidate rows
- `4` selected packets
- `224.0 KiB` used downlink
- `784.0 KiB` full-chip baseline
- `560.0 KiB / 71.43%` downlink saved
- `2/2 / 100%` high-stress retention
- `1/1` cloudy candidates deferred

The hybrid fixture is rebuilt by:

```bash
make hybrid-fixture
```

It writes:

```text
tests/fixtures/candidate_tiles.hybrid.csv
```

The fixture labels each row as either `ecostress_derived` or
`synthetic_mission_scenario`.

## Support Data Fixtures

Build the synthetic HLS-shaped vegetation support fixture:

```bash
make hls-fixture
```

Build the synthetic NASADEM / SRTM-style terrain support fixture:

```bash
make terrain-fixture
```

These fixtures are no-network scaffolds for Phase 2 data ingestion. They are
not real HLS, real DEM, hydrology, or stress-event validation.

## Real-Data Event Hunt

Rank available ECOSTRESS-derived fixtures:

```bash
make event-hunt
```

Current real campaign result:

```text
top-ranked row = cv-riparian-016, 2024-08-01..2024-09-30, knowledge_gap_candidate
```

That means the current real campaign is useful as NASA data-lineage and
tile-knowledge-ledger proof, not as a dramatic stress-event validation.

## Optional Credentialed AppEEARS Campaign

This requires Earthdata credentials outside the repo. Use a one-line command
and do not paste the password into chat, docs, code, or commit history.

```bash
EARTHDATA_USERNAME='YOUR_USERNAME' EARTHDATA_PASSWORD='YOUR_PASSWORD' make appeears-campaign
```

The campaign writes separate derived fixtures:

```text
tests/fixtures/ecostress_derived_*.csv
```

After it completes, rerun:

```bash
make event-hunt
```

Promotion rule: only promote a real row into the final hybrid story if it is
clear enough to explain as either a `stress_event_candidate` or a useful
`knowledge_gap_candidate`.

## AppEEARS Single-Window Pattern

Use this one-liner for a targeted follow-up window:

```bash
EARTHDATA_USERNAME='YOUR_USERNAME' EARTHDATA_PASSWORD='YOUR_PASSWORD' PYTHONPATH=src .venv/bin/python scripts/appeears_ecostress_sample.py run --start-date 2024-06-01 --end-date 2024-07-31 --date-start 2024-06-01 --date-end 2024-07-31 --output tests/fixtures/ecostress_derived_2024_06_07.csv --poll
```

## Syntax Check

If Python tries to write bytecode outside the workspace, use:

```bash
env PYTHONPATH=src PYTHONPYCACHEPREFIX=/tmp/nasa-space-to-soil-pyc python3 -m compileall -q src scripts
```

## Data Policy

The repo must not contain downloaded ECOSTRESS bundles, credentials, private
submission videos, account tokens, or bulky generated data. Raw AppEEARS
downloads belong under gitignored `data/appeears/`.

If a new real NASA sample fixture is added, update:

- `docs/local-data-manifest.md`
- `docs/DATA_BRIDGE.md`
- `docs/SOURCES.md`
- `docs/CLAIM_REGISTER.md`
- `docs/REAL_DATA_EVENT_HUNT.md`

Then run:

```bash
PYTHONPATH=src python3 scripts/build_local_data_manifest.py --hash
```
