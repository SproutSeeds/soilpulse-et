"""AppEEARS helpers for the ECOSTRESS-derived sample workflow."""

from __future__ import annotations

import base64
import csv
import json
import math
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

APPEEARS_API_BASE = "https://appeears.earthdatacloud.nasa.gov/api"
ECOSTRESS_PRODUCT = "ECO_L3T_JET.002"
ECOSTRESS_DOI = "10.5067/ECOSTRESS/ECO_L3T_JET.002"
ECOSTRESS_LAYERS = ("ETdaily", "ETinstUncertainty", "cloud", "water")
EARTHDATA_KEYCHAIN_ALIAS = "earthdata-login"
EARTHDATA_KEYCHAIN_SERVICE = "soilpulse-et.earthdata"

DEFAULT_POINT_SAMPLES = (
    {"id": "cv-west-01", "category": "irrigated_agriculture", "latitude": 36.66, "longitude": -121.70},
    {"id": "cv-mid-02", "category": "irrigated_agriculture", "latitude": 36.74, "longitude": -121.61},
    {"id": "cv-east-03", "category": "regenerative_trial", "latitude": 36.82, "longitude": -121.52},
    {"id": "cv-north-04", "category": "riparian_buffer", "latitude": 36.88, "longitude": -121.47},
)
DEFAULT_TILE_POINT_SAMPLES = (
    {
        "id": "cv-covercrop-013__p01",
        "category": "cover-cropped almond block",
        "latitude": 36.660,
        "longitude": -121.704,
    },
    {
        "id": "cv-covercrop-013__p02",
        "category": "cover-cropped almond block",
        "latitude": 36.663,
        "longitude": -121.700,
    },
    {
        "id": "cv-covercrop-013__p03",
        "category": "cover-cropped almond block",
        "latitude": 36.657,
        "longitude": -121.697,
    },
    {
        "id": "cv-vineyard-032__p01",
        "category": "deficit-irrigated vineyard",
        "latitude": 36.738,
        "longitude": -121.614,
    },
    {
        "id": "cv-vineyard-032__p02",
        "category": "deficit-irrigated vineyard",
        "latitude": 36.742,
        "longitude": -121.610,
    },
    {
        "id": "cv-vineyard-032__p03",
        "category": "deficit-irrigated vineyard",
        "latitude": 36.745,
        "longitude": -121.606,
    },
    {
        "id": "cv-riparian-016__p01",
        "category": "riparian buffer",
        "latitude": 36.875,
        "longitude": -121.474,
    },
    {
        "id": "cv-riparian-016__p02",
        "category": "riparian buffer",
        "latitude": 36.879,
        "longitude": -121.470,
    },
    {
        "id": "cv-riparian-016__p03",
        "category": "riparian buffer",
        "latitude": 36.883,
        "longitude": -121.466,
    },
    {
        "id": "cv-fallow-003__p01",
        "category": "managed fallow soil-cover trial",
        "latitude": 36.815,
        "longitude": -121.524,
    },
    {
        "id": "cv-fallow-003__p02",
        "category": "managed fallow soil-cover trial",
        "latitude": 36.820,
        "longitude": -121.520,
    },
    {
        "id": "cv-fallow-003__p03",
        "category": "managed fallow soil-cover trial",
        "latitude": 36.825,
        "longitude": -121.516,
    },
)


@dataclass(frozen=True)
class EarthdataCredentials:
    """Earthdata username/password pair."""

    username: str
    password: str


@dataclass(frozen=True)
class AppEearsFile:
    """One downloadable file listed in an AppEEARS bundle."""

    file_id: str
    file_name: str
    file_type: str
    file_size: int
    sha256: str | None = None


class AppEearsError(RuntimeError):
    """Raised when AppEEARS returns an error response."""


class CredentialError(RuntimeError):
    """Raised when Earthdata credentials cannot be loaded or parsed."""


