#!/usr/bin/env python3
"""Build deterministic SVG charts for the final pitch screen share."""

from __future__ import annotations

import argparse
from html import escape
from pathlib import Path

from nasa_space_to_soil_challenge.onboard_triage import (
    ResourceBudget,
    compute_metrics,
    load_candidate_tiles,
    plan_downlink,
    sensitivity_report,
)


ACTION_COLORS = {
    "priority_chip": "#2563eb",
    "feature_summary": "#059669",
    "defer": "#6b7280",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("tests/fixtures/candidate_tiles.hybrid.csv"),
        help="Hybrid candidate fixture.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/diagrams"),
        help="Directory for generated SVG charts.",
    )
    args = parser.parse_args()

    candidates = load_candidate_tiles(args.input)
    plan = plan_downlink(candidates)
    metrics = compute_metrics(candidates, plan)
    sensitivity = sensitivity_report(
        candidates,
        (
            ResourceBudget(downlink_kib=64.0, max_packets=3, processing_ms=900, energy_j=18.0),
            ResourceBudget(downlink_kib=128.0, max_packets=4, processing_ms=1_100, energy_j=28.0),
            ResourceBudget(downlink_kib=384.0, max_packets=6, processing_ms=1_500, energy_j=42.0),
        ),
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    optimization_path = args.output_dir / "video_downlink_optimization.svg"
    decisions_path = args.output_dir / "video_tile_decisions.svg"
    optimization_path.write_text(build_optimization_svg(metrics, sensitivity), encoding="utf-8")
    decisions_path.write_text(build_decisions_svg(plan), encoding="utf-8")
    print(optimization_path)
    print(decisions_path)


def build_optimization_svg(metrics: object, sensitivity: list[dict[str, object]]) -> str:
    full = float(getattr(metrics, "full_chip_baseline_kib"))
    used = float(getattr(metrics, "used_downlink_kib"))
    saved = float(getattr(metrics, "downlink_saved_kib"))
    saved_pct = float(getattr(metrics, "downlink_saved_pct"))
    selected = int(getattr(metrics, "selected_count"))
    deferred = int(getattr(metrics, "deferred_count"))
    high_selected = int(getattr(metrics, "high_stress_selected"))
    high_total = int(getattr(metrics, "high_stress_candidates"))
    cloudy_deferred = int(getattr(metrics, "cloudy_deferred"))
    cloudy_total = int(getattr(metrics, "cloudy_candidates"))

    max_bar = 760.0
    full_width = max_bar
    used_width = max_bar * (used / full)
    saved_width = max_bar * (saved / full)
    budget_points = _sensitivity_points(sensitivity)
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in budget_points)
    circles = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#2563eb"/>'
        for x, y in budget_points
    )
    labels = "\n".join(_sensitivity_label(row, x, y) for row, (x, y) in zip(sensitivity, budget_points))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" role="img" aria-label="SoilPulse-ET downlink optimization chart">
<rect width="1600" height="900" fill="#f8fafc"/>
<text x="72" y="78" font-family="Arial, sans-serif" font-size="42" font-weight="700" fill="#111827">SoilPulse-ET optimizes scarce downlink</text>
<text x="72" y="122" font-family="Arial, sans-serif" font-size="24" fill="#4b5563">Hybrid demo: one ECOSTRESS-derived knowledge-gap row plus labeled mission-scenario rows</text>

<rect x="72" y="170" width="900" height="410" rx="18" fill="#ffffff" stroke="#d1d5db"/>
<text x="112" y="226" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#111827">Downlink used per contact</text>

<text x="112" y="296" font-family="Arial, sans-serif" font-size="24" fill="#374151">Full-chip baseline</text>
<rect x="112" y="316" width="{full_width:.1f}" height="58" rx="10" fill="#dbeafe"/>
<rect x="112" y="316" width="{full_width:.1f}" height="58" rx="10" fill="#2563eb"/>
<text x="898" y="354" text-anchor="end" font-family="Arial, sans-serif" font-size="26" font-weight="700" fill="#ffffff">{full:.0f} KiB</text>

