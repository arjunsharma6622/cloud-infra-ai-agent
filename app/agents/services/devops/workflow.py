
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
