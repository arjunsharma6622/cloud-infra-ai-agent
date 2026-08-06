import os
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from .prompts import ARCHITECTURE_AGENT_SYSTEM_PROMPT
from app.llms import get_agent_structured_llm
from app.config import AgentType
import json
from app.schemas import ArchitecturePlan
from pydantic import BaseModel

class ArchitectureResult(BaseModel):
    architecture_plan: ArchitecturePlan

def architecture_planner_node(state: AgentState) -> dict:
    print("--- [Agent] Architecture Planner Working ---")

    structured_llm = get_agent_structured_llm(
        AgentType.ARCHITECTURE,
        ArchitectureResult
    )

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

    result: ArchitectureResult = structured_llm.invoke(prompt)

    return {
        "architecture_plan": result.architecture_plan
    }


