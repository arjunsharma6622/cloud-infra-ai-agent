from .state import AgentState

from app.tf_validation.workspace import (
    create_workspace,
    write_files,
    cleanup_workspace,
)

from app.tf_validation.runner import (
    terraform_init,
    terraform_validate,
)

from app.tf_validation.parser import (
    parse_validation_output,
)


async def validation_agent_node(state: AgentState) -> dict:
    print("--- [Agent] Validation Agent Working ---")

    attempts = state.get("validation_attempts", 0)
    generated_code = state["generated_code"]

    if not generated_code:
        return {
            "validation_passed": False,
            "validation_stage": "generator",
            "validation_errors": [{
                "summary": "Generator produced no Terraform files."
            }],
            "validation_attempts": attempts + 1,
        }

    workspace = create_workspace()

    try:
        # Write generated Terraform files
        write_files(workspace, generated_code)

        # -----------------------------
        # Terraform Init
        # -----------------------------
        init_code, init_output = await terraform_init(workspace)

        print(init_output)

        if init_code != 0:
            return {
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

        # -----------------------------
        # Terraform Validate
        # -----------------------------
        validate_code, validate_output = await terraform_validate(workspace)

        passed, diagnostics = parse_validation_output(validate_output)

        # error_messages = [
        #     f"[{d['file']}] {d['summary']}: {d['detail']}"
        #     for d in diagnostics
        # ]

        return {
            "validation_passed": passed and validate_code == 0,
            "validation_stage": "validate",
            "validation_errors": diagnostics,
            "validation_attempts": attempts + 1,
        }

    finally:
        # TEMP
        print("Clean workspace, but not doing for debugging")
    #     cleanup_workspace(workspace)