from .state import AgentState

from .services.devops.factory import (
    get_git_provider,
)

from .services.devops.repo_bootstrap import (
    bootstrap_repo,
)


async def repo_bootstrap_node(
    state: AgentState,
) -> dict:

    print(
        "--- [Agent] Repository Bootstrap ---"
    )

    repo_config = {
        **state["repo_config"],
        "thread_id": state["thread_id"],
    }

    provider = get_git_provider(
        repo_config
    )

    thread_id = state["thread_id"]

    repo_name = (
        f"infra-proj-{thread_id[:8]}"
    )

    repo_result = await bootstrap_repo(
        provider=provider,
        repo_name=repo_name,
        description=(
            "Infra proj generated "
            "by Infra AI agent."
        ),
        cloud_provider=state["cloud_provider"],
        private=True,
    )

    repo_config.update({
        "repo": repo_result["repo_name"],
        "target_branch": "dev",
    })

    return {
        "repo_config": repo_config,
        "repo_url": repo_result["repo_url"],
        "deployment_status": "repo_bootstrapped",
    }
