def get_terraform_workflow() -> str:

    return """
name: Terraform Deployment

on:
  workflow_dispatch:

permissions:
  contents: read

jobs:

  terraform:
    name: Terraform Deployment
    runs-on: ubuntu-latest

    environment:
      name: dev-approval

    steps:

      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3

      - name: Terraform Init
        run: terraform init

      - name: Terraform Validate
        run: terraform validate

      - name: Terraform Plan
        run: terraform plan
"""
