from langgraph.types import interrupt
from langchain_core.messages import AIMessage, HumanMessage
from .state import AgentState


def clarification_node(state: AgentState):
    question = state["clarification_question"]

    answer = interrupt(question)

    return {
        "messages": [
            AIMessage(content=question),
            HumanMessage(content=answer),
        ],
        "clarification_question": None,
    }
