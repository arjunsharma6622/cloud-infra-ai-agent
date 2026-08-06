from .state import AgentState
from app.config import VALIDATION_MAX_RETRIES

def route_after_parser(state: AgentState):
    if state.get("clarification_question"):
        return "clarification"
    return "srs_generator"

def route_after_validation(state: AgentState) -> str:
    if state.get("validation_passed", False):
        print("--> Validation passed!")
        return "end"

    attempts = state.get("validation_attempts", 0)

    if attempts < VALIDATION_MAX_RETRIES:
        print(f"--> Validation failed (Attempt {attempts}). Retrying...")
        return "retry"

    print("--> Maximum validation attempts reached.")
    return "end"
