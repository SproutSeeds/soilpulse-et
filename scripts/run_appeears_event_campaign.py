#!/usr/bin/env python3
"""Run a small multi-window AppEEARS ECOSTRESS event-hunt campaign."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from nasa_space_to_soil_challenge.appeears import (
    APPEEARS_API_BASE,
    DEFAULT_TILE_POINT_SAMPLES,
    AppEearsClient,
    AppEearsError,
    CredentialError,
    build_ecostress_tile_point_task,
    bundle_files,
    credential_help,
    derive_from_download_dir,
    load_earthdata_credentials,
    write_json,
)

DEFAULT_DATA_ROOT = Path("data/appeears")
DEFAULT_OUTPUT_DIR = Path("tests/fixtures")
DEFAULT_WINDOWS = (
    "2024-05-01..2024-06-30",
    "2024-06-01..2024-07-31",
    "2024-08-01..2024-09-30",
    "2023-07-01..2023-08-31",
    "2022-07-01..2022-08-31",
)
GEOMETRY_LABEL = "central-valley-public-microtile-sample"


@dataclass(frozen=True)
class CampaignWindow:
    """One AppEEARS date window and output fixture path."""

    start_date: str
    end_date: str
    output_path: Path


def parse_window(value: str, output_dir: Path) -> CampaignWindow:
    """Parse YYYY-MM-DD..YYYY-MM-DD into a campaign window."""

    if ".." not in value:
        raise ValueError(f"window must use START..END format: {value}")
    start, end = (part.strip() for part in value.split("..", 1))
    datetime.strptime(start, "%Y-%m-%d")
    datetime.strptime(end, "%Y-%m-%d")
    suffix = f"{start[:4]}_{start[5:7]}_{end[:4]}_{end[5:7]}"
    return CampaignWindow(
        start_date=start,
        end_date=end,
        output_path=output_dir / f"ecostress_derived_{suffix}.csv",
    )


def run_campaign(
    windows: list[CampaignWindow],
    *,
    base_url: str = APPEEARS_API_BASE,
    data_root: Path = DEFAULT_DATA_ROOT,
    timeout_seconds: int = 900,
    interval_seconds: int = 20,
    force: bool = False,
) -> list[dict[str, object]]:
    """Submit, poll, download, and derive all requested windows."""

    credentials = load_earthdata_credentials()
    client = AppEearsClient.login(credentials, base_url=base_url)
    summary: list[dict[str, object]] = []

    for window in windows:
        if window.output_path.exists() and not force:
            summary.append(
                {
                    "window": f"{window.start_date}..{window.end_date}",
                    "status": "skipped_existing",
                    "output": window.output_path.as_posix(),
                }
            )
            continue

        task_name = _task_name(window)
        task = build_ecostress_tile_point_task(
            task_name=task_name,
            start_date=window.start_date,
            end_date=window.end_date,
            points=DEFAULT_TILE_POINT_SAMPLES,
        )
        write_json(data_root / task_name / "request.json", task)
        response = client.submit_task(task)
        task_id = str(response["task_id"])
        run_dir = data_root / task_id
        write_json(run_dir / "request.json", task)
        write_json(run_dir / "submit-response.json", response)
        write_json(
            data_root / "latest-campaign-task.json",
            {"task_id": task_id, "task_name": task_name, "window": f"{window.start_date}..{window.end_date}"},
        )

        print(f"window={window.start_date}..{window.end_date}")
        print(f"task_id={task_id}")
        print(f"status={response.get('status', '')}")
        task_status = client.wait_for_task(
            task_id,
            timeout_seconds=timeout_seconds,
            interval_seconds=interval_seconds,
        )
        print(f"status={task_status.get('status', '')}")

        bundle = client.bundle(task_id)
        write_json(run_dir / "bundle.json", bundle)
        downloaded = []
        for file in bundle_files(bundle):
            downloaded.append(client.download_file(task_id, file, run_dir))
        rows = derive_from_download_dir(
            run_dir,
            output_path=window.output_path,
            date_start=window.start_date,
            date_end=window.end_date,
            geometry_label=GEOMETRY_LABEL,
        )
        print(f"downloaded_files={len(downloaded)}")
        print(f"derived_rows={len(rows)}")
        print(window.output_path)

        summary.append(
            {
                "window": f"{window.start_date}..{window.end_date}",
                "status": "done",
                "task_id": task_id,
                "downloaded_files": len(downloaded),
                "derived_rows": len(rows),
                "output": window.output_path.as_posix(),
            }
        )

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=APPEEARS_API_BASE)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--window", action="append", dest="windows", help="Date window as YYYY-MM-DD..YYYY-MM-DD.")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--interval-seconds", type=int, default=20)
    parser.add_argument("--force", action="store_true", help="Re-run windows even when output CSV exists.")
    args = parser.parse_args()

    raw_windows = args.windows or list(DEFAULT_WINDOWS)
    windows = [parse_window(value, args.output_dir) for value in raw_windows]
    summary = run_campaign(
        windows,
        base_url=args.base_url,
        data_root=args.data_root,
        timeout_seconds=args.timeout_seconds,
        interval_seconds=args.interval_seconds,
        force=args.force,
    )
    print("campaign_summary")
    for row in summary:
        print(row)


def _task_name(window: CampaignWindow) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    start = window.start_date.replace("-", "")
    end = window.end_date.replace("-", "")
    return f"soilpulse-ecostress-{start}-{end}-{stamp}"


if __name__ == "__main__":
    try:
        main()
    except CredentialError as exc:
        raise SystemExit(f"{exc}\n\n{credential_help()}") from exc
    except AppEearsError as exc:
        raise SystemExit(str(exc)) from exc
