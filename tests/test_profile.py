from nasa_space_to_soil_challenge import PROFILE, PROJECT_ROOT, ensure_workspace_dirs


def test_profile_slug() -> None:
    assert PROFILE.slug == "nasa-space-to-soil-challenge"


def test_workspace_dirs_exist() -> None:
    ensure_workspace_dirs()
    assert PROJECT_ROOT.exists()
    assert (PROJECT_ROOT / "data").exists()
    assert (PROJECT_ROOT / "docs").exists()
    assert (PROJECT_ROOT / "notebooks").exists()
    assert (PROJECT_ROOT / "scripts").exists()
    assert (PROJECT_ROOT / "submission").exists()
