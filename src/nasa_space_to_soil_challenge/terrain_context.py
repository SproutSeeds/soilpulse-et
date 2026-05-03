"""Static terrain-context helpers for SoilPulse-ET fixtures.

The helpers in this module treat NASADEM/SRTM-style elevation derivatives as
contextual support only. They classify simple static terrain signals for
planning and review; they are not a hydrology model.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from io import StringIO
from pathlib import Path
from typing import Iterable, Literal, Mapping

SlopeClass = Literal["flat", "gentle", "moderate", "steep"]
RelativeElevationClass = Literal["low", "mid", "high"]
TerrainContextLabel = Literal[
    "convergent_low_context",
    "retention_context",
    "runoff_shedding_context",
    "mixed_terrain_context",
    "neutral_context",
]

TERRAIN_CONTEXT_FIELDS = (
    "tile_id",
    "land_use",
    "acres",
    "slope_degrees",
    "relative_elevation_m",
    "low_point_signal",
    "flow_accumulation_proxy",
    "slope_class",
    "relative_elevation_class",
    "terrain_context",
    "retention_context_score",
    "runoff_context_score",
    "convergence_context_score",
    "flow_proxy_used",
)

TRIAGE_METADATA_FIELDS = (
    "source",
    "product",
    "doi",
    "date_start",
    "date_end",
    "geometry_label",
    "hybrid_role",
    "augmentation_note",
)

TERRAIN_CONTEXT_FIELDNAMES = TERRAIN_CONTEXT_FIELDS + TRIAGE_METADATA_FIELDS


@dataclass(frozen=True)
class TerrainSample:
    """One tile-level row of static terrain derivative inputs."""

    tile_id: str
    land_use: str
    acres: float
    slope_degrees: float
    relative_elevation_m: float
    low_point_signal: float
    flow_accumulation_proxy: float | None = None
    source: str = "synthetic_terrain_context"
    product: str = "NASADEM/SRTM-style elevation derivatives"
    doi: str = ""
    date_start: str = ""
    date_end: str = ""
    geometry_label: str = "central-valley-synthetic-terrain-context"


@dataclass(frozen=True)
class TerrainContext:
    """Compact terrain-context classification for a candidate tile."""

    tile_id: str
    slope_class: SlopeClass
    relative_elevation_class: RelativeElevationClass
    terrain_context: TerrainContextLabel
    retention_context_score: float
    runoff_context_score: float
    convergence_context_score: float
    flow_proxy_used: bool
    note: str = "contextual support only; not a hydrology model"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def classify_slope(slope_degrees: float) -> SlopeClass:
    """Classify a non-negative slope in degrees."""

    if slope_degrees < 0:
        raise ValueError("slope_degrees must be non-negative")
    if slope_degrees <= 2.0:
        return "flat"
    if slope_degrees <= 6.0:
        return "gentle"
    if slope_degrees <= 12.0:
        return "moderate"
    return "steep"


def classify_relative_elevation(relative_elevation_m: float) -> RelativeElevationClass:
    """Classify a local relative-elevation signal in meters."""

    if relative_elevation_m <= -1.5:
        return "low"
    if relative_elevation_m >= 3.0:
        return "high"
    return "mid"


def classify_terrain_context(sample: TerrainSample) -> TerrainContext:
    """Classify static terrain context from slope, low-point, and flow signals."""

    if sample.slope_degrees < 0:
        raise ValueError("slope_degrees must be non-negative")

    slope_class = classify_slope(sample.slope_degrees)
    relative_class = classify_relative_elevation(sample.relative_elevation_m)
    slope_signal = _clamp(sample.slope_degrees / 15.0)
    relative_low_signal = _clamp((6.0 - sample.relative_elevation_m) / 9.0)
    relative_high_signal = _clamp((sample.relative_elevation_m - 1.0) / 9.0)
    low_point_signal = _clamp(sample.low_point_signal)
    flow_signal = _clamp(sample.flow_accumulation_proxy or 0.0)
    flow_proxy_used = sample.flow_accumulation_proxy is not None

    retention_score = _round_score(
        (0.48 * low_point_signal)
        + (0.32 * relative_low_signal)
        + (0.20 * (1.0 - _clamp(sample.slope_degrees / 12.0)))
    )
    runoff_score = _round_score(
        (0.65 * slope_signal)
        + (0.25 * relative_high_signal)
        + (0.10 * (1.0 - low_point_signal))
    )
    convergence_score = _round_score(
        (0.50 * low_point_signal)
        + (0.30 * flow_signal)
        + (0.20 * relative_low_signal)
    )

    if flow_proxy_used and convergence_score >= 0.68:
        label: TerrainContextLabel = "convergent_low_context"
    elif retention_score >= 0.68 and slope_class in {"flat", "gentle"}:
        label = "retention_context"
    elif runoff_score >= 0.68 and slope_class in {"moderate", "steep"}:
        label = "runoff_shedding_context"
    elif retention_score >= 0.52 and runoff_score >= 0.52:
        label = "mixed_terrain_context"
    else:
        label = "neutral_context"

    return TerrainContext(
        tile_id=sample.tile_id,
        slope_class=slope_class,
        relative_elevation_class=relative_class,
        terrain_context=label,
        retention_context_score=retention_score,
        runoff_context_score=runoff_score,
        convergence_context_score=convergence_score,
        flow_proxy_used=flow_proxy_used,
    )


def build_terrain_context_rows(samples: Iterable[TerrainSample]) -> list[dict[str, object]]:
    """Build CSV-ready terrain-context rows with triage-compatible metadata."""

    rows: list[dict[str, object]] = []
    for sample in samples:
        context = classify_terrain_context(sample)
        rows.append(
            {
                "tile_id": sample.tile_id,
                "land_use": sample.land_use,
                "acres": sample.acres,
                "slope_degrees": sample.slope_degrees,
                "relative_elevation_m": sample.relative_elevation_m,
                "low_point_signal": _round_score(_clamp(sample.low_point_signal)),
                "flow_accumulation_proxy": (
                    None
                    if sample.flow_accumulation_proxy is None
                    else _round_score(_clamp(sample.flow_accumulation_proxy))
                ),
                "slope_class": context.slope_class,
                "relative_elevation_class": context.relative_elevation_class,
                "terrain_context": context.terrain_context,
                "retention_context_score": context.retention_context_score,
                "runoff_context_score": context.runoff_context_score,
                "convergence_context_score": context.convergence_context_score,
                "flow_proxy_used": context.flow_proxy_used,
                "source": sample.source,
                "product": sample.product,
                "doi": sample.doi,
                "date_start": sample.date_start,
                "date_end": sample.date_end,
                "geometry_label": sample.geometry_label,
                "hybrid_role": "static_terrain_context",
                "augmentation_note": (
                    "Synthetic NASADEM/SRTM-style derivative fixture; contextual support only, "
                    "not a hydrology model."
                ),
            }
        )
    return rows


def load_terrain_samples(path: Path) -> tuple[TerrainSample, ...]:
    """Load terrain-derivative input rows from a CSV fixture."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        return tuple(_terrain_sample_from_mapping(row) for row in csv.DictReader(handle))


