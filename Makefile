PYTHON ?= python3
VENV ?= .venv

.PHONY: help venv install smoke manifest demo event-hunt hybrid-fixture hybrid-demo video-charts hls-fixture terrain-fixture appeears-discover appeears-login-check appeears-run appeears-campaign test final-check

help:
	@printf "Targets:\n"
	@printf "  make venv     - create a local virtualenv\n"
	@printf "  make install  - install editable package with dev extras\n"
	@printf "  make smoke    - run the import-level smoke check\n"
	@printf "  make manifest - print local data manifest\n"
	@printf "  make demo     - run the synthetic onboard triage demo\n"
	@printf "  make event-hunt - rank real/sample rows for useful event windows\n"
	@printf "  make hybrid-fixture - build real-plus-synthetic hybrid demo fixture\n"
	@printf "  make hybrid-demo - run triage demo against hybrid fixture\n"
	@printf "  make video-charts - build final-pitch SVG charts from hybrid fixture\n"
	@printf "  make hls-fixture - build synthetic HLS vegetation support fixture\n"
	@printf "  make terrain-fixture - build synthetic terrain context fixture\n"
	@printf "  make appeears-discover - show ECOSTRESS AppEEARS layers\n"
	@printf "  make appeears-login-check - check AppEEARS login only\n"
	@printf "  make appeears-run      - submit/poll/download/derive ECOSTRESS micro-tile sample\n"
	@printf "  make appeears-campaign - run default multi-window ECOSTRESS event hunt\n"
	@printf "  make test     - run pytest from the venv\n"
	@printf "  make final-check - run the non-credentialed submission verification commands\n"

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -e '.[dev]'

smoke:
	PYTHONPATH=src $(PYTHON) scripts/smoke_import.py

manifest:
	PYTHONPATH=src $(PYTHON) scripts/build_local_data_manifest.py

demo:
	PYTHONPATH=src $(PYTHON) scripts/run_onboard_triage_demo.py --include-metrics --sensitivity

event-hunt:
	PYTHONPATH=src $(PYTHON) scripts/score_event_hunt_candidates.py tests/fixtures/ecostress_derived*.csv

hybrid-fixture:
	PYTHONPATH=src $(PYTHON) scripts/build_hybrid_demo_fixture.py tests/fixtures/ecostress_derived*.csv

hybrid-demo: hybrid-fixture
	PYTHONPATH=src $(PYTHON) scripts/run_onboard_triage_demo.py --input tests/fixtures/candidate_tiles.hybrid.csv --include-metrics --sensitivity

video-charts: hybrid-fixture
	PYTHONPATH=src $(PYTHON) scripts/build_video_charts.py

hls-fixture:
	PYTHONPATH=src $(PYTHON) scripts/build_hls_vegetation_fixture.py

terrain-fixture:
	PYTHONPATH=src $(PYTHON) scripts/build_terrain_context_fixture.py

appeears-discover:
	PYTHONPATH=src $(VENV)/bin/python scripts/appeears_ecostress_sample.py discover

appeears-login-check:
	PYTHONPATH=src $(VENV)/bin/python scripts/appeears_ecostress_sample.py login-check

appeears-run:
	PYTHONPATH=src $(VENV)/bin/python scripts/appeears_ecostress_sample.py run --poll

appeears-campaign:
	PYTHONPATH=src $(VENV)/bin/python scripts/run_appeears_event_campaign.py

test:
	PYTHONPATH=src $(VENV)/bin/python -m pytest -q

final-check:
	$(MAKE) smoke
	$(MAKE) manifest
	$(MAKE) demo
	$(MAKE) hls-fixture
	$(MAKE) terrain-fixture
	$(MAKE) hybrid-demo
	$(MAKE) event-hunt
	$(MAKE) test
