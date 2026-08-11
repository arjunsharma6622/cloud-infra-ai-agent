from .state import AgentState
from .services.terraform_generator import generate_terraform
from .services.get_tf_docs import get_terraform_docs


def get_dependency_context(
    current_unit: dict,
    generated_units: dict,
) -> dict:
    """
    Get the latest generated context for units that the current
    generation unit depends on.
    """

    dependency_context = {}

    for dependency_name in current_unit.get("depends_on", []):
        dependency = generated_units.get(dependency_name)

        if dependency:
            dependency_context[dependency_name] = dependency

    return dependency_context


def iac_generator_node(state: AgentState) -> dict:
    print("--- [Agent] IaC Generator Working ---")

    project_plan = state["project_plan"]

    generation_units = project_plan["generation_units"]

    generation_mode = state.get("generation_mode", "initial")

    if generation_mode == "initial":
        index = state.get("generation_unit_index", 0)

        current_unit = generation_units[index]

    else:
        repair_index = state.get("current_repair_index", 0)

        units_to_regenerate = state.get("units_to_regenerate", [])

        unit_name = units_to_regenerate[repair_index]

        current_unit = next(
            unit
            for unit in generation_units
            if unit["name"] == unit_name
        )

    # -------------------------------------------------------
    # Determine current generation unit
    # -------------------------------------------------------

    unit_name = current_unit["name"]

    print(f"Generating unit: {unit_name}")

    # -------------------------------------------------------
    # Get Terraform docs ONLY for this unit
    # -------------------------------------------------------

    terraform_docs = get_terraform_docs(
        cloud_provider=state["cloud_provider"],
        terraform_types=current_unit["terraform_resources"],
    )

    # -------------------------------------------------------
    # Get latest dependency context
    # -------------------------------------------------------

    generated_units = state.get("generated_units", {})

    dependency_context = get_dependency_context(
        current_unit=current_unit,
        generated_units=generated_units,
    )

    # -------------------------------------------------------
    # Previous code for this unit
    #
    # During initial generation this will normally be None.
    # During repair, it contains the latest version of this unit.
    # -------------------------------------------------------

    previous_code = generated_units.get(unit_name)

    # -------------------------------------------------------
    # Generate current unit
    # -------------------------------------------------------

    generation_result = generate_terraform(
        architecture_plan=state["architecture_plan"],
        generation_unit=current_unit,
        terraform_docs=terraform_docs,
        dependency_context=dependency_context,
        generation_mode=state.get("generation_mode", "initial"),
        validation_stage=state.get("validation_stage"),
        validation_errors=state.get("validation_errors"),
        previous_code=previous_code,
    )

    generated_code = generation_result["generated_code"]

    # -------------------------------------------------------
    # Save latest version of this unit
    # -------------------------------------------------------

    updated_generated_units = {
        **generated_units,
        unit_name: generated_code,
    }

    if generation_mode == "initial":

        return {
            "current_generation_unit": current_unit,

            "terraform_docs": terraform_docs,

            "generated_units": updated_generated_units,

            "generation_prompt": generation_result["generation_prompt"],

            # Move to next unit
            "generation_unit_index": index + 1,
        }

    else:
        return {
            "current_generation_unit": current_unit,

            "terraform_docs": terraform_docs,

            "generated_units": updated_generated_units,

            "generation_prompt": generation_result["generation_prompt"],

            # Move to next unit
            "current_repair_index": repair_index + 1,
        }
