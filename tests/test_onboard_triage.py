from pathlib import Path

from nasa_space_to_soil_challenge.onboard_triage import (
    CandidateTile,
    ResourceBudget,
    baseline_plan,
    compute_metrics,
    demo_candidates,
    evidence_quality_score,
    freshness_score,
    knowledge_state,
    load_candidate_tiles,
    plan_downlink,
    sensitivity_report,
    stress_score,
)


def test_stress_score_rewards_et_deficit_and_penalizes_clouds() -> None:
    clear_stressed = CandidateTile(
        tile_id="clear",
        land_use="test",
        acres=10,
        et_anomaly_mm_day=-3.0,
        vegetation_index_delta=-0.12,
        cloud_fraction=0.05,
        days_since_seen=8,
        user_priority=0.8,
        confidence=0.8,
    )
    cloudy_stressed = CandidateTile(
        tile_id="cloudy",
        land_use="test",
        acres=10,
        et_anomaly_mm_day=-3.0,
        vegetation_index_delta=-0.12,
        cloud_fraction=0.70,
        days_since_seen=8,
        user_priority=0.8,
        confidence=0.8,
    )

    assert stress_score(clear_stressed) > stress_score(cloudy_stressed)


def test_evidence_quality_tracks_freshness_confidence_and_clouds() -> None:
    fresh_clear = CandidateTile(
        tile_id="fresh-clear",
        land_use="test",
        acres=10,
        et_anomaly_mm_day=-1.0,
        vegetation_index_delta=-0.05,
        cloud_fraction=0.05,
        days_since_seen=1,
        user_priority=0.5,
        confidence=0.9,
    )
    stale_cloudy = CandidateTile(
        tile_id="stale-cloudy",
        land_use="test",
        acres=10,
        et_anomaly_mm_day=-1.0,
        vegetation_index_delta=-0.05,
        cloud_fraction=0.72,
        days_since_seen=12,
        user_priority=0.5,
        confidence=0.55,
    )

    assert freshness_score(fresh_clear) > freshness_score(stale_cloudy)
    assert evidence_quality_score(fresh_clear) > evidence_quality_score(stale_cloudy)
    assert knowledge_state(stale_cloudy) == "obscured"


def test_plan_downlink_respects_packet_and_downlink_limits() -> None:
    budget = ResourceBudget(downlink_kib=128.0, max_packets=2, processing_ms=1_500, energy_j=42.0)

    plan = plan_downlink(demo_candidates(), budget)

    assert len(plan.selected) <= budget.max_packets
    assert plan.used_downlink_kib <= budget.downlink_kib
    assert plan.used_processing_ms <= budget.processing_ms
    assert plan.used_energy_j <= budget.energy_j


def test_plan_keeps_high_score_event_as_chip_when_budget_allows() -> None:
    plan = plan_downlink(demo_candidates(), ResourceBudget(downlink_kib=384.0))

    selected_actions = {decision.tile_id: decision.action for decision in plan.selected}
    decisions_by_id = {decision.tile_id: decision for decision in plan.decisions}

    assert selected_actions["cv-covercrop-013"] == "priority_chip"
    assert "cv-riparian-016" not in selected_actions
    assert decisions_by_id["cv-riparian-016"].knowledge_state == "obscured"
    assert decisions_by_id["cv-vineyard-032"].knowledge_state == "stale"


def test_load_candidate_tiles_from_csv_fixture() -> None:
    fixture = Path(__file__).parent / "fixtures" / "candidate_tiles.synthetic.csv"

    candidates = load_candidate_tiles(fixture)

    assert len(candidates) == 7
    assert candidates[0].tile_id == "cv-covercrop-013"
    assert candidates[-1].full_chip_kib == 112.0


def test_metrics_compare_to_full_chip_baseline() -> None:
    candidates = demo_candidates()
    plan = plan_downlink(candidates, ResourceBudget(downlink_kib=384.0))

    metrics = compute_metrics(candidates, plan)

    assert metrics.full_chip_baseline_kib == 688.0
    assert metrics.used_downlink_kib == 224.0
    assert metrics.downlink_saved_kib == 464.0
    assert metrics.high_stress_selected == metrics.high_stress_candidates
    assert metrics.cloudy_deferred == 1


def test_baseline_plan_respects_budget() -> None:
    budget = ResourceBudget(downlink_kib=128.0, max_packets=2, processing_ms=1_500, energy_j=42.0)

    plan = baseline_plan(demo_candidates(), budget, policy="fixed_user_priority")

    assert len(plan.selected) <= 2
    assert plan.used_downlink_kib <= 128.0
    assert all(decision.action in {"priority_chip", "defer"} for decision in plan.decisions)


def test_sensitivity_report_contains_requested_budgets() -> None:
    budgets = (
        ResourceBudget(downlink_kib=64.0, max_packets=3, processing_ms=900, energy_j=18.0),
        ResourceBudget(downlink_kib=384.0, max_packets=6, processing_ms=1_500, energy_j=42.0),
    )

    report = sensitivity_report(demo_candidates(), budgets)

    assert [row["budget"]["downlink_kib"] for row in report] == [64.0, 384.0]
    assert report[0]["metrics"]["candidate_count"] == 7
