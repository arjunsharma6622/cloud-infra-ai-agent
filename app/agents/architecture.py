import os
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from .prompts import ARCHITECTURE_AGENT_SYSTEM_PROMPT
from app.llms import get_agent_llm
from app.config import AgentType
import json

def architecture_planner_node(state: AgentState) -> dict:
    print("--- [Agent] Architecture Planner Working ---")

    llm = get_agent_llm(AgentType.ARCHITECTURE)

    prompt = [
        SystemMessage(content=ARCHITECTURE_AGENT_SYSTEM_PROMPT),
        *state['messages'],
        HumanMessage(
            content=f"""Project Specification (Authoritative Source)

        ```json
        {json.dumps(state["project_spec"], indent=2)}
        ```
        """
        )
    ]

    response = llm.invoke(prompt)

    return {
        "architecture_plan": response.text() if hasattr(response, "text") else response.content
    }


