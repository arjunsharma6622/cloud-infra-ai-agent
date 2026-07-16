from langgraph.graph import StateGraph, END
from .state import AgentState
from .parser import intent_parser_node
from .planner import architecture_planner_node
from .generator import iac_generator_node
from .validator import validation_agent_node

# 1. Initialize state graph
workflow = StateGraph(AgentState)

# 2. Add our agent nodes
workflow.add_node("intent_parser", intent_parser_node)
workflow.add_node("architecture_planner", architecture_planner_node)
workflow.add_node("iac_generator", iac_generator_node)
workflow.add_node("validation_agent", validation_agent_node)

# 3. Define the standard flow
workflow.set_entry_point("intent_parser")
workflow.add_edge("intent_parser", "architecture_planner")
workflow.add_edge("architecture_planner", "iac_generator")
workflow.add_edge("iac_generator", "validation_agent")

# def route_after_validation(state: AgentState):
#     if state["validation_attempts"] < 3:
#         print("--> Validation failed. Routing back to IaC Generator for remediation.")
#         return "iac_generator"
#     else: END
        
# workflow.add_conditional_edges(
#     "validation_agent",
#     route_after_validation
# )

# compiled_graph = workflow.compile()



# 4. Define the intelligent remediation loop
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

# FIX: Pass the explicit path dictionary mapping strings to graph nodes/END
workflow.add_conditional_edges(
    "validation_agent",
    route_after_validation,
    {
        "retry": "iac_generator",
        "end": END
    }
)

# 5. Compile the engine
compiled_graph = workflow.compile()