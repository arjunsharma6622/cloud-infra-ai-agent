from .workflow import get_terraform_workflow
from .base import GitProvider

async def bootstrap_repo(
    provider: GitProvider,
    repo_name: str,
    description: str,
    private: bool = True,
) -> dict:
    # create repo

    repo = await provider.create_repo(
        repo_name=repo_name,
        description=description,
        private=private,
    )

    main_branch = repo["default_branch"]

        # add github actions workflow

    workflow = get_terraform_workflow()

    workflow_files = {
        ".github/workflows/terraform.yml": workflow
    }

    # commit workflow to dev

    workflow_commit = await provider.commit_files(
        branch_name=main_branch,
        files=workflow_files,
        commit_message="ci: add Terraform deployment workflow",
    )

    # get main HEAD

    main_sha = await provider.get_branch_sha(
        main_branch
    )

    # create dev branch

    await provider.create_branch(
        branch_name="dev",
        base_sha=main_sha
    )

    # return repo info
    return {
        "repo_name": repo["name"],
        "repo_full_name": repo["full_name"],
        "repo_url": repo["url"],
        "main_branch": main_branch,
        "dev_branch": "dev",
        "workflow_path": ".github/workflows/terraform.yml",
        "workflow_commit_id": workflow_commit,
    }
