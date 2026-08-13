from fastapi import APIRouter, HTTPException

from app.schemas import GitHubPRTestRequest
from app.agents.services.devops.service import (
    create_infra_pr,
)

router = APIRouter(
    prefix="/devops",
    tags=["DevOps"],
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

    repository_config = {
        "provider": "github",
        "owner": request.owner,
        "repository": request.repository,
        "target_branch": request.target_branch,

        # Temporary test identifier.
        # The real DevOps node will use state["thread_id"].
        "thread_id": "manual-test",
    }

    try:

        result = await create_infra_pr(
            repository_config=repository_config,
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

    