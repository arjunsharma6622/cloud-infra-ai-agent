import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from .state import AgentState

def architecture_planner_node(state: AgentState) -> dict:
    print("--- [Agent] Architecture Planner Working ---")

    llm = ChatGoogleGenerativeAI(model=os.getenv("PLANNER_MODEL_NAME", "gemini-2.5-flash"))

    sys_msg = SystemMessage(content="""
    You are a Principal Cloud Architect. Based on the provided JSON specification, 
    design a logical deployment plan. Output a detailed Markdown document outlining 
    the resources to be created and their explicit dependency order (e.g., Network -> Subnets -> Compute).
    """)
    human_msg = HumanMessage(content=f"Specification: {state['project_spec']}")

    # TODO: think if we should pass in the entire state for the sake of more context, so let the prev agent do its job perfectly

    result = llm.invoke([sys_msg, human_msg])

    return {"architecture_plan": result.content}
