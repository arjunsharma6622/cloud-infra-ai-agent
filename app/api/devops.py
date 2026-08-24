import os
from fastapi import APIRouter, HTTPException

from app.schemas import GitHubPRTestRequest
from app.agents.services.devops.service import (
    create_infra_pr,
)
from app.agents.services.devops.repo_bootstrap import bootstrap_repo
from app.agents.services.devops.factory import get_git_provider
from app.schemas import GitHubConfigTestRequest

from uuid import uuid4

router = APIRouter(
    prefix="/devops",
    tags=["DevOps"],
)

@router.post("/github/bootstrap-repo")
async def bootstrap_github_repo():
    try:
        repo_config = {
            "provider": "github",
            "owner": "arjunsharma6622-temp1"
        }

        provider = get_git_provider(
            repo_config
        )

        bootstrap_result = await bootstrap_repo(
            provider=provider,
            repo_name=f"infra-proj-{str(uuid4())[:8]}",
            description="testing repo bootstrap creation using the api call",
            private=True
        )

        # TEMP: add repo secrets and vars
        # right now manually adding these from the env vars
        # later, we need to add these from our ui
        # also think about where to store in some valut and access from there (for enhanced security)
        await provider.set_repo_secrets(
            {
                "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
                "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY")
            }
        )

        await provider.set_repo_variables(
            {
                "AWS_REGION": os.getenv("AWS_REGION")
            }
        )

        return bootstrap_result
    except Exception as e:
        print(e)

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post("/github/test-pr")
async def test_github_pr(
    request: GitHubPRTestRequest,
):
    """
    Test GitHub branch creation, Terraform commit,
    and pull request creation.

    This bypasses LangGraph and directly tests
    the DevOps/GitHub integration.
    """

    generated_code = request.files

    if not generated_code:
        raise HTTPException(
            status_code=400,
            detail="No files provided.",
        )

    repo_config = {
        "provider": "github",
        "owner": request.owner,
        "repo": request.repository,
        "target_branch": request.target_branch,

        # Temporary test identifier.
        # The real DevOps node will use state["thread_id"].
        "thread_id": "manual-test",
    }

    try:

        result = await create_infra_pr(
            repo_config=repo_config,
            generated_code=generated_code,
        )

        return {
            "success": True,
            "message": "GitHub branch, commit and PR created successfully.",
            "branch": result["branch"],
            "commit_id": result["commit_id"],
            "pull_request_id": result["pull_request_id"],
            "pull_request_url": result["pull_request_url"],
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post("/github/test-secrets-vars")
async def test_github_config(
    request: GitHubConfigTestRequest,
):
    try:

        # ------------------------------------------
        # GitHub configuration
        # ------------------------------------------

        repo_config = {
            "provider": "github",
            "owner": "arjunsharma6622-temp1",
            "repo": request.repository,
        }

        # ------------------------------------------
        # Create provider
        # ------------------------------------------

        provider = get_git_provider(
            repo_config
        )

        # ------------------------------------------
        # Repository secret
        # ------------------------------------------

        await provider.set_repo_secret(
            name=request.repo_secret.name,
            value=request.repo_secret.value,
        )

        # ------------------------------------------
        # Repository variable
        # ------------------------------------------

        await provider.set_repo_variable(
            name=request.repo_variable.name,
            value=request.repo_variable.value,
        )

        # ------------------------------------------
        # Environment secret
        # ------------------------------------------

        await provider.set_environment_secret(
            environment_name=request.environment_name,
            name=request.environment_secret.name,
            value=request.environment_secret.value,
        )

        # ------------------------------------------
        # Environment variable
        # ------------------------------------------

        await provider.set_environment_variable(
            environment_name=request.environment_name,
            name=request.environment_variable.name,
            value=request.environment_variable.value,
        )

        # ------------------------------------------
        # Success
        # ------------------------------------------

        return {
            "status": "success",
            "repository": request.repository,
            "environment": request.environment_name,
            "configured": {
                "repo_secret": request.repo_secret.name,
                "repo_variable": request.repo_variable.name,
                "environment_secret": request.environment_secret.name,
                "environment_variable": request.environment_variable.name,
            },
        }

    except Exception as e:

        print(
            f"GitHub config test failed: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )