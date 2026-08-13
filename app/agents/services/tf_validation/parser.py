import json
from typing import Any


def parse_validation_output(terraform_output: str) -> tuple[bool, list[dict[str, str]]]:
    """
    Parse the JSON output from:
        terraform validate -json

    Returns:
        (
            validation_passed,
            diagnostics
        )

    diagnostics format:
    [
        {
            "file": "main.tf",
            "severity": "error",
            "summary": "...",
            "detail": "..."
        }
    ]
    """

    try:
        data: dict[str, Any] = json.loads(terraform_output)
    except json.JSONDecodeError:
        return (
            False,
            [
                {
                    "file": "",
                    "severity": "error",
                    "summary": "Unable to parse Terraform output",
                    "detail": terraform_output.strip(),
                }
            ],
        )

    diagnostics: list[dict[str, str]] = []

    for diag in data.get("diagnostics", []):

        diagnostics.append(
            {
                "file": diag.get("range", {}).get("filename", ""),
                "line": str(
                    diag.get("range", {})
                        .get("start", {})
                        .get("line", "")
                ),
                "severity": diag.get("severity", "error"),
                "summary": diag.get("summary", ""),
                "detail": diag.get("detail", ""),
            }
        )

    return (
        bool(data.get("valid", False)),
        diagnostics,
    )

def parse_init_output(
    terraform_output: str,
) -> tuple[bool, list[dict[str, str]]]:
    """
    Parse JSON Lines output from:

        terraform init -json

    Returns:
        (
            init_passed,
            diagnostics
        )

    diagnostics format:
        [
            {
                "file": "main.tf",
                "line": "2",
                "severity": "error",
                "summary": "...",
                "detail": "..."
            }
        ]
    """

    diagnostics: list[dict[str, str]] = []
    has_error = False

    for line in terraform_output.splitlines():
        line = line.strip()

        if not line:
            continue

        try:
            data: dict[str, Any] = json.loads(line)
        except json.JSONDecodeError:
            continue

        diagnostic = data.get("diagnostic")

        if not diagnostic:
            continue

        severity = diagnostic.get(
            "severity",
            data.get("@level", "error")
        )

        if severity == "error":
            has_error = True

        range_data = diagnostic.get("range", {})
        start = range_data.get("start", {})

        diagnostics.append(
            {
                "file": range_data.get("filename", ""),
                "line": str(start.get("line", "")),
                "severity": severity,
                "summary": diagnostic.get("summary", ""),
                "detail": diagnostic.get("detail", "")
            }
        )

    return (
        not has_error,
        diagnostics
    )

