from typing import TypedDict, Dict, Any,Literal

class AgentState(TypedDict):
    user_prompt: str
    project_spec: Dict[str, Any]
    architecture_plan: str # TODO: think about this which format
    generated_code: Dict[str, str]

    validation_passed: bool
    validation_errors: str
    validation_attempts: int

    #Security Guardrails

    security_status: Literal["blocked","passed"]
    security_message: str
    security_reason: str