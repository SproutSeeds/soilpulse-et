#!/usr/bin/env python3
"""Print a local data manifest for the NASA Space to Soil workspace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from nasa_space_to_soil_challenge.data_manifest import build_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Data directory to scan. Defaults to this repo's data/ directory.",
    )
    parser.add_argument(
        "--hash",
        action="store_true",
        help="Compute SHA-256 hashes for files up to --max-hash-bytes.",
    )
    parser.add_argument(
        "--max-hash-bytes",
        type=int,
        default=100_000_000,
        help="Maximum file size to hash when --hash is set.",
    )
    args = parser.parse_args()

    kwargs = {
        "include_hash": args.hash,
        "max_hash_bytes": args.max_hash_bytes,
    }
    if args.data_dir is not None:
        kwargs["data_dir"] = args.data_dir

    print(json.dumps(build_manifest(**kwargs), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
