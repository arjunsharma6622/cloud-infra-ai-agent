import os
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState
from .prompts import ARCHITECTURE_AGENT_SYSTEM_PROMPT
from app.llms import get_agent_structured_llm
from app.config import AgentType
import json
from .schemas.architecture_node import ArchitecturePlan
from pydantic import BaseModel

class ArchitectureResult(BaseModel):
    architecture_plan: ArchitecturePlan

def architecture_planner_node(state: AgentState) -> dict:
    print("--- [Agent] Architecture Planner Working ---")

    structured_llm = get_agent_structured_llm(
        AgentType.ARCHITECTURE,
        ArchitectureResult
    )

    project_spec = state["project_spec"]

    prompt = [
        SystemMessage(content=ARCHITECTURE_AGENT_SYSTEM_PROMPT),
        *state['messages'],
        HumanMessage(
            content=f"""
        PROJECT SPECIFICATION
        =====================

        The following Project Specification is the authoritative source of
        requirements.

        Do not omit any requirement.

        ```json
        {json.dumps(project_spec, indent=2)}
        ```
        Design the complete cloud architecture from this specification.

        """
        )
    ]

    result: ArchitectureResult = structured_llm.invoke(prompt)

    print(result.architecture_plan.cloud_provider)
    print(result.architecture_plan.terraform_resources)

    return {
        "architecture_plan": result.architecture_plan.architecture_markdown,
        "cloud_provider": result.architecture_plan.cloud_provider,
        "terraform_resources": result.architecture_plan.terraform_resources
    }

