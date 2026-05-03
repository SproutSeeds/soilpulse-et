"""Fixture-first HLS vegetation-index support for SoilPulse-ET.

This module does not contact Earthdata, fetch HLS assets, or validate real
stress events. It provides deterministic helpers for Phase 1/Phase 2 support
artifacts: compute simple vegetation-index before/after deltas and map them
into the existing triage CSV vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

VegetationContext = Literal[
    "strengthens_et_signal",
    "weakens_et_signal",
    "mixed_or_limited_context",
]

HLS_VEGETATION_SOURCE = "hls_vegetation_synthetic_fixture"
HLS_VEGETATION_PRODUCT = "HLS vegetation-index support lane"
HLS_VEGETATION_DOI = ""
HLS_VALIDATION_STATUS = "synthetic_fixture_not_validated_stress_event"

TRIAGE_COMPATIBLE_FIELDS = (
    "tile_id",
    "land_use",
    "acres",
    "source",
    "product",
    "doi",
    "date_start",
    "date_end",
    "geometry_label",
    "sample_count",
    "valid_observation_count",
    "latest_observation_date",
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

HLS_EXTRA_FIELDS = (
    "hls_clear_fraction",
    "ndvi_before",
    "ndvi_after",
    "ndvi_delta",
    "ndmi_before",
    "ndmi_after",
    "ndmi_delta",
    "ndwi_before",
    "ndwi_after",
    "ndwi_delta",
    "vegetation_context",
    "vegetation_context_reason",
    "claim_label",
    "validation_status",
)

HLS_VEGETATION_FIELDS = TRIAGE_COMPATIBLE_FIELDS + HLS_EXTRA_FIELDS


@dataclass(frozen=True)
class ReflectanceSnapshot:
    """Surface-reflectance values for one before or after observation."""

    red: float
    nir: float
    swir1: float


@dataclass(frozen=True)
class VegetationIndexDeltas:
    """Before/after vegetation indices and after-minus-before deltas."""

    ndvi_before: float
    ndvi_after: float
    ndvi_delta: float
    ndmi_before: float
    ndmi_after: float
    ndmi_delta: float
    ndwi_before: float
    ndwi_after: float
    ndwi_delta: float


@dataclass(frozen=True)
class VegetationContextResult:
    """Heuristic context label for an ECOSTRESS ET stress signal."""

    context: VegetationContext
    reason: str


@dataclass(frozen=True)
class VegetationContextThresholds:
    """Conservative thresholds for fixture-level context labels."""

    et_stress_mm_day: float = -1.0
    ndvi_decline: float = -0.04
    ndmi_decline: float = -0.04
    stable_delta: float = -0.01
    min_confidence: float = 0.55
    max_cloud_fraction: float = 0.65


@dataclass(frozen=True)
class HlsVegetationSample:
    """One synthetic/sample tile pair used to build HLS support rows."""

    tile_id: str
    land_use: str
    acres: float
    date_start: str
    date_end: str
    geometry_label: str
    before: ReflectanceSnapshot
    after: ReflectanceSnapshot
    et_anomaly_mm_day: float
    cloud_fraction: float
    days_since_seen: int
    user_priority: float
    hls_clear_fraction: float
    full_chip_kib: float = 96.0
    summary_kib: float = 8.0
    processing_ms: int = 180
    energy_j: float = 4.0


def normalized_difference(positive: float, negative: float) -> float:
    """Compute a normalized difference index from two non-negative bands."""

    if positive < 0 or negative < 0:
        raise ValueError("reflectance inputs must be non-negative for this fixture helper")
    denominator = positive + negative
    if denominator == 0:
        raise ValueError("normalized difference denominator is zero")
    return round((positive - negative) / denominator, 4)


def ndvi(snapshot: ReflectanceSnapshot) -> float:
    """Compute NDVI as (NIR - red) / (NIR + red)."""

    return normalized_difference(snapshot.nir, snapshot.red)


def ndmi(snapshot: ReflectanceSnapshot) -> float:
    """Compute NDMI as (NIR - SWIR1) / (NIR + SWIR1)."""

    return normalized_difference(snapshot.nir, snapshot.swir1)


def ndwi(snapshot: ReflectanceSnapshot) -> float:
    """Compute vegetation NDWI using the same NIR/SWIR1 convention as NDMI."""

    return ndmi(snapshot)


def vegetation_index_deltas(
    before: ReflectanceSnapshot,
    after: ReflectanceSnapshot,
) -> VegetationIndexDeltas:
    """Compute NDVI and NDMI/NDWI before/after deltas."""

    ndvi_before = ndvi(before)
    ndvi_after = ndvi(after)
    ndmi_before = ndmi(before)
    ndmi_after = ndmi(after)
    ndwi_before = ndwi(before)
    ndwi_after = ndwi(after)
    return VegetationIndexDeltas(
        ndvi_before=ndvi_before,
        ndvi_after=ndvi_after,
        ndvi_delta=round(ndvi_after - ndvi_before, 4),
        ndmi_before=ndmi_before,
        ndmi_after=ndmi_after,
        ndmi_delta=round(ndmi_after - ndmi_before, 4),
        ndwi_before=ndwi_before,
        ndwi_after=ndwi_after,
        ndwi_delta=round(ndwi_after - ndwi_before, 4),
    )


def vegetation_context_confidence(hls_clear_fraction: float, cloud_fraction: float) -> float:
    """Map HLS clear fraction and scene cloud fraction into triage confidence."""

    return round(_clamp(0.70 * hls_clear_fraction + 0.30 * (1.0 - cloud_fraction)), 4)


def classify_vegetation_context(
    *,
    et_anomaly_mm_day: float,
    ndvi_delta: float,
    ndmi_delta: float,
    confidence: float,
    cloud_fraction: float,
    thresholds: VegetationContextThresholds = VegetationContextThresholds(),
) -> VegetationContextResult:
    """Classify whether vegetation context supports an ECOSTRESS ET deficit.

    The result is a heuristic context label only. It should not be interpreted
    as a validated crop-stress event detector.
    """

    if cloud_fraction > thresholds.max_cloud_fraction or confidence < thresholds.min_confidence:
        return VegetationContextResult(
            context="mixed_or_limited_context",
            reason="limited_clear_view_or_confidence",
        )

    et_deficit = et_anomaly_mm_day <= thresholds.et_stress_mm_day
    vegetation_decline = (
        ndvi_delta <= thresholds.ndvi_decline
        or ndmi_delta <= thresholds.ndmi_decline
    )
    vegetation_stable_or_better = (
        ndvi_delta >= thresholds.stable_delta
        and ndmi_delta >= thresholds.stable_delta
    )

    if et_deficit and vegetation_decline:
        return VegetationContextResult(
            context="strengthens_et_signal",
            reason="et_deficit_with_vegetation_decline",
        )
    if et_deficit and vegetation_stable_or_better:
        return VegetationContextResult(
            context="weakens_et_signal",
            reason="et_deficit_without_matching_vegetation_decline",
        )
    if not et_deficit and not vegetation_decline:
        return VegetationContextResult(
            context="weakens_et_signal",
            reason="no_et_deficit_and_no_vegetation_decline",
        )
    return VegetationContextResult(
        context="mixed_or_limited_context",
        reason="vegetation_and_et_signals_do_not_cleanly_align",
    )


def derive_hls_vegetation_rows(
    samples: Iterable[HlsVegetationSample],
) -> tuple[dict[str, object], ...]:
    """Convert HLS vegetation samples into triage-compatible metadata rows."""

    return tuple(_row_from_sample(sample) for sample in samples)


def sample_hls_vegetation_inputs() -> tuple[HlsVegetationSample, ...]:
    """Return a small labeled synthetic/sample fixture input set."""

    return (
        HlsVegetationSample(
            tile_id="cv-covercrop-013",
            land_use="cover-cropped almond block",
            acres=38.0,
            date_start="2024-07-15",
            date_end="2024-08-15",
            geometry_label="synthetic-hls-central-valley-support-lane",
            before=ReflectanceSnapshot(red=0.18, nir=0.54, swir1=0.27),
            after=ReflectanceSnapshot(red=0.21, nir=0.43, swir1=0.35),
            et_anomaly_mm_day=-2.8,
            cloud_fraction=0.10,
            days_since_seen=6,
            user_priority=0.95,
            hls_clear_fraction=0.90,
        ),
        HlsVegetationSample(
            tile_id="cv-vineyard-032",
            land_use="deficit-irrigated vineyard",
            acres=44.0,
            date_start="2024-07-15",
            date_end="2024-08-15",
            geometry_label="synthetic-hls-central-valley-support-lane",
            before=ReflectanceSnapshot(red=0.20, nir=0.46, swir1=0.30),
            after=ReflectanceSnapshot(red=0.19, nir=0.47, swir1=0.30),
            et_anomaly_mm_day=-2.6,
            cloud_fraction=0.12,
            days_since_seen=5,
            user_priority=0.82,
            hls_clear_fraction=0.88,
            full_chip_kib=112.0,
        ),
        HlsVegetationSample(
            tile_id="cv-riparian-016",
            land_use="riparian buffer",
            acres=17.0,
            date_start="2024-07-15",
            date_end="2024-08-15",
            geometry_label="synthetic-hls-central-valley-support-lane",
            before=ReflectanceSnapshot(red=0.16, nir=0.50, swir1=0.25),
            after=ReflectanceSnapshot(red=0.18, nir=0.45, swir1=0.28),
            et_anomaly_mm_day=-2.1,
            cloud_fraction=0.72,
            days_since_seen=8,
            user_priority=0.90,
            hls_clear_fraction=0.55,
        ),
        HlsVegetationSample(
            tile_id="cv-fallow-003",
            land_use="managed fallow soil-cover trial",
            acres=80.0,
            date_start="2024-07-15",
            date_end="2024-08-15",
            geometry_label="synthetic-hls-central-valley-support-lane",
            before=ReflectanceSnapshot(red=0.24, nir=0.34, swir1=0.31),
            after=ReflectanceSnapshot(red=0.23, nir=0.35, swir1=0.30),
            et_anomaly_mm_day=0.3,
            cloud_fraction=0.05,
            days_since_seen=3,
            user_priority=0.25,
            hls_clear_fraction=0.92,
        ),
    )


def _row_from_sample(sample: HlsVegetationSample) -> dict[str, object]:
    deltas = vegetation_index_deltas(sample.before, sample.after)
    confidence = vegetation_context_confidence(sample.hls_clear_fraction, sample.cloud_fraction)
    context = classify_vegetation_context(
        et_anomaly_mm_day=sample.et_anomaly_mm_day,
        ndvi_delta=deltas.ndvi_delta,
        ndmi_delta=deltas.ndmi_delta,
        confidence=confidence,
        cloud_fraction=sample.cloud_fraction,
    )
    valid_observations = round(2 * sample.hls_clear_fraction)
    return {
        "tile_id": sample.tile_id,
        "land_use": sample.land_use,
        "acres": sample.acres,
        "source": HLS_VEGETATION_SOURCE,
        "product": HLS_VEGETATION_PRODUCT,
        "doi": HLS_VEGETATION_DOI,
        "date_start": sample.date_start,
        "date_end": sample.date_end,
        "geometry_label": sample.geometry_label,
        "sample_count": 2,
        "valid_observation_count": valid_observations,
        "latest_observation_date": sample.date_end,
        "et_anomaly_mm_day": sample.et_anomaly_mm_day,
        "vegetation_index_delta": deltas.ndvi_delta,
        "cloud_fraction": sample.cloud_fraction,
        "days_since_seen": sample.days_since_seen,
        "user_priority": sample.user_priority,
        "confidence": confidence,
        "full_chip_kib": sample.full_chip_kib,
        "summary_kib": sample.summary_kib,
        "processing_ms": sample.processing_ms,
        "energy_j": sample.energy_j,
        "hls_clear_fraction": sample.hls_clear_fraction,
        "ndvi_before": deltas.ndvi_before,
        "ndvi_after": deltas.ndvi_after,
        "ndvi_delta": deltas.ndvi_delta,
        "ndmi_before": deltas.ndmi_before,
        "ndmi_after": deltas.ndmi_after,
        "ndmi_delta": deltas.ndmi_delta,
        "ndwi_before": deltas.ndwi_before,
        "ndwi_after": deltas.ndwi_after,
        "ndwi_delta": deltas.ndwi_delta,
        "vegetation_context": context.context,
        "vegetation_context_reason": context.reason,
        "claim_label": "Heuristic",
        "validation_status": HLS_VALIDATION_STATUS,
    }


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))