<text x="112" y="430" font-family="Arial, sans-serif" font-size="24" fill="#374151">SoilPulse-ET selected packets</text>
<rect x="112" y="450" width="{full_width:.1f}" height="58" rx="10" fill="#e5e7eb"/>
<rect x="112" y="450" width="{used_width:.1f}" height="58" rx="10" fill="#059669"/>
<rect x="{112 + used_width:.1f}" y="450" width="{saved_width:.1f}" height="58" fill="#a7f3d0"/>
<text x="{112 + max(used_width - 18, 120):.1f}" y="488" text-anchor="end" font-family="Arial, sans-serif" font-size="26" font-weight="700" fill="#ffffff">{used:.0f} KiB</text>
<text x="898" y="488" text-anchor="end" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="#065f46">saved {saved:.0f} KiB / {saved_pct:.2f}%</text>

<rect x="1020" y="170" width="508" height="410" rx="18" fill="#ffffff" stroke="#d1d5db"/>
<text x="1060" y="226" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#111827">What survived the triage?</text>
{_metric_card(1060, 270, "Selected packets", f"{selected}", "#2563eb")}
{_metric_card(1298, 270, "Deferred tiles", f"{deferred}", "#6b7280")}
{_metric_card(1060, 398, "High-stress retained", f"{high_selected}/{high_total}", "#059669")}
{_metric_card(1298, 398, "Cloudy deferred", f"{cloudy_deferred}/{cloudy_total}", "#b45309")}

<rect x="72" y="626" width="1456" height="190" rx="18" fill="#ffffff" stroke="#d1d5db"/>
<text x="112" y="680" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#111827">Budget sensitivity: high-stress retention stays at 100%</text>
<line x1="180" y1="766" x2="810" y2="766" stroke="#d1d5db" stroke-width="3"/>
<polyline points="{polyline}" fill="none" stroke="#2563eb" stroke-width="5"/>
{circles}
{labels}
<text x="930" y="716" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="#111827">Next optimization path</text>
<text x="930" y="754" font-family="Arial, sans-serif" font-size="22" fill="#374151">Replace synthetic HLS + terrain fixtures with real ingestion, then tune</text>
<text x="930" y="786" font-family="Arial, sans-serif" font-size="22" fill="#374151">chip/summary thresholds against user priorities and field feedback.</text>

<text x="72" y="864" font-family="Arial, sans-serif" font-size="18" fill="#6b7280">Generated from tests/fixtures/candidate_tiles.hybrid.csv via scripts/build_video_charts.py. This is a policy demonstrator, not flight software or crop-stress validation.</text>
</svg>
"""


def build_decisions_svg(plan: object) -> str:
    decisions = list(getattr(plan, "decisions"))
    rows = []
    y = 178
    for decision in decisions:
        score = float(getattr(decision, "score"))
        evidence = float(getattr(decision, "evidence_quality"))
        action = str(getattr(decision, "action"))
        color = ACTION_COLORS.get(action, "#6b7280")
        bar_width = 720.0 * score
        evidence_x = 662.0 + 720.0 * evidence
        tile_id = str(getattr(decision, "tile_id"))
        source_note = "real ECOSTRESS knowledge-gap row" if tile_id.endswith("-ecostress") else "mission-scenario row"
        rows.append(
            f"""
