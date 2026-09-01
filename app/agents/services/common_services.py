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
        return f"""terraform {{
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

def extract_terraform_inputs(
    generated_code: dict[str, str],
) -> list[dict]:

    variables_tf = generated_code.get("variables.tf")

    if not variables_tf:
        return []

    parsed = hcl2.load(
        StringIO(variables_tf)
    )

    inputs = []

    for variable_block in parsed.get("variable", []):

        for name, config in variable_block.items():

            name = name.strip().strip('"').strip("'")

            has_default = "default" in config

            inputs.append({
                "name": name,
                "type": config.get(
                    "type",
                    "string",
                ),
                "description": config.get(
                    "description",
                    "",
                ),
                "required": not has_default,
                "has_default": has_default,
                "default": (
                    None
                    if config.get("sensitive", False)
                    else config.get("default")
                ),
                "sensitive": config.get(
                    "sensitive",
                    False,
                ),
            })

    return inputs

def build_terraform_input_request(
    generated_code: dict[str, str],
) -> list[dict]:

    inputs = extract_terraform_inputs(
        generated_code
    )

    result = []

    for item in inputs:

        result.append({
            "name": item["name"],
            "type": item["type"],
            "description": item["description"],
            "required": item["required"],
            "has_default": item["has_default"],
            "default": item["default"],
            "sensitive": item["sensitive"],
            "value": (
                None
                if item["sensitive"]
                else item["default"]
            ),
        })

    return result


def build_configured_terraform_inputs(
    inputs: list[dict],
    values: dict,
) -> list[dict]:

    configured = []

    for item in inputs:

        name = item["name"]

        if name not in values:

            continue

        value = values[name]

        has_default = item["has_default"]

        default = item["default"]

        # Required input always needs external config.
        needs_external_value = not has_default

        # Defaulted input only needs GitHub config
        # if user changed the default.
        if has_default:

            needs_external_value = (
                value != default
            )

        if needs_external_value:

            configured.append({
                **item,
                "value": value,
            })

    return configured



def generate_terraform_workflow(
    cloud_provider: str,
    terraform_inputs: list[dict],
) -> str:

    if cloud_provider != "aws":
        raise ValueError(
            f"Unsupported cloud provider: "
            f"{cloud_provider}"
        )

    env_lines = []

    for item in terraform_inputs:

        name = item["name"].upper()

        if item["sensitive"]:

            env_lines.append(
                f"          TF_VAR_{item['name']}: "
                f"${{{{ secrets.{name} }}}}"
            )

        else:

            env_lines.append(
                f"          TF_VAR_{item['name']}: "
                f"${{{{ vars.{name} }}}}"
            )

    terraform_env = "\n".join(env_lines)

    return f"""name: Terraform Deployment

on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  terraform:
    name: Terraform Deployment
    runs-on: ubuntu-latest
    env:
{terraform_env}

    steps:

      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{{{ secrets.AWS_ACCESS_KEY_ID }}}}
          aws-secret-access-key: ${{{{ secrets.AWS_SECRET_ACCESS_KEY }}}}
          aws-region: ${{{{ vars.AWS_REGION }}}}

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3

      - name: Terraform Init
        run: terraform init

      - name: Terraform Validate
        run: terraform validate

      - name: Terraform Plan
        run: terraform plan

      - name: Terraform Apply
        run: terraform apply -auto-approve
"""
