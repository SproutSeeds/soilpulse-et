#!/usr/bin/env python3
"""Build the synthetic HLS vegetation support fixture."""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path
from typing import Iterable

from nasa_space_to_soil_challenge.hls_vegetation import (
    HLS_VEGETATION_FIELDS,
    derive_hls_vegetation_rows,
    sample_hls_vegetation_inputs,
)

DEFAULT_OUTPUT = Path("tests/fixtures/hls_vegetation_sample.csv")


def build_fixture_rows() -> list[dict[str, object]]:
    """Return the deterministic synthetic HLS fixture rows."""

    return list(derive_hls_vegetation_rows(sample_hls_vegetation_inputs()))


def render_csv(rows: Iterable[dict[str, object]]) -> str:
    """Render rows as CSV with the stable fixture field order."""

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=HLS_VEGETATION_FIELDS,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def write_hls_vegetation_fixture(rows: Iterable[dict[str, object]], output_path: Path) -> None:
    """Write the HLS vegetation fixture CSV."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_csv(rows), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--stdout", action="store_true", help="Print the CSV fixture to stdout.")
    parser.add_argument("--no-write", action="store_true", help="Do not write the output file.")
    args = parser.parse_args()

    rows = build_fixture_rows()
    if not args.no_write:
        write_hls_vegetation_fixture(rows, args.output)

    if args.stdout or args.no_write:
        sys.stdout.write(render_csv(rows))
    else:
        print(f"hls_vegetation_rows={len(rows)}")
        print(args.output)


if __name__ == "__main__":
    main()
