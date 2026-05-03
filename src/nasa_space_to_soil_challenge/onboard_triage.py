"""Small auditable onboard triage demo for the Phase 1 concept."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from random import Random
from typing import Iterable, Literal

DecisionAction = Literal["priority_chip", "feature_summary", "defer"]
BaselinePolicy = Literal["full_chip_all", "fixed_user_priority", "random"]
KnowledgeState = Literal["clear_recent", "stale", "partial_cloud", "obscured", "low_confidence"]


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


@dataclass(frozen=True)
class CandidateTile:
    """One candidate observation tile after lightweight onboard feature extraction."""

    tile_id: str
    land_use: str
    acres: float
    et_anomaly_mm_day: float
    vegetation_index_delta: float
    cloud_fraction: float
    days_since_seen: int
    user_priority: float
    confidence: float
    full_chip_kib: float = 96.0
    summary_kib: float = 8.0
    processing_ms: int = 180
    energy_j: float = 4.0


@dataclass(frozen=True)
class ResourceBudget:
    """Planning budget for one short onboard triage cycle."""

    downlink_kib: float = 384.0
    max_packets: int = 6
    processing_ms: int = 1_500
    energy_j: float = 42.0


@dataclass(frozen=True)
class TriageDecision:
    """Policy result for one candidate tile."""

    tile_id: str
    action: DecisionAction
    score: float
    evidence_quality: float
    knowledge_state: KnowledgeState
    reason: str
    downlink_kib: float
    processing_ms: int
    energy_j: float


@dataclass(frozen=True)
class TriagePlan:
    """Complete deterministic plan for a triage cycle."""

    budget: ResourceBudget
    decisions: tuple[TriageDecision, ...]

    @property
    def selected(self) -> tuple[TriageDecision, ...]:
        return tuple(decision for decision in self.decisions if decision.action != "defer")

    @property
    def deferred(self) -> tuple[TriageDecision, ...]:
        return tuple(decision for decision in self.decisions if decision.action == "defer")

    @property
    def used_downlink_kib(self) -> float:
        return round(sum(decision.downlink_kib for decision in self.selected), 3)

    @property
    def used_processing_ms(self) -> int:
        return sum(decision.processing_ms for decision in self.selected)

    @property
    def used_energy_j(self) -> float:
        return round(sum(decision.energy_j for decision in self.selected), 3)

    def as_dict(self) -> dict[str, object]:
        return {
            "budget": asdict(self.budget),
            "used": {
                "downlink_kib": self.used_downlink_kib,
                "processing_ms": self.used_processing_ms,
                "energy_j": self.used_energy_j,
                "packets": len(self.selected),
            },
            "decisions": [asdict(decision) for decision in self.decisions],
        }


@dataclass(frozen=True)
class TriageMetrics:
    """Compact metrics for paper and judging support."""

    candidate_count: int
    selected_count: int
    deferred_count: int
    full_chip_baseline_kib: float
    used_downlink_kib: float
    downlink_saved_kib: float
    downlink_saved_pct: float
    high_stress_candidates: int
    high_stress_selected: int
    high_stress_retention_pct: float
    cloudy_candidates: int
    cloudy_deferred: int
    cloud_waste_avoided_kib: float
    packet_budget_used_pct: float
    processing_budget_used_pct: float
    energy_budget_used_pct: float

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def stress_score(candidate: CandidateTile) -> float:
    """Score a tile for drought or irrigation-stress follow-up.

    The score is not a crop-health model. It is a transparent onboard policy
    proxy that can later be calibrated against ECOSTRESS ET products and field
    user priorities.
    """

    et_deficit = _clamp(-candidate.et_anomaly_mm_day / 4.0)
    vegetation_decline = _clamp(-candidate.vegetation_index_delta / 0.25)
    revisit_need = _clamp(candidate.days_since_seen / 14.0)
    user_value = _clamp(candidate.user_priority)
    confidence = _clamp(candidate.confidence)
    cloud_penalty = _clamp(candidate.cloud_fraction)

    raw_score = (
        0.42 * et_deficit
        + 0.20 * vegetation_decline
        + 0.12 * revisit_need
        + 0.18 * user_value
        + 0.08 * confidence
        - 0.45 * cloud_penalty
    )
    return round(_clamp(raw_score), 4)


def freshness_score(candidate: CandidateTile) -> float:
    """Estimate how fresh the last useful observation is on a 0-1 scale."""

    return round(_clamp(1.0 - (candidate.days_since_seen / 14.0)), 4)


def evidence_quality_score(candidate: CandidateTile) -> float:
    """Score how complete and reliable the current evidence is.

    This is separate from priority: a tile can be high priority because it
    looks risky, while still having low evidence quality because clouds,
    uncertainty, or stale observations limit what the system knows.
    """

    clear_view = _clamp(1.0 - candidate.cloud_fraction)
    quality = (
        0.55 * _clamp(candidate.confidence)
        + 0.25 * clear_view
        + 0.20 * freshness_score(candidate)
    )
    return round(_clamp(quality), 4)


def knowledge_state(candidate: CandidateTile) -> KnowledgeState:
    """Classify the tile's current state of knowledge for analyst review."""

    if candidate.cloud_fraction > 0.65:
        return "obscured"
    if candidate.confidence < 0.65:
        return "low_confidence"
    if candidate.cloud_fraction > 0.35:
        return "partial_cloud"
    if candidate.days_since_seen >= 10:
        return "stale"
    return "clear_recent"


