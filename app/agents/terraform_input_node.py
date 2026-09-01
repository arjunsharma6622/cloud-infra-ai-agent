from langgraph.types import interrupt

from .state import AgentState
from .services.common_services import (
    extract_terraform_inputs
)

async def terraform_input_node(
    state: AgentState
) -> dict:

    print("--- [Agent] Terraform Input Discovery ---")

    terraform_inputs = extract_terraform_inputs(
        state["generated_code"]
    )

    requir