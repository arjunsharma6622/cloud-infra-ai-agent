from pydantic import BaseModel, Field

from app.config import AgentType
from app.llms import get_agent_structured_llm

class TerraformUnitProject(BaseModel):
    files: dict[str, str] = Field(
        description=(
            "Complete Terraform files for this generation unit. "
            "Keys are file paths relative to the generation unit path. "
            "Values are the complete file contents."
        )
    )


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
    architecture_plan: str,
    generation_unit: dict,
    terraform_docs: dict[str, str],
    dependency_context: dict,
    generation_mode: str,
    validation_stage: str | None = None,
    validation_errors: list[dict] | None = None,
    previous_code: dict[str, str] | None = None,
) -> dict:

    structured_llm = get_agent_structured_llm(
        AgentType.GENERATOR,
        TerraformUnitProject,
    )

    is_repair = generation_mode == "repair"

    docs_text = "\n\n".join(
        f"""
        ========================================
        TERRAFORM DOCUMENTATION
        Resource Type: {resource_type}
        ========================================

        {content}
        """
                for resource_type, content in terraform_docs.items()
            )

    dependency_text = "\n\n".join(
        f"""
        ========================================
        DEPENDENCY: {unit_name}
        ========================================

        {context}
        """
        for unit_name, context in dependency_context.items()
    )

    if is_repair:
        diagnostics = "\n".join(
            f"""
            File: {d.get("file", "")}
            Severity: {d.get("severity", "")}
            Summary: {d.get("summary", "")}
            Details: {d.get("detail", "")}
            """
            for d in (validation_errors or [])
        )

        previous_files = "\n\n".join(
            f"""
            ========================================
            PREVIOUS FILE: {file_path}
            ========================================

            {content}
            """
            for file_path, content in previous_code.items()
        )

        prompt = f"""
{FORMATTING_RULES}

You are repairing ONE Terraform generation unit.

The Terraform project was validated and the current generation unit
contains one or more validation errors.

Your task is to regenerate the COMPLETE CURRENT GENERATION UNIT.

Do not regenerate the entire Terraform project.

========================================
ARCHITECTURE
========================================

{architecture_plan}

========================================
CURRENT GENERATION UNIT
========================================

{generation_unit}

========================================
LATEST DEPENDENCY CONTEXT
========================================

{dependency_text}

========================================
TERRAFORM DOCUMENTATION
========================================

{docs_text}

========================================
VALIDATION STAGE
========================================

{validation_stage}

========================================
VALIDATION DIAGNOSTICS
========================================

{diagnostics}

========================================
PREVIOUS CURRENT-UNIT CODE
========================================

{previous_files}

========================================
REPAIR REQUIREMENTS
========================================

- Fix the reported validation issues.
- Regenerate the COMPLETE current generation unit.
- Preserve the generation unit's purpose.
- Preserve its required inputs.
- Preserve its required outputs.
- Preserve its resource assignments.
- Preserve naming conventions.
- Preserve compatibility with the latest dependency context.
- Do not modify unrelated generation units.
- Do not invent new infrastructure requirements.
- Do not remove resources unless required to fix the validation issue.
"""

    else:
        prompt = f"""
{FORMATTING_RULES}

You are generating ONE Terraform generation unit.

Generate the complete Terraform implementation for the CURRENT
generation unit described below.

========================================
ARCHITECTURE
========================================

{architecture_plan}

========================================
CURRENT GENERATION UNIT
========================================

{generation_unit}

========================================
LATEST DEPENDENCY CONTEXT
========================================

{dependency_text}

========================================
TERRAFORM DOCUMENTATION
========================================

{docs_text}

========================================
GENERATION REQUIREMENTS
========================================

- Generate ONLY this generation unit.
- Generate every file specified by the generation unit.
- Implement every Terraform resource assigned to this unit.
- Follow the input requirements exactly.
- Produce every required output.
- Make the outputs usable by dependent units.
- Use the Terraform documentation as the authoritative source for
  resource arguments and syntax.
- Do not invent resources that are not part of the architecture.
- Do not generate resources belonging to another generation unit.
- Make the generated unit internally consistent.
- Make the generated unit compatible with its dependencies.
"""

    result: TerraformUnitProject = structured_llm.invoke(prompt)

    return {
        "generated_code": result.files,
        "generation_prompt": prompt,
    }
