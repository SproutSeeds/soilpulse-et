from pathlib import Path

from nasa_space_to_soil_challenge.onboard_triage import load_candidate_tiles, plan_downlink
from scripts.build_hybrid_demo_fixture import build_hybrid_rows, write_hybrid_fixture


CSV_HEADER = (
    "tile_id,land_use,acres,source,product,doi,date_start,date_end,geometry_label,"
    "sample_count,valid_observation_count,latest_observation_date,et_anomaly_mm_day,"
    "vegetation_index_delta,cloud_fraction,days_since_seen,user_priority,confidence,"
    "full_chip_kib,summary_kib,processing_ms,energy_j\n"
)


def test_build_hybrid_rows_combines_real_and_synthetic_roles() -> None:
    rows = build_hybrid_rows([Path("tests/fixtures/ecostress_derived_sample.csv")])

    roles = {str(row["hybrid_role"]) for row in rows}

    assert "real_ecostress_knowledge_gap" in roles
    assert "synthetic_onboard_behavior" in roles
    assert len(rows) >= 4


def test_written_hybrid_fixture_loads_and_exercises_policy(tmp_path: Path) -> None:
    output = tmp_path / "hybrid.csv"
    rows = build_hybrid_rows([Path("tests/fixtures/ecostress_derived_sample.csv")])
    write_hybrid_fixture(rows, output)

    candidates = load_candidate_tiles(output)
    plan = plan_downlink(candidates)
    actions = {decision.action for decision in plan.decisions}

    assert {"priority_chip", "feature_summary", "defer"} <= actions


def test_build_hybrid_rows_uses_ranked_source_when_tile_ids_repeat(tmp_path: Path) -> None:
    older = tmp_path / "older.csv"
    newer = tmp_path / "newer.csv"
    older.write_text(
        CSV_HEADER
        + "repeat-tile,test tile,10,ecostress_derived,ECO_L3T_JET.002,doi,"
        "2024-07-01,2024-08-31,test,3,30,2024-08-21,0,0,0,10,0.8,0.20,96,8,180,4\n",
        encoding="utf-8",
    )
    newer.write_text(
        CSV_HEADER
        + "repeat-tile,test tile,10,ecostress_derived,ECO_L3T_JET.002,doi,"
        "2024-08-01,2024-09-30,test,3,15,2024-08-21,0,0,0,40,0.8,0.05,96,8,180,4\n",
        encoding="utf-8",
    )

    rows = build_hybrid_rows([older, newer])

    real_row = next(row for row in rows if row["hybrid_role"] == "real_ecostress_knowledge_gap")
    assert real_row["date_start"] == "2024-08-01"
    assert real_row["days_since_seen"] == 40
