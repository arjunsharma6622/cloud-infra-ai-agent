import os
from pydantic import BaseModel, Field
from .state import AgentState
from typing import List, Optional
from langchain_core.messages import SystemMessage
from .prompts import INTENT_PARSER_SYSTEM_PROMPT
from app.config import AgentType
from app.llms import get_agent_structured_llm

class CloudResource(BaseModel):
    name: str = Field(description="Logical name of the resource")
    resource_type: str = Field(description="Specific cloud service (e.g., Azure SQL, EC2)")
    specifications: str = Field(description="Size, tier, version, or OS details")
    reasoning: str = Field(description="Why this resource is needed based on user intent")

class NetworkSpec(BaseModel):
    topology: str = Field(description="e.g., Hub and Spoke, Single VNet/VPC")
    subnets: List[str] = Field(description="e.g., Public Web Subnet, Private DB Subnet")
    security_rules: List[str] = Field(description="High-level access rules (e.g., Block all inbound, Allow SSH)")

class ProjectSpec(BaseModel):
    cloud_provider: str = Field(description="AWS, Azure, GCP, etc.")
    region: str = Field(description="Target deployment region")
    networking: NetworkSpec
    compute: List[CloudResource]
    databases: List[CloudResource]
    storage: List[CloudResource]
    additional_info: List[str] = Field(
        description="Any extra preferences, constraints, or 'special requests' (like restaurant notes) provided by the user."
    )
    missing_critical_requirements: List[str] = Field(
        description="If the user prompt lacks critical info (like region or provider), list the questions to ask them back. Leave empty if sufficient."
    )

class IntentParserResult(BaseModel):
    needs_clarification: bool = Field(
        description="True if more information is required before generating a project specification."
    )

    clarification_questions: List[str] = Field(
        default_factory=list,
        description="Questions to ask the user if clarification is needed."
    )

    project_spec: Optional[ProjectSpec] = Field(
        default=None,
        description="Complete project specification. Null if clarification is required."
    )

def intent_parser_node(state: AgentState) -> dict:
    print("--- [Agent] Intent Parser Working ---")

    structured_llm = get_agent_structured_llm(AgentType.PARSER, IntentParserResult)

    prompt_with_messages = [
        SystemMessage(content=INTENT_PARSER_SYSTEM_PROMPT),
        *state.get("messages", []),
    ]

    result: IntentParserResult = structured_llm.invoke(prompt_with_messages)

    if result.needs_clarification:
        return {
            "clarification_question": "\n".join(result.clarification_questions),
            "project_spec": None,
        }

    return {
        "project_spec": result.project_spec.model_dump(),
        "clarification_question": None,
    }