def plan_downlink(
    candidates: Iterable[CandidateTile],
    budget: ResourceBudget = ResourceBudget(),
    *,
    chip_score_threshold: float = 0.62,
    min_summary_score: float = 0.30,
    max_cloud_fraction: float = 0.65,
) -> TriagePlan:
    """Build a deterministic downlink plan under simple SmallSat-like limits."""

    ordered = sorted(candidates, key=lambda tile: (stress_score(tile), tile.user_priority), reverse=True)
    decisions: list[TriageDecision] = []
    used_downlink = 0.0
    used_processing = 0
    used_energy = 0.0
    used_packets = 0

    for candidate in ordered:
        score = stress_score(candidate)
        if candidate.cloud_fraction > max_cloud_fraction:
            decisions.append(_defer(candidate, score, "cloud_screen"))
            continue
        if score < min_summary_score:
            decisions.append(_defer(candidate, score, "below_event_threshold"))
            continue
        if used_packets >= budget.max_packets:
            decisions.append(_defer(candidate, score, "packet_limit"))
            continue

        preferred_action: DecisionAction = "priority_chip" if score >= chip_score_threshold else "feature_summary"
        preferred_kib = candidate.full_chip_kib if preferred_action == "priority_chip" else candidate.summary_kib

        if _fits(candidate, preferred_kib, budget, used_downlink, used_processing, used_energy):
            decisions.append(
                TriageDecision(
                    tile_id=candidate.tile_id,
                    action=preferred_action,
                    score=score,
                    evidence_quality=evidence_quality_score(candidate),
                    knowledge_state=knowledge_state(candidate),
                    reason="selected_by_score",
                    downlink_kib=preferred_kib,
                    processing_ms=candidate.processing_ms,
                    energy_j=candidate.energy_j,
                )
            )
            used_downlink += preferred_kib
            used_processing += candidate.processing_ms
            used_energy += candidate.energy_j
            used_packets += 1
            continue

        if preferred_action == "priority_chip" and _fits(
            candidate,
            candidate.summary_kib,
            budget,
            used_downlink,
            used_processing,
            used_energy,
        ):
            decisions.append(
                TriageDecision(
                    tile_id=candidate.tile_id,
                    action="feature_summary",
                    score=score,
                    evidence_quality=evidence_quality_score(candidate),
                    knowledge_state=knowledge_state(candidate),
                    reason="chip_budget_exceeded_summary_kept",
                    downlink_kib=candidate.summary_kib,
                    processing_ms=candidate.processing_ms,
                    energy_j=candidate.energy_j,
                )
            )
            used_downlink += candidate.summary_kib
            used_processing += candidate.processing_ms
            used_energy += candidate.energy_j
            used_packets += 1
            continue

        decisions.append(_defer(candidate, score, "resource_limit"))

    return TriagePlan(budget=budget, decisions=tuple(decisions))


