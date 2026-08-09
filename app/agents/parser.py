import os

from langchain_core.messages import SystemMessage

from .state import AgentState
from .prompts import INTENT_PARSER_SYSTEM_PROMPT
from app.config import AgentType
from app.llms import get_agent_structured_llm

from .schemas.parser_node import IntentParserResult


def intent_parser_node(state: AgentState) -> dict:

    print("--- [Agent] Intent Parser Working ---")

    structured_llm = get_agent_structured_llm(
        AgentType.PARSER,
        IntentParserResult
    )

    prompt = [
        SystemMessage(content=INTENT_PARSER_SYSTEM_PROMPT),
        *state.get("messages", []),
    ]

    result: IntentParserResult = structured_llm.invoke(prompt)

    if result.needs_clarification:
        return {
            "clarification_question": "\n".join(result.clarification_questions),
            "project_spec": None,
        }

    return {
        "project_spec": result.project_spec.model_dump(),
        "clarification_question": None,
    }
