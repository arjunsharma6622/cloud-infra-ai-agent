import os
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import AgentState

class ProjectSpec(BaseModel):
    cloud_provider: str
    resources: list[str]
    region: str
    networking: str

def intent_parser_node(state: AgentState) -> dict:
    print("--- [Agent] Intent Parser Working ---")

    llm = ChatGoogleGenerativeAI(model=os.getenv("PARSER_MODEL_NAME", "gemini-2.5-flash"))
    structured_llm = llm.with_structured_output(ProjectSpec)

    prompt = f"""
    Extract the infrastructure requirements from the following user request.
    Request: {state['user_prompt']}
    """

    result = structured_llm.invoke(prompt)
    return {"project_spec": result.model_dump()}