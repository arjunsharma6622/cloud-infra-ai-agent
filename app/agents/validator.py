from .state import AgentState

from .services.tf_validation.workspace import (
    write_files,
    cleanup_workspace,
)

from .services.tf_validation.runner import (
    terraform_init,
    terraform_validate,
)

from .services.tf_validation.parser import (
    parse_validation_output,
)

from .services.tf_validation.validation_context import ValidationContext

from .services.tf_validation.logger import (
    log_attempt,
    log_stage,
    log_success,
    log_failure
)

def assemble_generated_code(
    generated_units: dict[str, dict[str, str]],
    generation_units: list[dict],
) -> dict[str, str]:
    """
    Flatten all generation-unit files into a single project file map.

    Example:

    {
        "network": {
            "main.tf": "...",
        },
        "compute": {
            "main.tf": "...",
        }
    }

    becomes:

    {
        "modules/network/main.tf": "...",
        "modules/compute/main.tf": "..."
    }
    """

    project_files = {}

    for unit in generation_units:

        unit_name = unit["name"]
        unit_path = unit["path"]

        unit_files = generated_units.get(unit_name, {})

        for filename, content in unit_files.items():

            if unit_path in ("", "."):
                file_path = filename
            else:
                file_path = f"{unit_path.rstrip('/')}/{filename}"

            project_files[file_path] = content

    return project_files


async def validation_agent_node(state: AgentState) -> dict:
    print("--- [Agent] Validation Agent Working ---")

    attempts = state.get("validation_attempts", 0)
    # generated_code = state["generated_code"]
    generated_units = state.get("generated_units", {})
    generation_units = state["project_plan"]["generation_units"]

    generated_code = assemble_generated_code(
        generated_units,
        generation_units,
    )

    validation_ctx = ValidationContext.from_state(state)

    validation_run_id = validation_ctx.validation_run_id

    workspace = validation_ctx.workspace
    validation_logger = validation_ctx.logger

    if not generated_code:
        log_failure("Generator produced no Terraform files.")

        return {
            "validation_run_id": validation_run_id,
            "validation_passed": False,
            "validation_stage": "generator",
            "validation_errors": [
                {
                    "file": "",
                    "severity": "error",
                    "summary": "Generator produced no Terraform files.",
                    "detail": "",
                }
            ],
            "validation_attempts": attempts + 1,
        }

    log_attempt(
        validation_run_id,
        attempts + 1,
        workspace,
    )

            # Save everything that produced THIS attempt
    validation_logger.save_prompt(
        state["generation_prompt"]
    )

    try:
        log_stage("Writing Terraform files")

        # Write generated Terraform files
        write_files(workspace, generated_code)

        log_success("Terraform files written.")


        # -----------------------------
        # Terraform Init
        # -----------------------------
        log_stage("terraform init")

        init_code, init_output = await terraform_init(workspace)

        if init_code != 0:
            log_failure("terraform init failed.")

            validation_logger.save_command_output(
                command="terraform_init",
                return_code=init_code,
                output=init_output,
            )

            validation_logger.save_summary(
                attempt=attempts + 1,
                stage="terraform_init",
                passed=False,
            )

            return {
                "validation_run_id": validation_run_id,
                "validation_passed": False,
                "validation_stage": "init",
                "validation_errors": [
                    {
                        "file": "",
                        "severity": "error",
                        "summary": "Terraform init failed",
                        "detail": init_output,
                    }
                ],
                "validation_attempts": attempts + 1,
            }

        log_success("terraform init succeeded.")

        # -----------------------------
        # Terraform Validate
        # -----------------------------
        log_stage("terraform validate")

        validate_code, validate_output = await terraform_validate(workspace)

        passed, diagnostics = parse_validation_output(validate_output)

        # tf validate passed
        if passed and validate_code == 0:
            log_success("terraform validate succeeded.")

            validation_logger.save_summary(
                attempt=attempts + 1,
                stage="terraform_validate",
                passed=True,
            )

            return {
                "validation_run_id": validation_run_id,
                "validation_passed": True,
                "validation_stage": "validate",
                "validation_errors": [],
                "validation_attempts": attempts + 1,
            }

        log_failure("terraform validate failed.")

        validation_logger.save_command_output(
            command="terraform_validate",
            return_code=validate_code,
            output=validate_output,
        )

        validation_logger.save_validation_json(
            diagnostics,
        )

        validation_logger.save_summary(
            attempt=attempts + 1,
            stage="terraform_validate",
            passed=False,
        )

        return {
            "validation_run_id": validation_run_id,
            "validation_passed": False,
            "validation_stage": "validate",
            "validation_errors": diagnostics,
            "validation_attempts": attempts + 1,
        }

    finally:
        print("Clean workspace, but not doing for debugging")
        # cleanup_workspace(workspace)