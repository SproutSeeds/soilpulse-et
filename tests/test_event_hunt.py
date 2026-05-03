from nasa_space_to_soil_challenge.onboard_triage import CandidateTile

from scripts.score_event_hunt_candidates import (
    rank_candidates,
    score_event_interest,
)


def test_score_event_interest_marks_stress_candidate() -> None:
    candidate = CandidateTile(
        tile_id="stress",
        land_use="test",
        acres=10,
        et_anomaly_mm_day=-3.0,
        vegetation_index_delta=-0.10,
        cloud_fraction=0.05,
        days_since_seen=10,
        user_priority=0.9,
        confidence=0.8,
    )

    score, reason = score_event_interest(candidate)

    assert score > 0.45
    assert reason == "stress_event_candidate"


def test_score_event_interest_marks_knowledge_gap_candidate() -> None:
    candidate = CandidateTile(
        tile_id="gap",
        land_use="test",
        acres=10,
        et_anomaly_mm_day=0.0,
        vegetation_index_delta=0.0,
        cloud_fraction=0.10,
        days_since_seen=12,
        user_priority=0.7,
        confidence=0.05,
    )

    score, reason = score_event_interest(candidate)

    assert score > 0.45
    assert reason == "knowledge_gap_candidate"


def test_rank_candidates_reads_ecostress_fixture() -> None:
    rows = rank_candidates([__import__("pathlib").Path("tests/fixtures/ecostress_derived_sample.csv")])

    assert len(rows) == 4
    assert rows[0].reason == "knowledge_gap_candidate"