class AppEearsClient:
    """Small standard-library client for the AppEEARS API."""

    def __init__(self, token: str, *, base_url: str = APPEEARS_API_BASE) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/")

    @classmethod
    def login(
        cls,
        credentials: EarthdataCredentials,
        *,
        base_url: str = APPEEARS_API_BASE,
    ) -> "AppEearsClient":
        auth = base64.b64encode(f"{credentials.username}:{credentials.password}".encode("utf-8")).decode("ascii")
        status, _, payload = _request_json(
            f"{base_url.rstrip('/')}/login",
            method="POST",
            headers={"Authorization": f"Basic {auth}", "Content-Length": "0"},
        )
        if status >= 400:
            if status in {401, 403}:
                raise CredentialError(
                    "NASA AppEEARS rejected the Earthdata credentials. Check the username/password, "
                    "then sign in once at https://urs.earthdata.nasa.gov/ and "
                    "https://appeears.earthdatacloud.nasa.gov/ to confirm the account and terms."
                )
            raise AppEearsError(_message_from_payload(payload, f"login failed with HTTP {status}"))
        token = str(payload.get("token", ""))
        if not token:
            raise AppEearsError("login response did not include a bearer token")
        return cls(token, base_url=base_url)

    def submit_task(self, task: dict[str, Any]) -> dict[str, Any]:
        status, _, payload = _request_json(
            f"{self.base_url}/task",
            method="POST",
            headers=self._headers({"Content-Type": "application/json"}),
            data=json.dumps(task).encode("utf-8"),
        )
        if status not in {200, 201, 202}:
            raise AppEearsError(_message_from_payload(payload, f"task submit failed with HTTP {status}"))
        return payload

    def task(self, task_id: str) -> dict[str, Any]:
        status, _, payload = _request_json(
            f"{self.base_url}/task/{urllib.parse.quote(task_id)}",
            headers=self._headers({"Content-Type": "application/json"}),
        )
        if status >= 400:
            raise AppEearsError(_message_from_payload(payload, f"task retrieve failed with HTTP {status}"))
        if isinstance(payload, list):
            return payload[0] if payload else {}
        return payload

    def status(self, task_id: str) -> dict[str, Any]:
        status, _, payload = _request_json(
            f"{self.base_url}/status/{urllib.parse.quote(task_id)}",
            headers=self._headers(),
        )
        if status >= 400:
            raise AppEearsError(_message_from_payload(payload, f"status retrieve failed with HTTP {status}"))
        if isinstance(payload, list):
            return payload[0] if payload else {}
        return payload

    def wait_for_task(self, task_id: str, *, timeout_seconds: int = 900, interval_seconds: int = 20) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        last_status: dict[str, Any] = {}
        while time.monotonic() < deadline:
            last_status = self.status(task_id)
            status = str(last_status.get("status", "")).lower()
            if status == "done":
                return last_status
            if status == "error":
                raise AppEearsError(json.dumps(last_status, indent=2, sort_keys=True))
            time.sleep(interval_seconds)
        raise TimeoutError(f"AppEEARS task {task_id} did not finish within {timeout_seconds} seconds")

    def bundle(self, task_id: str) -> dict[str, Any]:
        status, _, payload = _request_json(
            f"{self.base_url}/bundle/{urllib.parse.quote(task_id)}",
            headers=self._headers(),
        )
        if status >= 400:
            raise AppEearsError(_message_from_payload(payload, f"bundle retrieve failed with HTTP {status}"))
        return payload

    def download_file(self, task_id: str, file: AppEearsFile, destination_dir: Path) -> Path:
        destination_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(file.file_name).name
        destination = destination_dir / safe_name
        request = urllib.request.Request(
            f"{self.base_url}/bundle/{urllib.parse.quote(task_id)}/{urllib.parse.quote(file.file_id)}",
            headers=self._headers(),
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                destination.write_bytes(response.read())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise AppEearsError(f"download failed for {safe_name}: HTTP {exc.code}: {body}") from exc
        return destination

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.token}"}
        if extra:
            headers.update(extra)
        return headers


def load_earthdata_credentials(
    *,
    keychain_alias: str = EARTHDATA_KEYCHAIN_ALIAS,
    keychain_service: str = EARTHDATA_KEYCHAIN_SERVICE,
) -> EarthdataCredentials:
    """Load Earthdata credentials from environment or a local macOS Keychain item."""

    username = os.environ.get("EARTHDATA_USERNAME")
    password = os.environ.get("EARTHDATA_PASSWORD")
    if username and password:
        return EarthdataCredentials(username=username, password=password)

    raw = os.environ.get("EARTHDATA_CREDENTIALS")
    if raw:
        try:
            return parse_earthdata_credentials(raw)
        except CredentialError as exc:
            raise CredentialError("EARTHDATA_CREDENTIALS is set but could not be parsed") from exc

    raw = _read_macos_keychain_secret(keychain_alias, keychain_service)
    if raw:
        try:
            return parse_earthdata_credentials(raw)
        except CredentialError as exc:
            raise CredentialError(
                f"macOS Keychain item account={keychain_alias!r} service={keychain_service!r} "
                "exists but could not be parsed as Earthdata credentials"
            ) from exc

    raise CredentialError(
        "Earthdata credentials were not found. Set EARTHDATA_USERNAME/EARTHDATA_PASSWORD, "
        "EARTHDATA_CREDENTIALS, or save a local keychain item for account earthdata-login."
    )


