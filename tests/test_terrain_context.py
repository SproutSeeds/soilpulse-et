import csv
import subprocess
import sys
from pathlib import Path

from nasa_space_to_soil_challenge.terrain_context import (
    TERRAIN_CONTEXT_FIELDNAMES,
    TerrainSample,
    build_terrain_context_rows,
    classify_slope,
    classify_terrain_context,
    format_terrain_context_csv,
    load_terrain_samples,
    sample_terrain_samples,
)


def test_classify_slope_thresholds() -> None:
    assert classify_slope(0.0) == "flat"
    assert classify_slope(2.1) == "gentle"
    assert classify_slope(7.5) == "moderate"
    assert classify_slope(16.0) == "steep"


def test_terrain_context_separates_retention_and_runoff_context() -> None:
    low_convergent = TerrainSample(
        tile_id="low",
        land_use="test",
        acres=10.0,
        slope_degrees=1.0,
        relative_elevation_m=-3.0,
        low_point_signal=0.9,
        flow_accumulation_proxy=0.8,
    )
    steep_high = TerrainSample(
        tile_id="steep",
        land_use="test",
        acres=10.0,
        slope_degrees=14.0,
        relative_elevation_m=6.0,
        low_point_signal=0.2,
        flow_accumulation_proxy=0.1,
    )

    low_context = classify_terrain_context(low_convergent)
    steep_context = classify_terrain_context(steep_high)

    assert low_context.terrain_context == "convergent_low_context"
    assert low_context.retention_context_score > low_context.runoff_context_score
    assert steep_context.terrain_context == "runoff_shedding_context"
    assert steep_context.runoff_context_score > steep_context.retention_context_score


def test_terrain_context_without_flow_proxy_stays_contextual() -> None:
    context = classify_terrain_context(
        TerrainSample(
            tile_id="gentle-low",
            land_use="test",
            acres=10.0,
            slope_degrees=2.5,
            relative_elevation_m=-2.0,
            low_point_signal=0.8,
            flow_accumulation_proxy=None,
        )
    )

    assert context.terrain_context == "retention_context"
    assert context.flow_proxy_used is False
    assert "not a hydrology model" in context.note


def test_build_rows_include_triage_compatible_metadata() -> None:
    rows = build_terrain_context_rows(sample_terrain_samples())
    by_id = {str(row["tile_id"]): row for row in rows}

    assert set(TERRAIN_CONTEXT_FIELDNAMES).issuperset(rows[0])
    assert by_id["cv-covercrop-013"]["terrain_context"] == "convergent_low_context"
    assert by_id["cv-vineyard-032"]["terrain_context"] == "runoff_shedding_context"
    assert by_id["cv-rangeland-008"]["flow_accumulation_proxy"] is None
    assert rows[0]["source"] == "synthetic_terrain_context"
    assert rows[0]["hybrid_role"] == "static_terrain_context"
    assert "not a hydrology model" in str(rows[0]["augmentation_note"])


def test_fixture_round_trips_from_csv() -> None:
    fixture = Path(__file__).parent / "fixtures" / "terrain_context_sample.csv"

    samples = load_terrain_samples(fixture)
    rows = build_terrain_context_rows(samples)

    assert len(samples) == 5
    assert samples[0].tile_id == "cv-covercrop-013"
    assert samples[3].flow_accumulation_proxy is None
    assert rows[2]["terrain_context"] == "convergent_low_context"


def test_format_terrain_context_csv_has_stable_header() -> None:
    csv_text = format_terrain_context_csv(build_terrain_context_rows(sample_terrain_samples()))
    header = csv_text.splitlines()[0].split(",")

    assert header == list(TERRAIN_CONTEXT_FIELDNAMES)
    assert "cv-riparian-016" in csv_text


def test_cli_builder_writes_fixture(tmp_path: Path) -> None:
    output = tmp_path / "terrain_context_sample.csv"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_terrain_context_fixture.py",
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "terrain_context_rows=5" in result.stdout
    with output.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["tile_id"] == "cv-covercrop-013"
    assert rows[0]["terrain_context"] == "convergent_low_context"


def test_cli_builder_can_print_fixture() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/build_terrain_context_fixture.py", "--stdout"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.splitlines()[0].startswith("tile_id,land_use,acres")
    assert "static_terrain_context" in result.stdout
