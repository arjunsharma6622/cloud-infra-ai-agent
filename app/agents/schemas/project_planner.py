from pydantic import BaseModel, Field


class TerraformGenerationUnit(BaseModel):
    name: str = Field(
        description=(
            "Logical name of this infrastructure unit, e.g. network, "
            "database, compute, security."
        )
    )

    path: str = Field(
        description=(
            "Terraform directory path for this unit. "
            "Use '.' for the root project."
        )
    )

    purpose: str = Field(
        description="What this infrastructure unit is responsible for."
    )

    terraform_resources: list[str] = Field(
        description=(
            "Terraform resource types from the Architecture Agent that "
            "belong to this generation unit."
        )
    )

    depends_on: list[str] = Field(
        default_factory=list,
        description=(
            "Names of other generation units that this unit genuinely "
            "depends on. Only include dependencies supported by the "
            "architecture. Do not invent dependencies."
        )
    )

    input_requirements: list[str] = Field(
        default_factory=list,
        description=(
            "Values this unit must receive from another generation unit "
            "to implement the architecture correctly. Only include inputs "
            "that are genuinely required. Examples: subnet_id, vnet_id, "
            "managed_identity_id. Do not invent inputs."
        )
    )

    output_requirements: list[str] = Field(
        default_factory=list,
        description=(
            "Values this unit must expose because another generation unit "
            "requires them. Only include outputs that are genuinely required "
            "by another unit. Do not invent outputs."
        )
    )

    files: list[str] = Field(
        description=(
            "Terraform files that should be generated for this unit. "
            "For a module this will commonly be main.tf, variables.tf, "
            "and outputs.tf."
        )
    )


class TerraformProjectPlan(BaseModel):
    complexity: str = Field(
        description="Overall project complexity: simple, medium, or complex."
    )

    generation_units: list[TerraformGenerationUnit] = Field(
        description=(
            "Ordered list of logical Terraform generation units. "
            "Units must be ordered so dependencies are generated first."
        )
    )