def parse_earthdata_credentials(raw: str) -> EarthdataCredentials:
    """Parse common clipboard formats without exposing the secret in logs."""

    text = raw.strip()
    if not text:
        raise CredentialError("credential value is empty")

    json_creds = _parse_json_credentials(text)
    if json_creds is not None:
        return json_creds

    encoded_creds = _parse_encoded_credentials(text)
    if encoded_creds is not None:
        return encoded_creds

    key_values = _parse_key_value_credentials(text)
    if key_values is not None:
        return key_values

    netrc_creds = _parse_netrc_credentials(text)
    if netrc_creds is not None:
        return netrc_creds

    if ":" in text and "\n" not in text:
        username, password = text.split(":", 1)
        return _validated_credentials(username, password)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) == 2:
        return _validated_credentials(lines[0], lines[1])

    raise CredentialError("could not parse Earthdata credentials")


def credential_help() -> str:
    """Return non-secret guidance for configuring Earthdata credentials."""

    return (
        "Provide Earthdata credentials with one of:\n"
        "  EARTHDATA_USERNAME=<username> EARTHDATA_PASSWORD=<password> make appeears-run\n"
        "  EARTHDATA_USERNAME=<username> EARTHDATA_PASSWORD=<password> make appeears-login-check\n"
        "  EARTHDATA_CREDENTIALS='<username>:<password>' make appeears-run\n"
        "  security add-generic-password -a earthdata-login -s soilpulse-et.earthdata -w '<username>:<password>' -U\n"
        "Do not commit credentials or paste them into tracked files."
    )


def build_ecostress_point_task(
    *,
    task_name: str,
    start_date: str = "2024-07-01",
    end_date: str = "2024-08-31",
    points: Iterable[dict[str, object]] = DEFAULT_POINT_SAMPLES,
    product: str = ECOSTRESS_PRODUCT,
    layers: Iterable[str] = ECOSTRESS_LAYERS,
) -> dict[str, Any]:
    """Build a minimal AppEEARS point request for ECOSTRESS JET layers."""

    return {
        "task_type": "point",
        "task_name": task_name,
        "params": {
            "dates": [
                {
                    "startDate": _appeears_date(start_date),
                    "endDate": _appeears_date(end_date),
                }
            ],
            "layers": [{"product": product, "layer": layer} for layer in layers],
            "coordinates": [_point_payload(point) for point in points],
        },
    }


def build_ecostress_tile_point_task(
    *,
    task_name: str,
    start_date: str = "2024-07-01",
    end_date: str = "2024-08-31",
    points: Iterable[dict[str, object]] = DEFAULT_TILE_POINT_SAMPLES,
    product: str = ECOSTRESS_PRODUCT,
    layers: Iterable[str] = ECOSTRESS_LAYERS,
) -> dict[str, Any]:
    """Build a tiny tile-like AppEEARS request from grouped public points.

    AppEEARS point outputs are small CSVs, so grouping several public points per
    tile gives the submission a field-like aggregation without introducing
    bulky raster downloads or geospatial dependencies into the repo.
    """

    return build_ecostress_point_task(
        task_name=task_name,
        start_date=start_date,
        end_date=end_date,
        points=points,
        product=product,
        layers=layers,
    )


def discover_product(product: str = ECOSTRESS_PRODUCT) -> dict[str, Any]:
    """Fetch product layer metadata from AppEEARS."""

    status, _, payload = _request_json(f"{APPEEARS_API_BASE}/product/{urllib.parse.quote(product)}")
    if status >= 400:
        raise AppEearsError(_message_from_payload(payload, f"product lookup failed with HTTP {status}"))
    return payload


