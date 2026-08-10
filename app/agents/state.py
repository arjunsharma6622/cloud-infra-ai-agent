from typing import TypedDict, Dict, Any, Annotated, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    thread_id: str
    
    messages: Annotated[list, add_messages]

    clarification_question: Optional[str]

    project_spec: Dict[str, Any]

    srs_document: str

    architecture_plan: str

    cloud_provider: str

    terraform_resources: list[str]

    project_plan: Dict[str, Any]

    terraform_docs: Dict[str, any]
    
    generated_code: Dict[str, str]
    generation_prompt: str

    validation_run_id: str

    validation_stage: str
    validation_passed: bool
    validation_errors: list[dict[str, str]]
    validation_attempts: int