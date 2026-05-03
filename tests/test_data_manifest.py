from pathlib import Path

from nasa_space_to_soil_challenge.data_manifest import build_manifest, iter_local_data_files


def test_iter_local_data_files_skips_readme(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("do not count me\n", encoding="utf-8")
    (tmp_path / "sample.txt").write_text("abc\n", encoding="utf-8")

    rows = iter_local_data_files(tmp_path)

    assert [row.path for row in rows] == ["sample.txt"]
    assert rows[0].size_bytes == 4
    assert rows[0].sha256 is None


def test_build_manifest_can_hash_small_files(tmp_path: Path) -> None:
    (tmp_path / "sample.txt").write_text("abc\n", encoding="utf-8")

    manifest = build_manifest(tmp_path, include_hash=True)

    assert manifest["file_count"] == 1
    assert manifest["files"][0]["path"] == "sample.txt"
    assert manifest["files"][0]["sha256"] == "edeaaff3f1774ad2888673770c6d64097e391bc362d7d6fb34982ddf0efd18cb"
    assert manifest["policy"]["raw_data_committed"] is False
