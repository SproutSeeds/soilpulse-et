from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
SUBMISSION_DIR = PROJECT_ROOT / "submission"


def ensure_workspace_dirs() -> None:
    """Create the standard workspace directories if they are missing."""

    for path in (DATA_DIR, DOCS_DIR, NOTEBOOKS_DIR, SCRIPTS_DIR, SUBMISSION_DIR):
        path.mkdir(parents=True, exist_ok=True)
