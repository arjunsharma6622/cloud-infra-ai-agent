import os
from pydantic import BaseModel, Field
from .state import AgentState
from app.llms import get_agent_structured_llm
from app.config import AgentType

class TerraformProject(BaseModel):
    # TODO: currently getting all in one file, but in reality we need modules directory str etc...
    main_tf: str = Field(description="The complete, production-ready HCL content for main.tf")
    variables_tf: str = Field(description="The HCL content for variables.tf")
    outputs_tf: str = Field(description="The HCL content for outputs.tf")

def iac_generator_node(state: AgentState) -> dict:
    print("--- [Agent] IaC Generator Working ---")

    structured_llm = get_agent_structured_llm(AgentType.ARCHITECTURE, TerraformProject)

    formatting_rules = """
    CRITICAL FORMATTING RULES:
    1. Do NOT compress or squash the code into a single line. 
    2. Write the code EXACTLY as it should look in a modern code editor like VS Code.
    3. Use standard 2-space indentations for all nested attributes inside code blocks.
    4. Provide clear newline breaks between different resource blocks, variable definitions, and outputs.
    """

    if state.get("validation_attempts", 0) > 0:
        prompt = f"""
        {formatting_rules}
        You previously generated Terraform code that threw a syntax error.
        Previous Code: {state['generated_code']}
        Compiler Error: {state['validation_errors']}
        Fix the errors and return the corrected code.
        """
    else:
        prompt = f"""
        {formatting_rules}
        Translate the following architecture plan into production-ready Azure Terraform code.
        Plan: {state['architecture_plan']}
        """
    
    result: TerraformProject = structured_llm.invoke(prompt)

    code_files = {
        "main.tf": result.main_tf,
        "variables.tf": result.variables_tf,
        "outputs.tf": result.outputs_tf
    }

    return {"generated_code": code_files}

