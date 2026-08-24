import os
from .state import AgentState
from .services.devops.service import (
    create_infra_pr,
)
from .services.devops.factory import get_git_provider
from .services.devops.repo_bootstrap import bootstrap_repo
from .services.common_services import generate_backend_tf

async def devops_node(
    state: AgentState,
) -> dict:

    print(
        "--- [Agent] DevOps / GitHub Working ---"
    )

    # provider

    repo_config = {
        **state["repo_config"],
        "thread_id": state["thread_id"]
    }

    provider = get_git_provider(
        repo_config
    )

    # repo name

    thread_id = state["thread_id"]

    repo_name = (
        f"infra-proj-{thread_id[:8]}"
    )

    # bootstrap repo

    repo_result = await bootstrap_repo(
        provider=provider,
        repo_name=repo_name,
        description=(
            "Infra proj generated "
            "by Infra AI agent."
        ),
        private=True
    )

    # update repo config

    repo_config.update({
        "repo": repo_result[
            "repo_name"
        ],

        "target_branch": "dev",
    })

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

    # create AI tf PR
    generated_code = {
        **state["generated_code"],
        "backend.tf": generate_backend_tf(
            cloud_provider=state["cloud_provider"],
            thread_id=state["thread_id"],
        ),
    }

    pr_result = await create_infra_pr(
        repo_config=repo_config,
        generated_code=generated_code,
    )

    return {
        "repo_config": repo_config,
        "repo_url": repo_result["repo_url"],
        "git_branch": pr_result["branch"],
        "git_commit_id": pr_result["commit_id"],
        "pull_request_url": pr_result["pull_request_url"],
        "pull_request_id": pr_result["pull_request_id"],
        "deployment_status": "pr_created",
    }
