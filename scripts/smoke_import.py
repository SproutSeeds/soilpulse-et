from nasa_space_to_soil_challenge import PROFILE, ensure_workspace_dirs


def main() -> None:
    ensure_workspace_dirs()
    print(f"{PROFILE.title} [{PROFILE.status}]")
    for focus in PROFILE.first_focus:
        print(f"- {focus}")


if __name__ == "__main__":
    main()
