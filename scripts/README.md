# Scripts

Use this folder for repeatable helpers such as:

- manifest generation
- resource-budget calculators
- adaptive-policy demos
- paper / video support tables

Starter files:

- `smoke_import.py` verifies package imports and workspace directories
- `build_local_data_manifest.py` inventories local `data/` files
- `run_onboard_triage_demo.py` runs the synthetic adaptive downlink demo with
  optional fixture loading, metrics, JSON, CSV, and sensitivity outputs
- `appeears_ecostress_sample.py` discovers AppEEARS layers and builds a tiny
  ECOSTRESS-derived fixture when Earthdata credentials are available
- `run_appeears_event_campaign.py` runs the default multi-window ECOSTRESS
  event-hunt campaign
- `score_event_hunt_candidates.py` ranks derived fixtures as stress-event,
  knowledge-gap, or low-signal candidates
- `build_hybrid_demo_fixture.py` builds the labeled real-plus-synthetic
  submission-style demo fixture
