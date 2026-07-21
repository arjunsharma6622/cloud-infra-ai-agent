from typing import TypedDict, Dict, Any, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

    project_spec: Dict[str, Any]

    srs_document: str

    architecture_plan: str # TODO: think about this which format
    
    generated_code: Dict[str, str]

    validation_passed: bool
    validation_errors: str
    validation_attempts: int