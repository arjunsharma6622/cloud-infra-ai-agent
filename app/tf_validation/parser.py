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
                "severity": diag.get("severity", "error"),
                "summary": diag.get("summary", ""),
                "detail": diag.get("detail", ""),
            }
        )

    return (
        bool(data.get("valid", False)),
        diagnostics,
    )