def baseline_plan(
    candidates: Iterable[CandidateTile],
    budget: ResourceBudget = ResourceBudget(),
    *,
    policy: BaselinePolicy = "fixed_user_priority",
    seed: int = 7,
) -> TriagePlan:
    """Build a simple full-chip baseline under the same resource budget."""

    rows = tuple(candidates)
    if policy == "fixed_user_priority":
        ordered = sorted(rows, key=lambda tile: tile.user_priority, reverse=True)
    elif policy == "random":
        ordered = list(rows)
        Random(seed).shuffle(ordered)
    else:
        ordered = rows

    decisions: list[TriageDecision] = []
    used_downlink = 0.0
    used_processing = 0
    used_energy = 0.0
    used_packets = 0
    for candidate in ordered:
        score = stress_score(candidate)
        if used_packets >= budget.max_packets:
            decisions.append(_defer(candidate, score, "packet_limit"))
            continue
        if _fits(candidate, candidate.full_chip_kib, budget, used_downlink, used_processing, used_energy):
            decisions.append(
                TriageDecision(
                    tile_id=candidate.tile_id,
                    action="priority_chip",
                    score=score,
                    evidence_quality=evidence_quality_score(candidate),
                    knowledge_state=knowledge_state(candidate),
                    reason=f"baseline_{policy}",
                    downlink_kib=candidate.full_chip_kib,
                    processing_ms=candidate.processing_ms,
                    energy_j=candidate.energy_j,
                )
            )
            used_downlink += candidate.full_chip_kib
            used_processing += candidate.processing_ms
            used_energy += candidate.energy_j
            used_packets += 1
        else:
            decisions.append(_defer(candidate, score, "resource_limit"))

    return TriagePlan(budget=budget, decisions=tuple(decisions))


def compute_metrics(
    candidates: Iterable[CandidateTile],
    plan: TriagePlan,
    *,
    high_stress_threshold: float = 0.62,
    cloudy_threshold: float = 0.65,
) -> TriageMetrics:
    """Compute auditable metrics for a triage plan."""

    rows = tuple(candidates)
    selected_ids = {decision.tile_id for decision in plan.selected}
    deferred_by_id = {decision.tile_id: decision for decision in plan.deferred}
    full_chip_baseline_kib = round(sum(candidate.full_chip_kib for candidate in rows), 3)
    downlink_saved_kib = round(full_chip_baseline_kib - plan.used_downlink_kib, 3)
    high_stress_ids = {
        candidate.tile_id for candidate in rows if stress_score(candidate) >= high_stress_threshold
    }
    cloudy = [candidate for candidate in rows if candidate.cloud_fraction > cloudy_threshold]
    cloudy_deferred = sum(
        1 for candidate in cloudy if deferred_by_id.get(candidate.tile_id, None) is not None
    )
    cloud_waste_avoided_kib = round(
        sum(candidate.full_chip_kib for candidate in cloudy if candidate.tile_id not in selected_ids),
        3,
    )

    return TriageMetrics(
        candidate_count=len(rows),
        selected_count=len(plan.selected),
        deferred_count=len(plan.deferred),
        full_chip_baseline_kib=full_chip_baseline_kib,
        used_downlink_kib=plan.used_downlink_kib,
        downlink_saved_kib=downlink_saved_kib,
        downlink_saved_pct=_pct(downlink_saved_kib, full_chip_baseline_kib),
        high_stress_candidates=len(high_stress_ids),
        high_stress_selected=len(high_stress_ids & selected_ids),
        high_stress_retention_pct=_pct(len(high_stress_ids & selected_ids), len(high_stress_ids)),
        cloudy_candidates=len(cloudy),
        cloudy_deferred=cloudy_deferred,
        cloud_waste_avoided_kib=cloud_waste_avoided_kib,
        packet_budget_used_pct=_pct(len(plan.selected), plan.budget.max_packets),
        processing_budget_used_pct=_pct(plan.used_processing_ms, plan.budget.processing_ms),
        energy_budget_used_pct=_pct(plan.used_energy_j, plan.budget.energy_j),
    )


