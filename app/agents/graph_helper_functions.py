from .state import AgentState
from app.config import VALIDATION_MAX_RETRIES

def route_after_parser(state: AgentState):
    if state.get("clarification_question"):
        return "clarification"
    return "srs_generator"

def route_after_validation(state: AgentState) -> str:
    if state.get("validation_passed", False):
        return "repo_bootstrap"

    attempts = state.get("validation_attempts", 0)

    if attempts >= VALIDATION_MAX_RETRIES:
        print(f"--> Validation failed (Attempt {attempts}). Retrying...")
        return "end"

    if not state.get("units_to_regenerate"):
        print("--> Validation failed but no affected units found.")
        return "blocked"

    print(f"--> Validation filed (Attempt {attempts}). "
          "Starting repair cycle..."
    )

    return "retry"


def route_after_generation(state: AgentState) -> str:
    mode = state.get("generation_mode", "initial")


    # Initial mode (loop unitl all generation units are genrated initially)
    if mode == "initial":
        generation_units = state["project_plan"]["generation_units"]
        current_index = state.get("generation_unit_index", 0)

        if current_index < len(generation_units):
            return "next_unit"


    # Repair mode (loop unitl all the regeneration units are generated)
    units_to_regenerate = state.get("units_to_regenerate", [])

    repair_index = state.get("current_repair_index", 0)

    if repair_index < len(units_to_regenerate):
        return "next_unit"

    return "validation"
