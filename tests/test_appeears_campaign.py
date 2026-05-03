from pathlib import Path

import pytest

from scripts.run_appeears_event_campaign import parse_window


def test_parse_window_creates_stable_output_path() -> None:
    window = parse_window("2024-06-01..2024-07-31", Path("tests/fixtures"))

    assert window.start_date == "2024-06-01"
    assert window.end_date == "2024-07-31"
    assert window.output_path == Path("tests/fixtures/ecostress_derived_2024_06_2024_07.csv")


def test_parse_window_rejects_bad_format() -> None:
    with pytest.raises(ValueError):
        parse_window("2024-06-01/2024-07-31", Path("tests/fixtures"))
