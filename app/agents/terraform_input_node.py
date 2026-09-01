# app/agents/nodes/terraform_input_node.py

from langgraph.types import interrupt

from .state import AgentState
from .services.common_services import (
    build_terraform_input_request,
)
from .services.devops.factory import get_git_provider


async def terraform_input_node(
    state: AgentState,
) -> dict:

    print(
        "--- [Agent] Terraform Input Collection ---"
    )

    # --------------------------------------------------
    # Discover Terraform variables
    # --------------------------------------------------

    inputs = build_terraform_input_request(
        state["generated_code"]
    )

    if not inputs:

        return {
            "terraform_inputs": [],
            "terraform_inputs_status": {},
        }

    # --------------------------------------------------
    # INTERRUPT
    # --------------------------------------------------

    submitted = interrupt({
        "type": "terraform_inputs_required",
        "variables": inputs,
    })

    # --------------------------------------------------
    # Validate request
    # --------------------------------------------------

    if not isinstance(submitted, dict):
        raise ValueError(
            "Invalid Terraform input payload."
        )

    values = submitted.get("values")

    if not isinstance(values, dict):
        raise ValueError(
            "Terraform input payload must contain "
            "'values'."
        )

    expected_names = {
        item["name"]
        for item in inputs
    }

    provided_names = set(values.keys())

    unknown = provided_names - expected_names

    if unknown:
        raise ValueError(
            f"Unknown Terraform inputs: "
            f"{sorted(unknown)}"
        )

    # --------------------------------------------------
    # Validate required inputs
    # --------------------------------------------------

    for item in inputs:

        name = item["name"]

        if (
            item["required"]
            and name not in values
        ):
            raise ValueError(
                f"Required Terraform input "
                f"'{name}' was not provided."
            )

    # --------------------------------------------------
    # Provider
    # --------------------------------------------------

    repo_config = {
        **state["repo_config"],
        "thread_id": state["thread_id"],
    }

    provider = get_git_provider(
        repo_config
    )

    # --------------------------------------------------
    # Split GitHub secrets / variables
    # --------------------------------------------------

    secrets = {}
    variables = {}

    status = {}

    for item in inputs:

        name = item["name"]

        if name in values:

            value = values[name]

        elif item["has_default"]:

            value = item["default"]

        else:

            raise ValueError(
                f"Missing Terraform input: {name}"
            )

        # ----------------------------------------------
        # Secret
        # ----------------------------------------------

        if item["sensitive"]:

            secrets[name.upper()] = str(value)

            status[name] = "configured"

        # ----------------------------------------------
        # Variable
        # ----------------------------------------------

        else:

            variables[name.upper()] = str(value)

            status[name] = "configured"

    # --------------------------------------------------
    # Create GitHub secrets
    # --------------------------------------------------

    if secrets:

        await provider.set_repo_secrets(
            secrets
        )

    # --------------------------------------------------
    # Create GitHub variables
    # --------------------------------------------------

    if variables:

        await provider.set_repo_variables(
            variables
        )

    # --------------------------------------------------
    # Persist ONLY safe metadata
    # --------------------------------------------------

    safe_inputs = []

    for item in inputs:

        value = values.get(
            item["name"],
            item["default"],
        )

        safe_inputs.append({
            "name": item["name"],
            "type": item["type"],
            "description": item["description"],
            "required": item["required"],
            "has_default": item["has_default"],
            "sensitive": item["sensitive"],

            # Never persist sensitive value
            "value": (
                None
                if item["sensitive"]
                else value
            ),
        })

    return {
        "terraform_inputs": safe_inputs,
        "terraform_inputs_status": status,
    }
