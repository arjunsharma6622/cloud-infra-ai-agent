from typing import TypedDict, Dict, Any

class AgentState(TypedDict):
    user_prompt: str
    project_spec: Dict[str, Any]
    architecture_plan: str # TODO: think about this which format
    generated_code: Dict[str, str]

    validation_passed: bool
    validation_errors: str
    validation_attempts: int