def bundle_files(bundle: dict[str, Any]) -> tuple[AppEearsFile, ...]:
    files = []
    for row in bundle.get("files", []):
        files.append(
            AppEearsFile(
                file_id=str(row["file_id"]),
                file_name=str(row["file_name"]),
                file_type=str(row.get("file_type", "")),
                file_size=int(row.get("file_size", 0) or 0),
                sha256=str(row["sha256"]) if row.get("sha256") else None,
            )
        )
    return tuple(files)


def read_appeears_point_csv(path: Path) -> list[dict[str, str]]:
    """Read an AppEEARS point CSV, tolerating leading metadata lines."""

    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    header_index = _find_csv_header_index(lines)
    reader = csv.DictReader(lines[header_index:])
    return [dict(row) for row in reader]


def derive_ecostress_candidate_rows(
    appeears_rows: Iterable[dict[str, str]],
    *,
    date_start: str,
    date_end: str,
    geometry_label: str = "central-valley-public-point-sample",
    product: str = ECOSTRESS_PRODUCT,
    doi: str = ECOSTRESS_DOI,
) -> list[dict[str, object]]:
    """Convert AppEEARS point rows into the candidate-tile feature schema."""

    rows = list(appeears_rows)
    if not rows:
        return []

    columns = _column_map(rows[0].keys())
    etdaily_col = _find_column(columns, "etdaily")
    uncertainty_col = _find_column(columns, "etinstuncertainty", required=False)
    cloud_col = _find_column(columns, "cloud", required=False)
    water_col = _find_column(columns, "water", required=False)
    date_col = _find_column(columns, "date", required=False) or _find_column(columns, "time", required=False)
    id_col = _find_column(columns, "id", required=False)
    tile_id_col = _find_column(columns, "tileid", required=False)
    category_col = _find_column(columns, "category", required=False)
    lat_col = _find_column(columns, "latitude", required=False) or _find_column(columns, "lat", required=False)
    lon_col = _find_column(columns, "longitude", required=False) or _find_column(columns, "lon", required=False)

    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        group_id = _group_id(row, id_col, tile_id_col, lat_col, lon_col)
        grouped.setdefault(group_id, []).append(row)

    end = _parse_iso_date(date_end)
    valid_et_mm_day: list[float] = []
    normalized: dict[str, list[dict[str, object]]] = {}

    for group_id, group_rows in grouped.items():
        for row in group_rows:
            water_value = _optional_float(row.get(water_col, "")) if water_col else None
            if water_value is not None and water_value >= 0.5:
                continue

            et_raw = _optional_float(row.get(etdaily_col, ""))
            if et_raw is None or _is_fill_value(et_raw):
                continue

            et_mm_day = _w_m2_to_mm_day(et_raw)
            valid_et_mm_day.append(et_mm_day)
            normalized.setdefault(group_id, []).append(
                {
                    "row": row,
                    "et_raw": et_raw,
                    "et_mm_day": et_mm_day,
                    "uncertainty_raw": _optional_float(row.get(uncertainty_col, "")) if uncertainty_col else None,
                    "cloud": _cloud_indicator(row.get(cloud_col, "")) if cloud_col else 0.0,
                    "date": _parse_flexible_date(row.get(date_col, "")) if date_col else None,
                }
            )

    if not valid_et_mm_day:
        return []

    baseline = _median(valid_et_mm_day)
    derived: list[dict[str, object]] = []
    for index, (group_id, values) in enumerate(sorted(normalized.items()), start=1):
        if not values:
            continue
        mean_et = sum(float(value["et_mm_day"]) for value in values) / len(values)
        mean_raw = sum(float(value["et_raw"]) for value in values) / len(values)
        mean_uncertainty = _mean_optional(value["uncertainty_raw"] for value in values)
        cloud_fraction = sum(float(value["cloud"]) for value in values) / len(values)
        latest_date = max((value["date"] for value in values if isinstance(value["date"], date)), default=end)
        source_row = values[0]["row"]
        assert isinstance(source_row, dict)

        candidate_id = _safe_tile_id(group_id, fallback=f"ecostress-point-{index:02d}")
        category = str(source_row.get(category_col, "")).strip() if category_col else ""
        confidence = _confidence(mean_raw, mean_uncertainty, cloud_fraction)
        sample_ids = {
            str(value["row"].get(id_col, "")).strip()
            for value in values
            if isinstance(value["row"], dict) and id_col and value["row"].get(id_col)
        }

        derived.append(
            {
                "tile_id": candidate_id,
                "land_use": category or "public ECOSTRESS point sample",
                "acres": 10.0,
                "source": "ecostress_derived",
                "product": product,
                "doi": doi,
                "date_start": date_start,
                "date_end": date_end,
                "geometry_label": geometry_label,
                "sample_count": len(sample_ids) if sample_ids else 1,
                "valid_observation_count": len(values),
                "latest_observation_date": latest_date.isoformat(),
                "et_anomaly_mm_day": round(mean_et - baseline, 3),
                "vegetation_index_delta": 0.0,
                "cloud_fraction": round(_clamp(cloud_fraction), 3),
                "days_since_seen": max(0, (end - latest_date).days),
                "user_priority": _default_priority(category),
                "confidence": round(confidence, 3),
                "full_chip_kib": 96.0,
                "summary_kib": 8.0,
                "processing_ms": 180,
                "energy_j": 4.0,
            }
        )
    return derived


