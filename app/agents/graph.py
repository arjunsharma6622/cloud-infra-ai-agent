from langgraph.graph import StateGraph, END
from .state import AgentState
from .parser import intent_parser_node
from .srs import srs_node
from .architecture import architecture_planner_node
from .generator import iac_generator_node
from .validator import validation_agent_node
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from .clarification import clarification_node
from .graph_helper_functions import route_after_parser, route_after_validation,route_after_security
from .security_node import security_node
workflow = StateGraph(AgentState)

#security
workflow.add_node("security", security_node)
workflow.add_node("intent_parser", intent_parser_node)
workflow.add_node("srs_generator", srs_node)
workflow.add_node("architecture_planner", architecture_planner_node)
workflow.add_node("iac_generator", iac_generator_node)
workflow.add_node("validation_agent", validation_agent_node)
workflow.add_node("clarification", clarification_node)

workflow.set_entry_point("security")

workflow.add_conditional_edges(
    "security",
    route_after_security,
    {
        "intent_parser": "intent_parser",
        "end": END,
    },
)
workflow.add_edge("clarification", "intent_parser")

workflow.add_conditional_edges(
    "intent_parser",
    route_after_parser,
    {
        "clarification": "clarification",
        "srs_generator": "srs_generator",
    },
)

workflow.add_edge("srs_generator", "architecture_planner")

workflow.add_edge("architecture_planner", "iac_generator")

workflow.add_edge("iac_generator", "validation_agent")

workflow.add_conditional_edges(
    "validation_agent",
    route_after_validation,
    {
        "retry": "iac_generator",
        "end": END
    }
)


db_path = "checkpoints.sqlite"
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)

compiled_graph = workflow.compile(checkpointer=memory)
