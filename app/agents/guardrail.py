from pydantic import BaseModel, Field
from .state import AgentState
from app.llms import get_agent_structured_llm
from .prompts import GUARDRAIL_SYSTEM_PROMPT
from langchain_core.messages import SystemMessage
from app.config import AgentType
class Guardrail_Result(BaseModel):
    isCompliant:bool
    guardrailMessage:str
def guardrail_node(state: AgentState):
    print("--- [Agent] Guardrail Node Working ---")

    structured_llm = get_agent_structured_llm(
        AgentType.GUARDRAIL,
        Guardrail_Result
    )
    latest_message=state["messages"][-1]
    prompt = [
        SystemMessage(content=GUARDRAIL_SYSTEM_PROMPT),
        latest_message
    ]

    result: Guardrail_Result = structured_llm.invoke(prompt)
    print("isComplaint:", result.isCompliant)
    print("guardrailMessage:", result.guardrailMessage)
    return {
        "isCompliant": result.isCompliant,
        "guardrailMessage": result.guardrailMessage,
    }