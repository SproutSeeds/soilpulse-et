import csv
import subprocess
import sys
from pathlib import Path

import pytest

from nasa_space_to_soil_challenge.hls_vegetation import (
    HLS_VEGETATION_FIELDS,
    ReflectanceSnapshot,
    classify_vegetation_context,
    normalized_difference,
    sample_hls_vegetation_inputs,
    vegetation_context_confidence,
    vegetation_index_deltas,
)
from nasa_space_to_soil_challenge.onboard_triage import load_candidate_tiles, plan_downlink
from scripts.build_hls_vegetation_fixture import (
    build_fixture_rows,
    render_csv,
    write_hls_vegetation_fixture,
)


def test_vegetation_index_deltas_compute_ndvi_and_ndmi_alias() -> None:
    before = ReflectanceSnapshot(red=0.20, nir=0.50, swir1=0.30)
    after = ReflectanceSnapshot(red=0.22, nir=0.40, swir1=0.36)

    deltas = vegetation_index_deltas(before, after)

    assert deltas.ndvi_before == pytest.approx(0.4286)
    assert deltas.ndvi_after == pytest.approx(0.2903)
    assert deltas.ndvi_delta == pytest.approx(-0.1383)
    assert deltas.ndmi_before == pytest.approx(0.25)
    assert deltas.ndmi_after == pytest.approx(0.0526)
    assert deltas.ndmi_delta == pytest.approx(-0.1974)
    assert deltas.ndwi_delta == deltas.ndmi_delta


def test_normalized_difference_rejects_zero_denominator() -> None:
    with pytest.raises(ValueError, match="denominator"):
        normalized_difference(0.0, 0.0)


def test_classify_vegetation_context_strengthens_or_weakens_et_signal() -> None:
    confidence = vegetation_context_confidence(hls_clear_fraction=0.90, cloud_fraction=0.10)

    strengthens = classify_vegetation_context(
        et_anomaly_mm_day=-2.0,
        ndvi_delta=-0.08,
        ndmi_delta=-0.07,
        confidence=confidence,
        cloud_fraction=0.10,
    )
    weakens = classify_vegetation_context(
        et_anomaly_mm_day=-2.0,
        ndvi_delta=0.01,
        ndmi_delta=0.00,
        confidence=confidence,
        cloud_fraction=0.10,
    )
    limited = classify_vegetation_context(
        et_anomaly_mm_day=-2.0,
        ndvi_delta=-0.08,
        ndmi_delta=-0.07,
        confidence=0.45,
        cloud_fraction=0.75,
    )

    assert strengthens.context == "strengthens_et_signal"
    assert weakens.context == "weakens_et_signal"
    assert limited.context == "mixed_or_limited_context"


def test_fixture_rows_are_triage_compatible_and_labeled() -> None:
    rows = build_fixture_rows()

    assert len(rows) == len(sample_hls_vegetation_inputs())
    assert set(HLS_VEGETATION_FIELDS) == set(rows[0])
    assert {row["vegetation_context"] for row in rows} == {
        "strengthens_et_signal",
        "weakens_et_signal",
        "mixed_or_limited_context",
    }
    assert all(row["claim_label"] == "Heuristic" for row in rows)
    assert all(row["validation_status"] == "synthetic_fixture_not_validated_stress_event" for row in rows)
    assert rows[0]["vegetation_index_delta"] == rows[0]["ndvi_delta"]


def test_written_fixture_loads_with_existing_triage_csv_vocabulary(tmp_path: Path) -> None:
    output = tmp_path / "hls_vegetation_sample.csv"
    rows = build_fixture_rows()

    write_hls_vegetation_fixture(rows, output)
    candidates = load_candidate_tiles(output)
    plan = plan_downlink(candidates)

    assert [candidate.tile_id for candidate in candidates] == [str(row["tile_id"]) for row in rows]
    assert any(decision.action == "priority_chip" for decision in plan.decisions)
    assert any(decision.action == "defer" for decision in plan.decisions)


def test_tracked_fixture_matches_builder_schema() -> None:
    fixture = Path("tests/fixtures/hls_vegetation_sample.csv")

    with fixture.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert reader.fieldnames == list(HLS_VEGETATION_FIELDS)
    assert len(rows) == len(build_fixture_rows())
    assert rows[0]["source"] == "hls_vegetation_synthetic_fixture"
    assert rows[0]["vegetation_context"] == "strengthens_et_signal"


def test_cli_can_print_fixture_without_network(tmp_path: Path) -> None:
    output = tmp_path / "hls.csv"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_hls_vegetation_fixture.py",
            "--output",
            str(output),
            "--stdout",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert output.exists()
    assert result.stdout == render_csv(build_fixture_rows())
