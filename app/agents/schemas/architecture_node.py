from typing import Literal

from pydantic import BaseModel, Field


class ArchitecturePlan(BaseModel):
    architecture_markdown: str = Field(
        description=(
            "A comprehensive, human-readable Markdown architecture document "
            "describing the complete cloud architecture, components, networking, "
            "security, identity, data, compute, monitoring, scaling, dependencies, "
            "deployment flow, and important architectural decisions."
        )
    )

    cloud_provider: Literal[
        "azurerm",
        "aws",
        "google",
    ] = Field(
        description=(
            "The exact Terraform provider identifier used for the architecture. "
            "Must be one of: azurerm, aws, google."
        )
    )

    terraform_resources: list[str] = Field(
        description=(
            "Complete list of exact Terraform resource type identifiers required "
            "to implement the architecture. These values will be used directly "
            "as documentation lookup keys / filenames. Do not return cloud-service "
            "names, friendly names, logical names, or invented identifiers."
        )
    )
    