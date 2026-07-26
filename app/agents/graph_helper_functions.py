from .state import AgentState

def route_after_parser(state: AgentState):
    if state.get("clarification_question"):
        return "clarification"
    return "srs_generator"

def route_after_validation(state: AgentState) -> str:
    # Explicitly check the boolean state
    if state.get("validation_passed") is True:
        print("--> Validation passed! Finalizing execution.")
        return "end"
    
    # If it failed, send it back to code generator up to 3 times
    attempts = state.get("validation_attempts", 0)
    if attempts < 3:
        print(f"--> Validation failed (Attempt {attempts}). Routing back to IaC Generator.")
        return "retry"
    
    print("--> Max validation attempts reached. Exiting graph.")
    return "end"

