from typing import TypedDict, Dict, Any, Annotated, Optional
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    thread_id: str

    messages: Annotated[list, add_messages]

    clarification_question: Optional[str]

    # Requirements
    project_spec: Dict[str, Any]
    srs_document: str

    # Architecture
    architecture_plan: str
    cloud_provider: str
    terraform_resources: list[str]

    # Project planning
    project_plan: Dict[str, Any]

    # Generation
    current_generation_unit: dict | None
    generation_unit_index: int

    # Latest generated code for each unit
    generated_units: Dict[str, Dict[str, str]]

    # Combined/final Terraform project
    generated_code: Dict[str, str]

    # Prompt used for the current generation
    generation_prompt: str

    generation_mode: str

    # Validation / repair
    units_to_regenerate: list[str]

    current_repair_index: int

    validation_run_id: str
    validation_stage: str
    validation_passed: bool
    validation_errors: list[dict[str, str]]
    validation_attempts: int

    isCompliant:bool
    guardrailMessage:str
