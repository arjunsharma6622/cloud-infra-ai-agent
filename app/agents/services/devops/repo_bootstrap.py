import os

from .workflow import (
    generate_terraform_workflow,
)

from .base import GitProvider


async def bootstrap_repo(
    provider: GitProvider,
    repo_name: str,
    description: str,
    cloud_provider: str,
    private: bool = True,
) -> dict:

    # --------------------------------------------------
    # Create repository
    # --------------------------------------------------

    repo = await provider.create_repo(
        repo_name=repo_name,
        description=description,
        private=private,
    )

    main_branch = repo["default_branch"]

    # --------------------------------------------------
    # Add AWS credentials / variables
    # --------------------------------------------------

    await provider.set_repo_secrets(
        {
            "AWS_ACCESS_KEY_ID": os.getenv(
                "AWS_ACCESS_KEY_ID"
            ),
            "AWS_SECRET_ACCESS_KEY": os.getenv(
                "AWS_SECRET_ACCESS_KEY"
            ),
        }
    )

    await provider.set_repo_variables(
        {
            "AWS_REGION": os.getenv(
                "AWS_REGION"
            ),
        }
    )

    # --------------------------------------------------
    # Add default workflow
    # --------------------------------------------------

    workflow = generate_terraform_workflow(
        cloud_provider=cloud_provider,
        terraform_inputs=[],
    )

    workflow_files = {
        ".github/workflows/terraform.yml": workflow
    }

    workflow_commit = await provider.commit_files(
        branch_name=main_branch,
        files=workflow_files,
        commit_message=(
            "ci: add Terraform deployment workflow"
        ),
    )

    # --------------------------------------------------
    # Get latest main SHA
    # --------------------------------------------------

    main_sha = await provider.get_branch_sha(
        main_branch
    )

    # --------------------------------------------------
    # Create dev branch
    # --------------------------------------------------

    await provider.create_branch(
        branch_name="dev",
        base_sha=main_sha,
    )

    return {
        "repo_name": repo["name"],
        "repo_full_name": repo["full_name"],
        "repo_url": repo["url"],
        "main_branch": main_branch,
        "dev_branch": "dev",
        "workflow_path": (
            ".github/workflows/terraform.yml"
        ),
        "workflow_commit_id": workflow_commit,
    }