def format_terrain_context_csv(rows: Iterable[Mapping[str, object]]) -> str:
    """Render terrain-context rows as deterministic CSV text."""

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=TERRAIN_CONTEXT_FIELDNAMES,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({field: _format_csv_value(row.get(field)) for field in TERRAIN_CONTEXT_FIELDNAMES})
    return output.getvalue()


def write_terrain_context_fixture(
    output_path: Path,
    samples: Iterable[TerrainSample] | None = None,
) -> list[dict[str, object]]:
    """Write a small terrain-context fixture and return the rows written."""

    rows = build_terrain_context_rows(tuple(samples) if samples is not None else sample_terrain_samples())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_terrain_context_csv(rows), encoding="utf-8")
    return rows


def sample_terrain_samples() -> tuple[TerrainSample, ...]:
    """Return a small synthetic terrain fixture aligned to current demo tile IDs."""

    return (
        TerrainSample(
            tile_id="cv-covercrop-013",
            land_use="cover-cropped almond block",
            acres=38.0,
            slope_degrees=1.4,
            relative_elevation_m=-2.1,
            low_point_signal=0.78,
            flow_accumulation_proxy=0.62,
        ),
        TerrainSample(
            tile_id="cv-vineyard-032",
            land_use="deficit-irrigated vineyard",
            acres=44.0,
            slope_degrees=13.0,
            relative_elevation_m=7.0,
            low_point_signal=0.30,
            flow_accumulation_proxy=0.15,
        ),
        TerrainSample(
            tile_id="cv-riparian-016",
            land_use="riparian buffer",
            acres=17.0,
            slope_degrees=0.7,
            relative_elevation_m=-3.8,
            low_point_signal=0.92,
            flow_accumulation_proxy=0.88,
        ),
        TerrainSample(
            tile_id="cv-rangeland-008",
            land_use="restoration rangeland",
            acres=120.0,
            slope_degrees=5.5,
            relative_elevation_m=1.0,
            low_point_signal=0.35,
            flow_accumulation_proxy=None,
        ),
        TerrainSample(
            tile_id="cv-orchard-044",
            land_use="young orchard windbreak",
            acres=24.0,
            slope_degrees=3.2,
            relative_elevation_m=-0.5,
            low_point_signal=0.55,
            flow_accumulation_proxy=None,
        ),
    )


def _terrain_sample_from_mapping(row: Mapping[str, str]) -> TerrainSample:
    return TerrainSample(
        tile_id=str(row["tile_id"]),
        land_use=str(row["land_use"]),
        acres=float(row["acres"]),
        slope_degrees=float(row["slope_degrees"]),
        relative_elevation_m=float(row["relative_elevation_m"]),
        low_point_signal=float(row["low_point_signal"]),
        flow_accumulation_proxy=_optional_float(row.get("flow_accumulation_proxy")),
        source=str(row.get("source") or "synthetic_terrain_context"),
        product=str(row.get("product") or "NASADEM/SRTM-style elevation derivatives"),
        doi=str(row.get("doi") or ""),
        date_start=str(row.get("date_start") or ""),
        date_end=str(row.get("date_end") or ""),
        geometry_label=str(row.get("geometry_label") or "central-valley-synthetic-terrain-context"),
    )


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _round_score(value: float) -> float:
    return round(_clamp(value), 4)


def _format_csv_value(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return value