def derive_from_download_dir(
    download_dir: Path,
    *,
    output_path: Path,
    date_start: str,
    date_end: str,
    geometry_label: str = "central-valley-public-point-sample",
) -> list[dict[str, object]]:
    """Build the derived fixture from downloaded AppEEARS CSV files."""

    rows: list[dict[str, str]] = []
    for csv_path in sorted(download_dir.glob("*.csv")):
        if "result" in csv_path.name.lower():
            rows.extend(read_appeears_point_csv(csv_path))
    if not rows:
        raise AppEearsError(f"no AppEEARS result CSV files found in {download_dir}")

    derived = derive_ecostress_candidate_rows(
        rows,
        date_start=date_start,
        date_end=date_end,
        geometry_label=geometry_label,
    )
    if not derived:
        raise AppEearsError("AppEEARS CSV files contained no valid non-water ETdaily rows")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(derived[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(derived)
    return derived


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _request_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
) -> tuple[int, dict[str, str], Any]:
    request = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
            return response.status, dict(response.headers), _json_or_text(body)
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return exc.code, dict(exc.headers), _json_or_text(body)
    except TimeoutError as exc:
        raise AppEearsError(f"request timed out: {url}") from exc
    except urllib.error.URLError as exc:
        raise AppEearsError(f"request failed: {url}: {exc.reason}") from exc


def _json_or_text(body: bytes) -> Any:
    text = body.decode("utf-8", errors="replace")
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"message": text}


def _message_from_payload(payload: Any, fallback: str) -> str:
    if isinstance(payload, dict) and payload.get("message"):
        return str(payload["message"])
    return fallback


def _read_macos_keychain_secret(alias: str, service: str) -> str | None:
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-a", alias, "-s", service, "-w"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def _parse_json_credentials(text: str) -> EarthdataCredentials | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    candidates = [payload]
    if isinstance(payload, dict):
        candidates.extend(value for value in payload.values() if isinstance(value, dict))
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        username = _first_value(candidate, ("username", "user", "login", "earthdata_username"))
        password = _first_value(candidate, ("password", "pass", "earthdata_password"))
        if username and password:
            return _validated_credentials(username, password)
    return None


def _parse_key_value_credentials(text: str) -> EarthdataCredentials | None:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
        elif ":" in line:
            key, value = line.split(":", 1)
        else:
            continue
        key = _normalize(key)
        value = value.strip().strip('"').strip("'")
        if key and value:
            values[key] = value

    username = _first_value(values, ("username", "user", "login", "earthdatausername", "earthdatalogin"))
    password = _first_value(values, ("password", "pass", "earthdatapassword"))
    if username and password:
        return _validated_credentials(username, password)
    return None


