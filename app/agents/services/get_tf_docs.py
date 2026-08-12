import os
from pathlib import Path


DOCS_ROOT = Path(os.getenv("TERRAFORM_DOCS_PATH"))


PROVIDER_CONFIG = {
    "azurerm": {
        "directory": "azurerm",
        "prefix": "azurerm_",
    },
    "aws": {
        "directory": "aws",
        "prefix": "aws_",
    },
    "google": {
        "directory": "google",
        "prefix": "google_",
    },
}


def get_terraform_docs(
    cloud_provider: str,
    terraform_types: list[str],
) -> dict[str, str]:

    config = PROVIDER_CONFIG.get(cloud_provider)

    if not config:
        raise ValueError(
            f"Unsupported cloud provider: {cloud_provider}"
        )

    provider_dir = (
        DOCS_ROOT / config["directory"]
    )

    docs: dict[str, str] = {}

    for terraform_type in terraform_types:

        if not terraform_type.startswith(config["prefix"]):
            raise ValueError(
                f"Terraform type '{terraform_type}' "
                f"does not belong to provider '{cloud_provider}'"
            )

        resource_name = terraform_type[
            len(config["prefix"]):
        ]

        # Example:
        # azurerm_virtual_network
        # ->
        # terraform_docs/azurerm/virtual_network.html.markdown

        doc_path = (
            provider_dir
            / f"{resource_name}.html.markdown"
        )

        if not doc_path.exists():
            # print(
            #     f"[Docs] Documentation not found: "
            #     f"{terraform_type}"
            # )
            continue

        docs[terraform_type] = doc_path.read_text(
            encoding="utf-8"
        )

        # print(
        #     f"[Docs] Loaded: {terraform_type}"
        # )

    return docs