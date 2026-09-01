import hcl2
from io import StringIO

def find_affected_units(
    diagnostics: list[dict],
    generation_units: list[dict],
) -> list[str]:

    affected_units = []

    for unit in generation_units:
        unit_name = unit["name"]
        unit_path = unit["path"].rstrip("/")

        for diagnostic in diagnostics:
            file_path = diagnostic.get("file", "").replace("\\", "/")

            if not file_path:
                continue

            if unit_path in ("", "."):
                is_match = "/" not in file_path
            else:
                is_match = (
                    file_path == unit_path
                    or file_path.startswith(unit_path + "/")
                )

            if is_match:
                affected_units.append(unit_name)
                break

    return affected_units

def generate_backend_tf(cloud_provider, thread_id):

    if cloud_provider.casefold() == "aws".casefold():
        return f"""
        terraform {{
        backend "s3" {{
            bucket       = "infra-ai-terraform-state-6622"
            key          = "projects/{thread_id}/terraform.tfstate"
            region       = "ap-south-1"
            use_lockfile = true
        }}
        }}
        """

#     if cloud_provider == "azure":
#         return f"""
# terraform {{
#   backend "azurerm" {{
#     storage_account_name = "infraaitfstate"
#     container_name       = "tfstate"
#     key                  = "projects/{thread_id}.tfstate"
#     use_azuread_auth     = true
#   }}
# }}
# """
    raise ValueError(
        f"Unsupported cloud provider: {cloud_provider}"
    )

def extract_terraform_inputs(generated_code: dict[str, str]) -> list[dict]:

    variables_tf = generated_code.get(
        "variables.tf"
    )   

    if not variables_tf:
        return []

    parsed = hcl2.load(
        StringIO(variables_tf)
    )

    result = []

    for variable_block in parsed.get(
        "variable",
        []
    ):
        for name, config in variable_block.items():

            default_exists = (
                "default" in config
            )

            result.append({
                "name": name,
                "type": config.get(
                    "type",
                    "string"
                ),
                "description": config.get(
                    "description",
                    ""
                ),
                "required": not default_exists,
                "sensitive": config.get(
                    "sensitive",
                    False,
                ),
                "default": config.get(
                    "default"
                )
            })

    return result
