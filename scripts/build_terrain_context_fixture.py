#!/usr/bin/env python3
"""Build or print the synthetic static terrain-context fixture."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from nasa_space_to_soil_challenge.terrain_context import (
    build_terrain_context_rows,
    format_terrain_context_csv,
    sample_terrain_samples,
    write_terrain_context_fixture,
)

DEFAULT_OUTPUT = Path("tests/fixtures/terrain_context_sample.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the CSV fixture to stdout instead of writing the output path.",
    )
    args = parser.parse_args()

    samples = sample_terrain_samples()
    if args.stdout:
        sys.stdout.write(format_terrain_context_csv(build_terrain_context_rows(samples)))
        return

    rows = write_terrain_context_fixture(args.output, samples)
    print(f"terrain_context_rows={len(rows)}")
    print(args.output)


if __name__ == "__main__":
    main()