def sensitivity_report(
    candidates: Iterable[CandidateTile],
    budgets: Iterable[ResourceBudget],
) -> list[dict[str, object]]:
    """Run the policy for multiple budgets and return metrics rows."""

    rows = tuple(candidates)
    report: list[dict[str, object]] = []
    for budget in budgets:
        plan = plan_downlink(rows, budget)
        metrics = compute_metrics(rows, plan)
        report.append(
            {
                "budget": asdict(budget),
                "used": plan.as_dict()["used"],
                "metrics": metrics.as_dict(),
            }
        )
    return report


def load_candidate_tiles(path: Path) -> tuple[CandidateTile, ...]:
    """Load candidate tiles from a JSON or CSV fixture."""

    if path.suffix.lower() == ".json":
        raw_rows = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw_rows, dict):
            raw_rows = raw_rows.get("candidates", [])
    elif path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            raw_rows = list(csv.DictReader(handle))
    else:
        raise ValueError(f"unsupported candidate fixture format: {path.suffix}")

    return tuple(_candidate_from_mapping(row) for row in raw_rows)


def _fits(
    candidate: CandidateTile,
    packet_kib: float,
    budget: ResourceBudget,
    used_downlink: float,
    used_processing: int,
    used_energy: float,
) -> bool:
    return (
        used_downlink + packet_kib <= budget.downlink_kib
        and used_processing + candidate.processing_ms <= budget.processing_ms
        and used_energy + candidate.energy_j <= budget.energy_j
    )


def _pct(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def _candidate_from_mapping(row: object) -> CandidateTile:
    if not isinstance(row, dict):
        raise TypeError("candidate row must be an object")
    return CandidateTile(
        tile_id=str(row["tile_id"]),
        land_use=str(row["land_use"]),
        acres=float(row["acres"]),
        et_anomaly_mm_day=float(row["et_anomaly_mm_day"]),
        vegetation_index_delta=float(row["vegetation_index_delta"]),
        cloud_fraction=float(row["cloud_fraction"]),
        days_since_seen=int(row["days_since_seen"]),
        user_priority=float(row["user_priority"]),
        confidence=float(row["confidence"]),
        full_chip_kib=float(row.get("full_chip_kib", 96.0)),
        summary_kib=float(row.get("summary_kib", 8.0)),
        processing_ms=int(row.get("processing_ms", 180)),
        energy_j=float(row.get("energy_j", 4.0)),
    )


def _defer(candidate: CandidateTile, score: float, reason: str) -> TriageDecision:
    return TriageDecision(
        tile_id=candidate.tile_id,
        action="defer",
        score=score,
        evidence_quality=evidence_quality_score(candidate),
        knowledge_state=knowledge_state(candidate),
        reason=reason,
        downlink_kib=0.0,
        processing_ms=0,
        energy_j=0.0,
    )


def demo_candidates() -> tuple[CandidateTile, ...]:
    """Return synthetic candidate tiles for a repeatable demo run."""

    return (
        CandidateTile(
            tile_id="cv-covercrop-013",
            land_use="cover-cropped almond block",
            acres=38.0,
            et_anomaly_mm_day=-3.3,
            vegetation_index_delta=-0.14,
            cloud_fraction=0.08,
            days_since_seen=9,
            user_priority=0.95,
            confidence=0.86,
        ),
        CandidateTile(
            tile_id="cv-pasture-021",
            land_use="rotational pasture",
            acres=54.0,
            et_anomaly_mm_day=-2.2,
            vegetation_index_delta=-0.18,
            cloud_fraction=0.12,
            days_since_seen=5,
            user_priority=0.70,
            confidence=0.78,
        ),
        CandidateTile(
            tile_id="cv-orchard-044",
            land_use="young orchard windbreak",
            acres=24.0,
            et_anomaly_mm_day=-1.6,
            vegetation_index_delta=-0.04,
            cloud_fraction=0.18,
            days_since_seen=12,
            user_priority=0.88,
            confidence=0.71,
        ),
        CandidateTile(
            tile_id="cv-rangeland-008",
            land_use="restoration rangeland",
            acres=120.0,
            et_anomaly_mm_day=-0.4,
            vegetation_index_delta=0.02,
            cloud_fraction=0.04,
            days_since_seen=14,
            user_priority=0.42,
            confidence=0.67,
        ),
        CandidateTile(
            tile_id="cv-riparian-016",
            land_use="riparian buffer",
            acres=17.0,
            et_anomaly_mm_day=-2.7,
            vegetation_index_delta=-0.11,
            cloud_fraction=0.72,
            days_since_seen=7,
            user_priority=0.90,
            confidence=0.62,
        ),
        CandidateTile(
            tile_id="cv-fallow-003",
            land_use="managed fallow soil-cover trial",
            acres=80.0,
            et_anomaly_mm_day=0.3,
            vegetation_index_delta=0.01,
            cloud_fraction=0.03,
            days_since_seen=2,
            user_priority=0.25,
            confidence=0.75,
        ),
        CandidateTile(
            tile_id="cv-vineyard-032",
            land_use="deficit-irrigated vineyard",
            acres=44.0,
            et_anomaly_mm_day=-3.8,
            vegetation_index_delta=-0.10,
            cloud_fraction=0.16,
            days_since_seen=10,
            user_priority=0.82,
            confidence=0.84,
            full_chip_kib=112.0,
        ),
    )


def format_plan_markdown(plan: TriagePlan) -> str:
    """Render a compact markdown table for docs and paper support."""

    lines = [
        "| tile | action | priority | evidence | knowledge | downlink KiB | reason |",
        "| --- | --- | ---: | ---: | --- | ---: | --- |",
    ]
    for decision in plan.decisions:
        lines.append(
            "| "
            f"{decision.tile_id} | "
            f"{decision.action} | "
            f"{decision.score:.4f} | "
            f"{decision.evidence_quality:.4f} | "
            f"{decision.knowledge_state} | "
            f"{decision.downlink_kib:.1f} | "
            f"{decision.reason} |"
        )
    lines.append("")
    lines.append(
        "Used: "
        f"{plan.used_downlink_kib:.1f} KiB, "
        f"{plan.used_processing_ms} ms, "
        f"{plan.used_energy_j:.1f} J, "
        f"{len(plan.selected)} packets."
    )
    return "\n".join(lines)


def format_metrics_markdown(metrics: TriageMetrics) -> str:
    """Render a compact metrics table."""

    rows = [
        ("candidate count", str(metrics.candidate_count)),
        ("selected packets", str(metrics.selected_count)),
        ("full-chip baseline", f"{metrics.full_chip_baseline_kib:.1f} KiB"),
        ("used downlink", f"{metrics.used_downlink_kib:.1f} KiB"),
        ("downlink saved", f"{metrics.downlink_saved_kib:.1f} KiB ({metrics.downlink_saved_pct:.2f}%)"),
        (
            "high-stress retention",
            f"{metrics.high_stress_selected}/{metrics.high_stress_candidates} "
            f"({metrics.high_stress_retention_pct:.2f}%)",
        ),
        ("cloudy candidates deferred", f"{metrics.cloudy_deferred}/{metrics.cloudy_candidates}"),
        ("cloud waste avoided", f"{metrics.cloud_waste_avoided_kib:.1f} KiB"),
        ("packet budget used", f"{metrics.packet_budget_used_pct:.2f}%"),
        ("processing budget used", f"{metrics.processing_budget_used_pct:.2f}%"),
        ("energy budget used", f"{metrics.energy_budget_used_pct:.2f}%"),
    ]
    lines = ["| metric | value |", "| --- | ---: |"]
    lines.extend(f"| {name} | {value} |" for name, value in rows)
    return "\n".join(lines)


def format_sensitivity_markdown(report: list[dict[str, object]]) -> str:
    """Render budget sensitivity rows."""

    lines = [
        "| downlink KiB | packets | used KiB | selected | saved % | high-stress retained |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report:
        budget = row["budget"]
        used = row["used"]
        metrics = row["metrics"]
        if not isinstance(budget, dict) or not isinstance(used, dict) or not isinstance(metrics, dict):
            raise TypeError("invalid sensitivity report row")
        lines.append(
            "| "
            f"{float(budget['downlink_kib']):.0f} | "
            f"{int(budget['max_packets'])} | "
            f"{float(used['downlink_kib']):.1f} | "
            f"{int(used['packets'])} | "
            f"{float(metrics['downlink_saved_pct']):.2f} | "
            f"{float(metrics['high_stress_retention_pct']):.2f}% |"
        )
    return "\n".join(lines)