def _parse_encoded_credentials(text: str) -> EarthdataCredentials | None:
    compact = re.sub(r"\s+", "", text)
    candidates: list[str] = []

    if re.fullmatch(r"[0-9a-fA-F]+", compact or "") and len(compact) % 2 == 0:
        try:
            candidates.append(bytes.fromhex(compact).decode("utf-8"))
        except UnicodeDecodeError:
            pass

    if re.fullmatch(r"[A-Za-z0-9+/=]+", compact or "") and len(compact) % 4 == 0:
        try:
            candidates.append(base64.b64decode(compact, validate=True).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            pass

    for candidate in candidates:
        try:
            return parse_earthdata_credentials(candidate)
        except CredentialError:
            continue
    return None


def _parse_netrc_credentials(text: str) -> EarthdataCredentials | None:
    tokens = text.replace("\n", " ").split()
    if "login" not in tokens or "password" not in tokens:
        return None
    try:
        username = tokens[tokens.index("login") + 1]
        password = tokens[tokens.index("password") + 1]
    except IndexError:
        return None
    return _validated_credentials(username, password)


def _first_value(mapping: dict[str, Any], keys: Iterable[str]) -> str | None:
    normalized = {_normalize(str(key)): str(value) for key, value in mapping.items() if value is not None}
    for key in keys:
        value = normalized.get(_normalize(key))
        if value:
            return value
    return None


def _validated_credentials(username: str, password: str) -> EarthdataCredentials:
    username = username.strip()
    password = password.strip()
    if not username or not password:
        raise CredentialError("credential username or password is empty")
    return EarthdataCredentials(username=username, password=password)


def _appeears_date(value: str) -> str:
    parsed = _parse_iso_date(value)
    return parsed.strftime("%m-%d-%Y")


def _parse_iso_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_flexible_date(value: str | None) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt, width in (
        ("%Y-%m-%d", 10),
        ("%m/%d/%Y", 10),
        ("%m-%d-%Y", 10),
        ("%Y-%m-%dT%H:%M:%S", 19),
        ("%Y-%m-%d %H:%M:%S", 19),
    ):
        try:
            return datetime.strptime(text[:width], fmt).date()
        except ValueError:
            continue
    match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    if match:
        return _parse_iso_date(match.group(0))
    return None


def _point_payload(point: dict[str, object]) -> dict[str, object]:
    payload = {
        "latitude": float(point["latitude"]),
        "longitude": float(point["longitude"]),
    }
    if point.get("id"):
        payload["id"] = str(point["id"])
    if point.get("category"):
        payload["category"] = str(point["category"])
    return payload


def _find_csv_header_index(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        normalized = _normalize(line)
        if "etdaily" in normalized and ("date" in normalized or "latitude" in normalized):
            return index
    return 0


def _column_map(columns: Iterable[str]) -> dict[str, str]:
    return {_normalize(column): column for column in columns}


def _find_column(columns: dict[str, str], needle: str, *, required: bool = True) -> str | None:
    normalized_needle = _normalize(needle)
    for normalized, original in columns.items():
        if normalized == normalized_needle or normalized_needle in normalized:
            return original
    if required:
        raise AppEearsError(f"required AppEEARS column not found: {needle}")
    return None


def _group_id(
    row: dict[str, str],
    id_col: str | None,
    tile_id_col: str | None,
    lat_col: str | None,
    lon_col: str | None,
) -> str:
    if tile_id_col and row.get(tile_id_col):
        return str(row[tile_id_col])
    if id_col and row.get(id_col):
        return _tile_id_from_sample_id(str(row[id_col]))
    if lat_col and lon_col:
        return f"{row.get(lat_col, '')}_{row.get(lon_col, '')}"
    return "ecostress-point"


def _tile_id_from_sample_id(value: str) -> str:
    text = value.strip()
    for pattern in (r"__p\d+$", r"[-_:]p\d+$", r"[-_:]sample\d+$"):
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return text


def _safe_tile_id(value: str, *, fallback: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower()).strip("-")
    return text or fallback


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "na", "n/a"}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _is_fill_value(value: float) -> bool:
    return value <= -9_000 or value >= 1.0e20


def _cloud_indicator(value: object) -> float:
    number = _optional_float(value)
    if number is None:
        return 0.0
    return 1.0 if number >= 0.5 else 0.0


def _w_m2_to_mm_day(value: float) -> float:
    return value * 86_400.0 / 2_450_000.0


def _mean_optional(values: Iterable[object]) -> float | None:
    numbers = [float(value) for value in values if isinstance(value, (float, int))]
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def _confidence(mean_raw: float, mean_uncertainty: float | None, cloud_fraction: float) -> float:
    if mean_uncertainty is None:
        base = 0.75
    else:
        base = 1.0 - (abs(mean_uncertainty) / max(abs(mean_raw), 1.0))
    return _clamp(base * (1.0 - 0.5 * cloud_fraction), 0.05, 0.98)


def _default_priority(category: str) -> float:
    normalized = _normalize(category)
    if "riparian" in normalized:
        return 0.85
    if "regenerative" in normalized:
        return 0.80
    if "agriculture" in normalized or "irrigated" in normalized:
        return 0.75
    return 0.65


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())
