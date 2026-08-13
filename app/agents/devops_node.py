from .state import AgentState
from .services.devops.service import (
    create_infra_pr,
)


async def devops_node(
    state: AgentState,
) -> dict:

    print(
        "--- [Agent] DevOps / GitHub Working ---"
    )

    generated_code = state["generated_code"]

    repository_config = {
        **state["repository_config"],
        "thread_id": state["thread_id"],
    }

    result = await create_infra_pr(
        repository_config=repository_config,
        generated_code=generated_code,
    )

    return {
        "git_branch": result["branch"],
        "git_commit_id": result["commit_id"],
        "pull_request_url": result["pull_request_url"],
        "pull_request_id": result["pull_request_id"],
        "deployment_status": "pr_created",
    }
