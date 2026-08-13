from langgraph.graph import StateGraph, END
from .state import AgentState
from .parser import intent_parser_node
from .srs import srs_node
from .architecture import architecture_planner_node
from .project_planner import project_planner_node
from .generator import iac_generator_node
from .validator import validation_agent_node
from .clarification import clarification_node
from .graph_helper_functions import (
    route_after_parser, 
    route_after_validation, 
    route_after_generation
)
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

workflow = StateGraph(AgentState)

workflow.add_node("intent_parser", intent_parser_node)
workflow.add_node("srs_generator", srs_node)
workflow.add_node("architecture_planner", architecture_planner_node)
workflow.add_node("project_planner", project_planner_node)
workflow.add_node("iac_generator", iac_generator_node)
workflow.add_node("validation_agent", validation_agent_node)
workflow.add_node("clarification", clarification_node)

workflow.set_entry_point("intent_parser")

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

workflow.add_edge(
    "architecture_planner",
    "project_planner",
)

workflow.add_edge(
    "project_planner",
    "iac_generator",
)

workflow.add_conditional_edges(
    "iac_generator",
    route_after_generation,
    {
        "next_unit": "iac_generator",
        "validation": "validation_agent",
    },
)

workflow.add_conditional_edges(
    "validation_agent",
    route_after_validation,
    {
        "retry": "iac_generator",
        "end": END,
        "blocked": END,
    }
)

async def create_graph():
    conn = await aiosqlite.connect("checkpoints.sqlite")

    memory = AsyncSqliteSaver(conn)

    return workflow.compile(checkpointer=memory)
