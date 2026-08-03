from .state import AgentState

def route_after_parser(state: AgentState):
    if state.get("clarification_question"):
        return "clarification"
    return "srs_generator"

def route_after_validation(state: AgentState) -> str:
    if state["validation_passed"]:
        print("--> Validation passed!")
        return "end"

    attempts = state.get("validation_attempts", 0)

    if attempts < 3:
        print(f"--> Validation failed (Attempt {attempts}). Retrying...")
        return "retry"

    print("--> Maximum validation attempts reached.")
    return "end"
