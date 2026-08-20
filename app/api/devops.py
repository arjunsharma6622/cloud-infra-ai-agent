from fastapi import APIRouter, HTTPException

from app.schemas import GitHubPRTestRequest
from app.agents.services.devops.service import (
    create_infra_pr,
)
from app.agents.services.devops.repo_bootstrap import bootstrap_repo
from app.agents.services.devops.factory import get_git_provider


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
            "owner": "arjunsharma6622"
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

    