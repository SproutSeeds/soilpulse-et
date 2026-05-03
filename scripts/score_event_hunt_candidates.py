#!/usr/bin/env python3
"""Rank real or synthetic candidate rows for event-hunt usefulness."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from nasa_space_to_soil_challenge.onboard_triage import (
    CandidateTile,
    evidence_quality_score,
    knowledge_state,
    load_candidate_tiles,
    stress_score,
)


@dataclass(frozen=True)
class EventHuntRow:
    """One ranked tile/window candidate for real-data hunting."""

    source_file: str
    tile_id: str
    land_use: str
    date_window: str
    event_score: float
    stress_priority: float
    evidence_quality: float
    knowledge_state: str
    reason: str


def score_event_interest(candidate: CandidateTile) -> tuple[float, str]:
    """Score whether a tile/window is useful for the next data-hunt pass."""

    et_deficit = _clamp(-candidate.et_anomaly_mm_day / 3.0)
    vegetation_decline = _clamp(-candidate.vegetation_index_delta / 0.20)
    stale_signal = _clamp(candidate.days_since_seen / 21.0)
    cloud_signal = _clamp(candidate.cloud_fraction)
    low_confidence_signal = _clamp(1.0 - candidate.confidence)
    user_value = _clamp(candidate.user_priority)

    stress_signal = (
        0.45 * et_deficit
        + 0.20 * vegetation_decline
        + 0.20 * user_value
        + 0.15 * stale_signal
    )
    knowledge_gap = 0.45 * low_confidence_signal + 0.35 * cloud_signal + 0.20 * stale_signal

    if stress_signal >= 0.45 and candidate.cloud_fraction <= 0.65:
        return round(_clamp(stress_signal), 4), "stress_event_candidate"
    if knowledge_gap >= 0.45:
        return round(_clamp(knowledge_gap), 4), "knowledge_gap_candidate"
    return round(_clamp(max(stress_signal, knowledge_gap)), 4), "low_event_signal"


def rank_candidates(paths: Iterable[Path]) -> list[EventHuntRow]:
    rows: list[EventHuntRow] = []
    for path in paths:
        for candidate, metadata in _load_with_metadata(path):
            event_score, reason = score_event_interest(candidate)
            rows.append(
                EventHuntRow(
                    source_file=path.as_posix(),
                    tile_id=candidate.tile_id,
                    land_use=candidate.land_use,
                    date_window=_date_window(metadata),
                    event_score=event_score,
                    stress_priority=stress_score(candidate),
                    evidence_quality=evidence_quality_score(candidate),
                    knowledge_state=knowledge_state(candidate),
                    reason=reason,
                )
            )
    return sorted(rows, key=lambda row: (row.event_score, row.stress_priority), reverse=True)


def format_markdown(rows: Iterable[EventHuntRow]) -> str:
    lines = [
        "| tile | land use | window | event | priority | evidence | state | reason |",
        "| --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row.tile_id} | "
            f"{row.land_use} | "
            f"{row.date_window} | "
            f"{row.event_score:.4f} | "
            f"{row.stress_priority:.4f} | "
            f"{row.evidence_quality:.4f} | "
            f"{row.knowledge_state} | "
            f"{row.reason} |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        default=[Path("tests/fixtures/ecostress_derived_sample.csv")],
        help="Candidate CSV/JSON files to rank.",
    )
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--format", choices=("markdown", "csv"), default="markdown")
    args = parser.parse_args()

    rows = rank_candidates(args.inputs)[: args.limit]
    if args.format == "csv":
        writer = csv.DictWriter(
            __import__("sys").stdout,
            fieldnames=(
                "source_file",
                "tile_id",
                "land_use",
                "date_window",
                "event_score",
                "stress_priority",
                "evidence_quality",
                "knowledge_state",
                "reason",
            ),
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)
    else:
        print(format_markdown(rows))


def _load_with_metadata(path: Path) -> tuple[tuple[CandidateTile, dict[str, str]], ...]:
    candidates = load_candidate_tiles(path)
    metadata_rows = _read_metadata(path)
    return tuple(
        (candidate, metadata_rows.get(candidate.tile_id, {}))
        for candidate in candidates
    )


def _read_metadata(path: Path) -> dict[str, dict[str, str]]:
    if path.suffix.lower() != ".csv":
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {
            str(row.get("tile_id", "")): dict(row)
            for row in csv.DictReader(handle)
            if row.get("tile_id")
        }


def _date_window(metadata: dict[str, str]) -> str:
    start = metadata.get("date_start", "")
    end = metadata.get("date_end", "")
    if start and end:
        return f"{start}..{end}"
    return "synthetic"


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


if __name__ == "__main__":
    main()
