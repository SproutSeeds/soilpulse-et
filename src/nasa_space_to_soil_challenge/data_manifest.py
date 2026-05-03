"""Local data manifest helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from .paths import DATA_DIR

IGNORED_NAMES = {"README.md", ".DS_Store"}


@dataclass(frozen=True)
class LocalDataFile:
    """Metadata for one local data artifact."""

    path: str
    size_bytes: int
    suffix: str
    sha256: str | None = None
    sha256_note: str | None = None


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_local_data_files(
    data_dir: Path = DATA_DIR,
    *,
    include_hash: bool = False,
    max_hash_bytes: int = 100_000_000,
) -> list[LocalDataFile]:
    """Return tracked metadata for local data files under ``data_dir``."""

    if not data_dir.exists():
        return []

    rows: list[LocalDataFile] = []
    for path in sorted(p for p in data_dir.rglob("*") if p.is_file()):
        if path.name in IGNORED_NAMES:
            continue
        relative = path.relative_to(data_dir).as_posix()
        size_bytes = path.stat().st_size
        digest: str | None = None
        digest_note: str | None = None
        if include_hash:
            if size_bytes <= max_hash_bytes:
                digest = _file_sha256(path)
            else:
                digest_note = f"skipped: file exceeds max_hash_bytes={max_hash_bytes}"
        rows.append(
            LocalDataFile(
                path=relative,
                size_bytes=size_bytes,
                suffix=path.suffix,
                sha256=digest,
                sha256_note=digest_note,
            )
        )
    return rows


def build_manifest(
    data_dir: Path = DATA_DIR,
    *,
    include_hash: bool = False,
    max_hash_bytes: int = 100_000_000,
) -> dict[str, Any]:
    """Build a JSON-serializable local data manifest."""

    files = iter_local_data_files(
        data_dir,
        include_hash=include_hash,
        max_hash_bytes=max_hash_bytes,
    )
    return {
        "data_root": str(data_dir),
        "file_count": len(files),
        "files": [asdict(row) for row in files],
        "policy": {
            "raw_data_committed": False,
            "hashing_default": "off",
            "data_note": "Do not commit bulky challenge data or private submission artifacts.",
        },
    }
