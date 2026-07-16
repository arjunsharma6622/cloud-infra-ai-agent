from .state import AgentState

def validation_agent_node(state: AgentState) -> dict:
    print("--- [Agent] Validation Agent Working ---")
    attempts = state.get("validation_attempts", 0)

    # MOCK BEHAVIOR: We intentionally fail it on the first pass to test the LangGraph loop!
    if attempts == 0:
        print("--> Mocking a syntax error")

        return {
            "validation_passed": False,
            "validation_errors": "Error: Missing required argument 'name' in resource 'azurerm_resource_group'.",
            "validation_attempts": attempts+1
        }
    else:
        print("--> Mocking a successful validation...")
        return {
            "validation_passed": True,
            "validation_errors": "",
            "validation_attempts": attempts + 1
        }