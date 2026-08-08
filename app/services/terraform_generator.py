from pydantic import BaseModel, Field

from app.config import AgentType
from app.llms import get_agent_structured_llm

from app.schemas import ArchitecturePlan


class TerraformProject(BaseModel):
    main_tf: str = Field(description="Complete production-ready main.tf")
    variables_tf: str = Field(description="Complete variables.tf")
    outputs_tf: str = Field(description="Complete outputs.tf")


FORMATTING_RULES = """
==============================
TERRAFORM FORMATTING RULES
==============================

You are generating files that will be written DIRECTLY to disk and executed by Terraform.

Follow ALL rules strictly.

1. Every file MUST be valid Terraform HCL.

2. Preserve proper formatting exactly as a human would write in VS Code.

3. Every resource, variable, output, provider, data source, locals block, module block and terraform block MUST start on a NEW LINE.

4. Leave ONE blank line between top-level blocks.

5. Use normal indentation (2 spaces) inside every block.

6. Never compress multiple attributes onto one line.

7. Never return escaped newline characters (\\n).

8. Return actual newline characters.

9. Do NOT minify or compress the code.

10. Do NOT wrap the code inside Markdown code fences.

11. Return ONLY the file contents.

The files must be immediately executable by Terraform without any formatting changes.
"""


def generate_terraform(
    architecture_plan: ArchitecturePlan,
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

{architecture_plan.architecture_markdown}
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

{architecture_plan.architecture_markdown}

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
        "generated_code": {
            "main.tf": result.main_tf,
            "variables.tf": result.variables_tf,
            "outputs.tf": result.outputs_tf,
        },
        "generation_prompt": prompt,
    }
