#!/usr/bin/env python3
"""Run the synthetic onboard triage demo."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from nasa_space_to_soil_challenge.onboard_triage import (
    ResourceBudget,
    compute_metrics,
    demo_candidates,
    format_metrics_markdown,
    format_plan_markdown,
    format_sensitivity_markdown,
    load_candidate_tiles,
    plan_downlink,
    sensitivity_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downlink-kib", type=float, default=384.0)
    parser.add_argument("--max-packets", type=int, default=6)
    parser.add_argument("--processing-ms", type=int, default=1_500)
    parser.add_argument("--energy-j", type=float, default=42.0)
    parser.add_argument("--input", type=Path, default=None, help="Optional CSV or JSON candidate fixture.")
    parser.add_argument("--include-metrics", action="store_true", help="Include metrics in output.")
    parser.add_argument("--sensitivity", action="store_true", help="Run 64, 128, and 384 KiB budget sensitivity.")
    parser.add_argument("--format", choices=("json", "markdown", "csv"), default="markdown")
    args = parser.parse_args()

    budget = ResourceBudget(
        downlink_kib=args.downlink_kib,
        max_packets=args.max_packets,
        processing_ms=args.processing_ms,
        energy_j=args.energy_j,
    )
    candidates = load_candidate_tiles(args.input) if args.input is not None else demo_candidates()
    plan = plan_downlink(candidates, budget)
    metrics = compute_metrics(candidates, plan)

    if args.format == "json":
        payload = {"plan": plan.as_dict()}
        if args.include_metrics:
            payload["metrics"] = metrics.as_dict()
        if args.sensitivity:
            payload["sensitivity"] = sensitivity_report(
                candidates,
                (
                    ResourceBudget(downlink_kib=64.0, max_packets=3, processing_ms=900, energy_j=18.0),
                    ResourceBudget(downlink_kib=128.0, max_packets=4, processing_ms=1_100, energy_j=28.0),
                    ResourceBudget(downlink_kib=384.0, max_packets=6, processing_ms=1_500, energy_j=42.0),
                ),
            )
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif args.format == "csv":
        writer = csv.DictWriter(
            sys.stdout,
            fieldnames=(
                "tile_id",
                "action",
                "score",
                "evidence_quality",
                "knowledge_state",
                "reason",
                "downlink_kib",
                "processing_ms",
                "energy_j",
            ),
        )
        writer.writeheader()
        for decision in plan.decisions:
            writer.writerow(
                {
                    "tile_id": decision.tile_id,
                    "action": decision.action,
                    "score": f"{decision.score:.4f}",
                    "evidence_quality": f"{decision.evidence_quality:.4f}",
                    "knowledge_state": decision.knowledge_state,
                    "reason": decision.reason,
                    "downlink_kib": f"{decision.downlink_kib:.1f}",
                    "processing_ms": decision.processing_ms,
                    "energy_j": f"{decision.energy_j:.1f}",
                }
            )
    else:
        print(format_plan_markdown(plan))
        if args.include_metrics:
            print()
            print(format_metrics_markdown(metrics))
        if args.sensitivity:
            print()
            print(format_sensitivity_markdown(
                sensitivity_report(
                    candidates,
                    (
                        ResourceBudget(downlink_kib=64.0, max_packets=3, processing_ms=900, energy_j=18.0),
                        ResourceBudget(downlink_kib=128.0, max_packets=4, processing_ms=1_100, energy_j=28.0),
                        ResourceBudget(downlink_kib=384.0, max_packets=6, processing_ms=1_500, energy_j=42.0),
                    ),
                )
            ))


if __name__ == "__main__":
    main()
