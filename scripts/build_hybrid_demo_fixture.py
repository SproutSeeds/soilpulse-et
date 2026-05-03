#!/usr/bin/env python3
"""Build a labeled real-plus-synthetic hybrid fixture for the main demo."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from nasa_space_to_soil_challenge.onboard_triage import CandidateTile, demo_candidates, load_candidate_tiles

try:
    from scripts.score_event_hunt_candidates import rank_candidates
except ModuleNotFoundError:
    from score_event_hunt_candidates import rank_candidates

DEFAULT_REAL_INPUT = Path("tests/fixtures/ecostress_derived_sample.csv")
DEFAULT_OUTPUT = Path("tests/fixtures/candidate_tiles.hybrid.csv")

CANDIDATE_FIELDS = (
    "tile_id",
    "land_use",
    "acres",
    "et_anomaly_mm_day",
    "vegetation_index_delta",
    "cloud_fraction",
    "days_since_seen",
    "user_priority",
    "confidence",
    "full_chip_kib",
    "summary_kib",
    "processing_ms",
    "energy_j",
)
METADATA_FIELDS = (
    "source",
    "product",
    "doi",
    "date_start",
    "date_end",
    "geometry_label",
    "hybrid_role",
    "augmentation_note",
)


def build_hybrid_rows(real_paths: Iterable[Path]) -> list[dict[str, object]]:
    """Build rows combining the best real knowledge gap with synthetic scenario rows."""

    real_ranked = rank_candidates(real_paths)
    real_rows_by_id = _metadata_by_source_and_tile(real_paths)
    chosen_real = next((row for row in real_ranked if row.reason == "knowledge_gap_candidate"), None)

    rows: list[dict[str, object]] = []
    if chosen_real is not None:
        real_candidates = {
            (path.as_posix(), candidate.tile_id): candidate
            for path in real_paths
            for candidate in load_candidate_tiles(path)
        }
        original = real_candidates[(chosen_real.source_file, chosen_real.tile_id)]
        candidate = CandidateTile(
            tile_id=f"{original.tile_id}-ecostress",
            land_use=f"{original.land_use} ECOSTRESS sample",
            acres=original.acres,
            et_anomaly_mm_day=original.et_anomaly_mm_day,
            vegetation_index_delta=original.vegetation_index_delta,
            cloud_fraction=original.cloud_fraction,
            days_since_seen=original.days_since_seen,
            user_priority=original.user_priority,
            confidence=original.confidence,
            full_chip_kib=original.full_chip_kib,
            summary_kib=original.summary_kib,
            processing_ms=original.processing_ms,
            energy_j=original.energy_j,
        )
        metadata = real_rows_by_id.get((chosen_real.source_file, original.tile_id), {})
        rows.append(
            _row_from_candidate(
                candidate,
                metadata={
                    **metadata,
                    "hybrid_role": "real_ecostress_knowledge_gap",
                    "augmentation_note": "ET/cloud/confidence/freshness are ECOSTRESS-derived; no mission augmentation applied.",
                },
            )
        )

    for candidate in demo_candidates():
        rows.append(
            _row_from_candidate(
                candidate,
                metadata={
                    "source": "synthetic_mission_scenario",
                    "product": "",
                    "doi": "",
                    "date_start": "",
                    "date_end": "",
                    "geometry_label": "synthetic-resource-constrained-demo",
                    "hybrid_role": "synthetic_onboard_behavior",
                    "augmentation_note": (
                        "Synthetic row used to demonstrate chip/summary/defer behavior and planned onboard "
                        "features not present in the current ECOSTRESS sample."
                    ),
                },
            )
        )

    return rows


def write_hybrid_fixture(rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(CANDIDATE_FIELDS + METADATA_FIELDS)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="*", type=Path, default=[DEFAULT_REAL_INPUT])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rows = build_hybrid_rows(args.inputs)
    write_hybrid_fixture(rows, args.output)
    print(f"hybrid_rows={len(rows)}")
    print(args.output)


def _metadata_by_source_and_tile(paths: Iterable[Path]) -> dict[tuple[str, str], dict[str, str]]:
    metadata: dict[tuple[str, str], dict[str, str]] = {}
    for path in paths:
        if path.suffix.lower() != ".csv":
            continue
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                tile_id = str(row.get("tile_id", ""))
                key = (path.as_posix(), tile_id)
                if tile_id and key not in metadata:
                    metadata[key] = dict(row)
    return metadata


def _row_from_candidate(candidate: CandidateTile, *, metadata: dict[str, object]) -> dict[str, object]:
    row = asdict(candidate)
    for key in METADATA_FIELDS:
        row[key] = metadata.get(key, "")
    return row


if __name__ == "__main__":
    main()
