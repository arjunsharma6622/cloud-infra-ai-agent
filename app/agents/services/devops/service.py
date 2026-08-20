from .factory import get_git_provider

async def create_infra_pr(
    repo_config: dict,
    generated_code: dict[str, str],
):
    provider = get_git_provider(
        repo_config
    )

    target_branch = repo_config["target_branch"]

    thread_id = repo_config["thread_id"]

    branch_name = (
        f"ai/infra/{thread_id}"
    )

    # 1. Get latest target branch

    base_sha = await provider.get_branch_sha(
        target_branch
    )

    # 2. Create AI branch

    await provider.create_branch(
        branch_name=branch_name,
        base_sha=base_sha
    )

    # 3. Commit tf
    
    commit_id = await provider.commit_files(
        branch_name=branch_name,
        files=generated_code,
        commit_message=(
            "feat: generaated infra"
        )
    )

    # 4. Create PR
    pr = await provider.create_pull_request(
        source_branch=branch_name,
        target_branch=target_branch,
        title="🤖 AI Generated Infrastructure",
        description=(
            "## Infra AI Agent\n\n"
            "Terraform infrastructure generated "
            "and validated by the Infra AI Agent.\n\n"
            "### Terraform Validation\n"
            "- ✅ terraform init\n"
            "- ✅ terraform validate\n\n"
            "Terraform plan will be executed "
            "by CI/CD after PR creation."
        ),
    )

    return {
        "branch": branch_name,
        "commit_id": commit_id,
        "pull_request_id": pr["id"],
        "pull_request_url": pr["url"],
    }

