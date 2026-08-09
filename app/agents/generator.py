from .state import AgentState
from .services.terraform_generator import generate_terraform


def iac_generator_node(state: AgentState) -> dict:
    print("--- [Agent] IaC Generator Working ---")

    generation_result = generate_terraform(
        architecture_plan=state["architecture_plan"],
        validation_attempts=state.get("validation_attempts", 0),
        validation_stage=state.get("validation_stage"),
        validation_errors=state.get("validation_errors"),
        previous_code=state.get("generated_code"),
    )

    return {
        "generated_code": generation_result["generated_code"],
        "generation_prompt": generation_result["generation_prompt"]
    }
