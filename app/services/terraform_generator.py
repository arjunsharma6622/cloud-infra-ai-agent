from pydantic import BaseModel, Field

from app.config import AgentType
from app.llms import get_agent_structured_llm


class TerraformProject(BaseModel):
    main_tf: str = Field(description="Complete production-ready main.tf")
    variables_tf: str = Field(description="Complete variables.tf")
    outputs_tf: str = Field(description="Complete outputs.tf")


FORMATTING_RULES = """
CRITICAL FORMATTING RULES

- Return valid Terraform HCL.
- Preserve proper indentation.
- Do not compress code into one line.
- Return complete file contents.
- Do not wrap code in markdown fences.
"""


def generate_terraform(
    architecture_plan: str,
    validation_attempts: int = 0,
    validation_stage: str | None = None,
    validation_errors: list[dict] | None = None,
    previous_code: dict[str, str] | None = None,
) -> dict[str, str]:

    structured_llm = get_agent_structured_llm(
        AgentType.GENERATOR,
        TerraformProject,
    )

    if validation_attempts == 0:

        prompt = f"""
{FORMATTING_RULES}

Generate production-ready Terraform code from the following architecture.

Architecture Plan:

{architecture_plan}
"""

    else:

        diagnostics = "\n".join(
            f"""
File: {d.get("file", "")}
Severity: {d.get("severity", "")}
Summary: {d.get("summary", "")}
Details: {d.get("detail", "")}
"""
            for d in (validation_errors or [])
        )

        prompt = f"""
{FORMATTING_RULES}

The previous Terraform failed during:

Validation Stage : {validation_stage}

Below are the diagnostics.
Fix every issue.

Your task is to FIX the existing Terraform.

Architecture Plan:

{architecture_plan}

Validation Stage:

{validation_stage}

Validation Diagnostics:

{diagnostics}

Previous Terraform:

{previous_code}

Requirements:

- Fix ONLY the reported issues.
- Preserve the architecture.
- Preserve naming conventions.
- Do not remove resources unless required.
- Return complete corrected Terraform files.
"""

    result: TerraformProject = structured_llm.invoke(prompt)

    return {
        "main.tf": result.main_tf,
        "variables.tf": result.variables_tf,
        "outputs.tf": result.outputs_tf,
    }
