import os
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import AgentState
from typing import List

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

def intent_parser_node(state: AgentState) -> dict:
    print("--- [Agent] Intent Parser Working ---")

    llm = ChatGoogleGenerativeAI(model=os.getenv("PARSER_MODEL_NAME", "gemini-2.5-flash"))
    structured_llm = llm.with_structured_output(ProjectSpec)

    prompt = f"""
    You are an expert Cloud Infrastructure Architect. 
    Extract the infrastructure requirements from the user request into a detailed, structured format.
    Ensure every resource has a captured 'reasoning'. If needed to add more info add them to additional_info.
    If critical information (like Cloud Provider or Region) is missing, list the questions in 'missing_critical_requirements'.

    User Request: {state['messages']}
    """

    result = structured_llm.invoke(prompt)
    return {"project_spec": result.model_dump()}