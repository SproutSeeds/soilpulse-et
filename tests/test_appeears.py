from pathlib import Path

import pytest

from nasa_space_to_soil_challenge.appeears import (
    ECOSTRESS_LAYERS,
    ECOSTRESS_PRODUCT,
    build_ecostress_point_task,
    build_ecostress_tile_point_task,
    CredentialError,
    derive_ecostress_candidate_rows,
    parse_earthdata_credentials,
    read_appeears_point_csv,
)


def test_parse_earthdata_credentials_from_key_value_text() -> None:
    credentials = parse_earthdata_credentials("username: example_user\npassword: example_secret\n")

    assert credentials.username == "example_user"
    assert credentials.password == "example_secret"


def test_parse_earthdata_credentials_from_hex_encoded_pair() -> None:
    encoded = "example_user:example_secret".encode("utf-8").hex()

    credentials = parse_earthdata_credentials(encoded)

    assert credentials.username == "example_user"
    assert credentials.password == "example_secret"


def test_parse_earthdata_credentials_rejects_unlabeled_multiline_text() -> None:
    with pytest.raises(CredentialError):
        parse_earthdata_credentials("not credentials\nstill not credentials\nextra line\n")


def test_build_ecostress_point_task_uses_current_appeears_product() -> None:
    task = build_ecostress_point_task(task_name="unit-test")

    assert task["task_type"] == "point"
    assert task["task_name"] == "unit-test"
    layers = task["params"]["layers"]
    assert [layer["layer"] for layer in layers] == list(ECOSTRESS_LAYERS)
    assert {layer["product"] for layer in layers} == {ECOSTRESS_PRODUCT}
    assert task["params"]["dates"][0]["startDate"] == "07-01-2024"


def test_build_ecostress_tile_point_task_groups_public_samples() -> None:
    task = build_ecostress_tile_point_task(task_name="unit-test")

    coordinates = task["params"]["coordinates"]

    assert task["task_type"] == "point"
    assert len(coordinates) == 12
    assert coordinates[0]["id"] == "cv-covercrop-013__p01"
    assert coordinates[0]["category"] == "cover-cropped almond block"


def test_read_appeears_point_csv_skips_metadata_header(tmp_path: Path) -> None:
    path = tmp_path / "result.csv"
    path.write_text(
        "AppEEARS output\n"
        "generated,metadata\n"
        "ID,Category,Latitude,Longitude,Date,ECO_L3T_JET_002_ETdaily\n"
        "p1,irrigated,36.7,-121.6,2024-07-01,100\n",
        encoding="utf-8",
    )

    rows = read_appeears_point_csv(path)

    assert rows == [
        {
            "ID": "p1",
            "Category": "irrigated",
            "Latitude": "36.7",
            "Longitude": "-121.6",
            "Date": "2024-07-01",
            "ECO_L3T_JET_002_ETdaily": "100",
        }
    ]


def test_derive_ecostress_candidate_rows_masks_water_and_computes_anomaly() -> None:
    source_rows = [
        {
            "ID": "field-a",
            "Category": "irrigated_agriculture",
            "Latitude": "36.7",
            "Longitude": "-121.6",
            "Date": "2024-07-10",
            "ECO_L3T_JET_002_ETdaily": "80",
            "ECO_L3T_JET_002_ETinstUncertainty": "8",
            "ECO_L3T_JET_002_cloud": "0",
            "ECO_L3T_JET_002_water": "0",
        },
        {
            "ID": "field-b",
            "Category": "riparian_buffer",
            "Latitude": "36.8",
            "Longitude": "-121.5",
            "Date": "2024-07-11",
            "ECO_L3T_JET_002_ETdaily": "120",
            "ECO_L3T_JET_002_ETinstUncertainty": "12",
            "ECO_L3T_JET_002_cloud": "1",
            "ECO_L3T_JET_002_water": "0",
        },
        {
            "ID": "field-c",
            "Category": "water",
            "Latitude": "36.9",
            "Longitude": "-121.4",
            "Date": "2024-07-12",
            "ECO_L3T_JET_002_ETdaily": "999",
            "ECO_L3T_JET_002_ETinstUncertainty": "1",
            "ECO_L3T_JET_002_cloud": "0",
            "ECO_L3T_JET_002_water": "1",
        },
    ]

    derived = derive_ecostress_candidate_rows(source_rows, date_start="2024-07-01", date_end="2024-08-31")

    assert [row["tile_id"] for row in derived] == ["field-a", "field-b"]
    assert derived[0]["source"] == "ecostress_derived"
    assert derived[0]["product"] == ECOSTRESS_PRODUCT
    assert derived[0]["et_anomaly_mm_day"] == pytest.approx(-0.705)
    assert derived[1]["et_anomaly_mm_day"] == pytest.approx(0.705)
    assert derived[1]["cloud_fraction"] == 1.0
    assert derived[1]["user_priority"] == 0.85


def test_derive_ecostress_candidate_rows_groups_microtile_samples() -> None:
    source_rows = [
        {
            "ID": "cv-covercrop-013__p01",
            "Category": "cover-cropped almond block",
            "Latitude": "36.660",
            "Longitude": "-121.704",
            "Date": "2024-07-10",
            "ECO_L3T_JET_002_ETdaily": "80",
            "ECO_L3T_JET_002_ETinstUncertainty": "8",
            "ECO_L3T_JET_002_cloud": "0",
            "ECO_L3T_JET_002_water": "0",
        },
        {
            "ID": "cv-covercrop-013__p02",
            "Category": "cover-cropped almond block",
            "Latitude": "36.663",
            "Longitude": "-121.700",
            "Date": "2024-07-12",
            "ECO_L3T_JET_002_ETdaily": "100",
            "ECO_L3T_JET_002_ETinstUncertainty": "10",
            "ECO_L3T_JET_002_cloud": "1",
            "ECO_L3T_JET_002_water": "0",
        },
        {
            "ID": "cv-vineyard-032__p01",
            "Category": "deficit-irrigated vineyard",
            "Latitude": "36.738",
            "Longitude": "-121.614",
            "Date": "2024-07-12",
            "ECO_L3T_JET_002_ETdaily": "140",
            "ECO_L3T_JET_002_ETinstUncertainty": "14",
            "ECO_L3T_JET_002_cloud": "0",
            "ECO_L3T_JET_002_water": "0",
        },
    ]

    derived = derive_ecostress_candidate_rows(source_rows, date_start="2024-07-01", date_end="2024-08-31")

    assert [row["tile_id"] for row in derived] == ["cv-covercrop-013", "cv-vineyard-032"]
    assert derived[0]["sample_count"] == 2
    assert derived[0]["valid_observation_count"] == 2
    assert derived[0]["latest_observation_date"] == "2024-07-12"
    assert derived[0]["cloud_fraction"] == 0.5
