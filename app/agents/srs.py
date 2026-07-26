import json

from langchain_core.messages import HumanMessage, SystemMessage

from .state import AgentState
from .prompts import SRS_AGENT_SYSTEM_PROMPT
from app.llms import get_agent_llm
from app.config import AgentType


def srs_node(state: AgentState) -> dict:
    print("--- [Agent] SRS Generator Working ---")

    llm = get_agent_llm(AgentType.SRS)

    final_prompt = [
        SystemMessage(content=SRS_AGENT_SYSTEM_PROMPT),
        *state.get("messages", []),
        HumanMessage(
            content=(
                "Project Specification (Authoritative Source)\n\n"
                "Use this structured specification as the source of truth when "
                "generating the SRS.\n\n"
                f"```json\n{json.dumps(state['project_spec'], indent=2)}\n```"
            )
        ),
    ]

    response = llm.invoke(final_prompt)

    return {
        "srs_document": response.text() if hasattr(response, "text") else response.content
    }
