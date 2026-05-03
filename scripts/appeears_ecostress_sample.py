#!/usr/bin/env python3
"""Submit and process the tiny ECOSTRESS AppEEARS sample."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from nasa_space_to_soil_challenge.appeears import (
    APPEEARS_API_BASE,
    DEFAULT_POINT_SAMPLES,
    DEFAULT_TILE_POINT_SAMPLES,
    ECOSTRESS_DOI,
    ECOSTRESS_LAYERS,
    ECOSTRESS_PRODUCT,
    AppEearsClient,
    AppEearsError,
    CredentialError,
    build_ecostress_point_task,
    build_ecostress_tile_point_task,
    bundle_files,
    credential_help,
    derive_from_download_dir,
    discover_product,
    load_earthdata_credentials,
    write_json,
)

DEFAULT_DATA_ROOT = Path("data/appeears")
DEFAULT_OUTPUT = Path("tests/fixtures/ecostress_derived_sample.csv")
DEFAULT_START_DATE = "2024-07-01"
DEFAULT_END_DATE = "2024-08-31"
DEFAULT_GEOMETRY_LABEL = "central-valley-public-microtile-sample"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=APPEEARS_API_BASE)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("discover", help="Print ECOSTRESS product/layer metadata.")
    subparsers.add_parser("login-check", help="Check Earthdata/AppEEARS login without submitting a task.")

    submit = subparsers.add_parser("submit", help="Submit a point sample request.")
    _add_request_args(submit)

    status = subparsers.add_parser("status", help="Check AppEEARS task status.")
    status.add_argument("task_id")

    download = subparsers.add_parser("download", help="Download a completed task bundle.")
    download.add_argument("task_id")

    derive = subparsers.add_parser("derive", help="Derive the repo fixture from downloaded CSV files.")
    derive.add_argument("task_id")
    derive.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    _add_derivation_args(derive)

    run = subparsers.add_parser("run", help="Submit, optionally poll, download, and derive.")
    _add_request_args(run)
    _add_derivation_args(run)
    run.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    run.add_argument("--poll", action="store_true", help="Poll until the task completes.")
    run.add_argument("--timeout-seconds", type=int, default=900)
    run.add_argument("--interval-seconds", type=int, default=20)

    args = parser.parse_args()

    if args.command == "discover":
        _discover()
        return

    if args.command in {"login-check", "submit", "run", "status", "download"}:
        client = _authenticated_client(args.base_url)
    else:
        client = None

    if args.command == "login-check":
        assert client is not None
        print("login=ok")
        print(f"api={args.base_url}")
    elif args.command == "submit":
        response = _submit(args, client)
        print(f"task_id={response.get('task_id', '')}")
        print(f"status={response.get('status', '')}")
    elif args.command == "status":
        task_status = client.status(args.task_id)
        print(f"task_id={task_status.get('task_id', args.task_id)}")
        print(f"status={task_status.get('status', '')}")
        progress = task_status.get("progress", {})
        if isinstance(progress, dict) and progress.get("summary") is not None:
            print(f"progress_pct={progress['summary']}")
    elif args.command == "download":
        paths = _download(args.task_id, args.data_root, client)
        print(f"downloaded_files={len(paths)}")
        for path in paths:
            print(path)
    elif args.command == "derive":
        rows = _derive(args.task_id, args.data_root, args.output, args)
        print(f"derived_rows={len(rows)}")
        print(args.output)
    elif args.command == "run":
        response = _submit(args, client)
        task_id = str(response["task_id"])
        print(f"task_id={task_id}")
        print(f"status={response.get('status', '')}")
        if not args.poll:
            print("poll=false")
            print(f"next=PYTHONPATH=src .venv/bin/python {Path(__file__).as_posix()} status {task_id}")
            return
        try:
            task_status = client.wait_for_task(
                task_id,
                timeout_seconds=args.timeout_seconds,
                interval_seconds=args.interval_seconds,
            )
        except TimeoutError:
            print(f"status=pending_or_processing")
            print(f"next=PYTHONPATH=src .venv/bin/python {Path(__file__).as_posix()} status {task_id}")
            raise
        print(f"status={task_status.get('status', '')}")
        paths = _download(task_id, args.data_root, client)
        print(f"downloaded_files={len(paths)}")
        rows = _derive(task_id, args.data_root, args.output, args)
        print(f"derived_rows={len(rows)}")
        print(args.output)


def _add_request_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--task-name", default=None)
    parser.add_argument(
        "--sample-mode",
        choices=("tile-points", "legacy-points"),
        default="tile-points",
        help="Use grouped public points per tile, or the older one-point-per-site sample.",
    )


def _add_derivation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--date-start", default=DEFAULT_START_DATE)
    parser.add_argument("--date-end", default=DEFAULT_END_DATE)
    parser.add_argument("--geometry-label", default=DEFAULT_GEOMETRY_LABEL)


def _discover() -> None:
    product = discover_product()
    print(f"product={ECOSTRESS_PRODUCT}")
    print(f"doi={ECOSTRESS_DOI}")
    for layer in ECOSTRESS_LAYERS:
        metadata = product.get(layer, {})
        print(f"layer={layer} units={metadata.get('Units', '')} description={metadata.get('Description', '')}")


def _authenticated_client(base_url: str) -> AppEearsClient:
    credentials = load_earthdata_credentials()
    return AppEearsClient.login(credentials, base_url=base_url)


def _submit(args: argparse.Namespace, client: AppEearsClient) -> dict[str, object]:
    task_name = args.task_name or _default_task_name()
    if args.sample_mode == "legacy-points":
        task = build_ecostress_point_task(
            task_name=task_name,
            start_date=args.start_date,
            end_date=args.end_date,
            points=DEFAULT_POINT_SAMPLES,
        )
    else:
        task = build_ecostress_tile_point_task(
            task_name=task_name,
            start_date=args.start_date,
            end_date=args.end_date,
            points=DEFAULT_TILE_POINT_SAMPLES,
        )
    task_dir = args.data_root / task_name
    write_json(task_dir / "request.json", task)
    response = client.submit_task(task)
    task_id = str(response["task_id"])
    run_dir = args.data_root / task_id
    write_json(run_dir / "request.json", task)
    write_json(run_dir / "submit-response.json", response)
    write_json(args.data_root / "latest-task.json", {"task_id": task_id, "task_name": task_name})
    return response


def _download(task_id: str, data_root: Path, client: AppEearsClient) -> list[Path]:
    download_dir = data_root / task_id
    bundle = client.bundle(task_id)
    write_json(download_dir / "bundle.json", bundle)
    paths = []
    for file in bundle_files(bundle):
        paths.append(client.download_file(task_id, file, download_dir))
    return paths


def _derive(
    task_id: str,
    data_root: Path,
    output_path: Path,
    args: argparse.Namespace,
) -> list[dict[str, object]]:
    return derive_from_download_dir(
        data_root / task_id,
        output_path=output_path,
        date_start=args.date_start,
        date_end=args.date_end,
        geometry_label=args.geometry_label,
    )


def _default_task_name() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"soilpulse-ecostress-{stamp}"


if __name__ == "__main__":
    try:
        main()
    except CredentialError as exc:
        raise SystemExit(f"{exc}\n\n{credential_help()}") from exc
    except AppEearsError as exc:
        raise SystemExit(str(exc)) from exc