<text x="88" y="{y + 28}" font-family="Arial, sans-serif" font-size="21" font-weight="700" fill="#111827">{escape(tile_id)}</text>
<text x="88" y="{y + 56}" font-family="Arial, sans-serif" font-size="17" fill="#6b7280">{escape(source_note)}</text>
<rect x="662" y="{y}" width="720" height="34" rx="8" fill="#e5e7eb"/>
<rect x="662" y="{y}" width="{bar_width:.1f}" height="34" rx="8" fill="{color}"/>
<line x1="{evidence_x:.1f}" y1="{y - 6}" x2="{evidence_x:.1f}" y2="{y + 40}" stroke="#111827" stroke-width="3"/>
<text x="1524" y="{y + 27}" text-anchor="end" font-family="Arial, sans-serif" font-size="20" fill="#111827">priority {score:.2f} / evidence {evidence:.2f}</text>
<text x="662" y="{y + 62}" font-family="Arial, sans-serif" font-size="17" font-weight="700" fill="{color}">{escape(action)}</text>
"""
        )
        y += 76

    legend = "\n".join(
        f'<rect x="{x}" y="102" width="20" height="20" rx="4" fill="{color}"/><text x="{x + 30}" y="120" font-family="Arial, sans-serif" font-size="19" fill="#374151">{label}</text>'
        for x, color, label in (
            (662, ACTION_COLORS["priority_chip"], "priority chip"),
            (870, ACTION_COLORS["feature_summary"], "feature summary"),
            (1115, ACTION_COLORS["defer"], "defer"),
        )
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" role="img" aria-label="SoilPulse-ET tile decision chart">
<rect width="1600" height="900" fill="#f8fafc"/>
<text x="72" y="78" font-family="Arial, sans-serif" font-size="42" font-weight="700" fill="#111827">Tile-level decisions: priority versus evidence</text>
<text x="72" y="122" font-family="Arial, sans-serif" font-size="24" fill="#4b5563">Bars show event priority. Black ticks show evidence quality. Color shows the onboard packet action.</text>
{legend}
<text x="88" y="160" font-family="Arial, sans-serif" font-size="19" font-weight="700" fill="#374151">Candidate tile</text>
<text x="662" y="160" font-family="Arial, sans-serif" font-size="19" font-weight="700" fill="#374151">Onboard score and action</text>
{"".join(rows)}
<text x="72" y="850" font-family="Arial, sans-serif" font-size="20" fill="#6b7280">Screen-share note: this chart explains why the system sends two priority chips, sends two compact summaries, and defers cloudy or low-confidence tiles.</text>
</svg>
"""


def _metric_card(x: int, y: int, label: str, value: str, color: str) -> str:
    return f"""
<rect x="{x}" y="{y}" width="190" height="92" rx="14" fill="#f9fafb" stroke="#e5e7eb"/>
<text x="{x + 20}" y="{y + 35}" font-family="Arial, sans-serif" font-size="18" fill="#4b5563">{escape(label)}</text>
<text x="{x + 20}" y="{y + 73}" font-family="Arial, sans-serif" font-size="38" font-weight="700" fill="{color}">{escape(value)}</text>
"""


def _sensitivity_points(sensitivity: list[dict[str, object]]) -> list[tuple[float, float]]:
    x_values = (240.0, 480.0, 720.0)
    points: list[tuple[float, float]] = []
    for x, row in zip(x_values, sensitivity):
        metrics = row["metrics"]
        if not isinstance(metrics, dict):
            raise TypeError("invalid sensitivity metrics")
        saved_pct = float(metrics["downlink_saved_pct"])
        y = 800.0 - (saved_pct / 100.0) * 105.0
        points.append((x, y))
    return points


def _sensitivity_label(row: dict[str, object], x: float, y: float) -> str:
    budget = row["budget"]
    metrics = row["metrics"]
    if not isinstance(budget, dict) or not isinstance(metrics, dict):
        raise TypeError("invalid sensitivity row")
    budget_kib = float(budget["downlink_kib"])
    saved_pct = float(metrics["downlink_saved_pct"])
    return (
        f'<text x="{x:.1f}" y="{y - 18:.1f}" text-anchor="middle" '
        'font-family="Arial, sans-serif" font-size="18" font-weight="700" fill="#111827">'
        f"{saved_pct:.2f}% saved</text>"
        f'<text x="{x:.1f}" y="805" text-anchor="middle" '
        'font-family="Arial, sans-serif" font-size="18" fill="#4b5563">'
        f"{budget_kib:.0f} KiB budget</text>"
    )


if __name__ == "__main__":
    main()
