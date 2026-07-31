from pydantic import BaseModel, Field
from .state import AgentState
from app.llms import get_agent_structured_llm
from .prompts import SECURITY_SYSTEM_PROMPT
from langchain_core.messages import SystemMessage
from app.config import AgentType
class Security_Node(BaseModel):
    is_safe:bool
    reason:str
def security_node(state: AgentState):
    print("--- [Agent] Security Planner Working ---")

    structured_llm = get_agent_structured_llm(
        AgentType.SECURITY,
        Security_Node
    )

    prompt = [
        SystemMessage(content=SECURITY_SYSTEM_PROMPT),
        *state.get("messages", []),
    ]

    result: Security_Node = structured_llm.invoke(prompt)
    print("is_safe:", result.is_safe)
    print("reason:", result.reason)
    return {
        "security_passed": result.is_safe,
        "security_reason": result.reason,
    }