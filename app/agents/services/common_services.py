
def find_affected_units(
    diagnostics: list[dict],
    generation_units: list[dict],
) -> list[str]:

    affected_units = []

    for unit in generation_units:
        unit_name = unit["name"]
        unit_path = unit["path"].rstrip("/")

        for diagnostic in diagnostics:
            file_path = diagnostic.get("file", "").replace("\\", "/")

            if not file_path:
                continue

            if unit_path in ("", "."):
                is_match = "/" not in file_path
            else:
                is_match = (
                    file_path == unit_path
                    or file_path.startswith(unit_path + "/")
                )

            if is_match:
                affected_units.append(unit_name)
                break

    return affected_units
