from dataclasses import dataclass


@dataclass(frozen=True)
class ContestProfile:
    slug: str
    title: str
    status: str
    theme: str
    primary_metric: str
    first_focus: tuple[str, ...]


PROFILE = ContestProfile(
    slug="nasa-space-to-soil-challenge",
    title="NASA Space to Soil Challenge",
    status="active",
    theme="adaptive sensing and onboard processing for SmallSat land resilience",
    primary_metric="official Phase 1 judging criteria",
    first_focus=(
        "submission contract",
        "NASA dataset or algorithm selection",
        "SmallSat resource-budgeted demo",
    ),
)
