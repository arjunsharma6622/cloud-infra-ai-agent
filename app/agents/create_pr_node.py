from .state import AgentState

from .services.common_services import (
    generate_backend_tf,
)

from .services.devops.workflow import (
    generate_terraform_workflow,
)

from .services.devops.service import (
    create_infra_pr,
)


async def create_pr_node(
    state: AgentState,
) -> dict:

    print(
        "--- [Agent] Creating Terraform PR ---"
    )

    generated_code = {
        **state["generated_code"],

        "backend.tf": generate_backend_tf(
            cloud_provider=state["cloud_provider"],
            thread_id=state["thread_id"],
        ),

        ".github/workflows/terraform.yml":
            generate_terraform_workflow(
                cloud_provider=state[
                    "cloud_provider"
                ],
                terraform_inputs=[
                    item
                    for item in state[
                        "terraform_inputs"
                    ]
                    if (
                        item.get("value") is not None
                        or item["sensitive"]
                    )
                ],
            ),
    }

    pr_result = await create_infra_pr(
        repo_config=state["repo_config"],
        generated_code=generated_code,
    )

    return {
        "generated_code": generated_code,

        "git_branch": pr_result["branch"],

        "git_commit_id": pr_result[
            "commit_id"
        ],

        "pull_request_url": pr_result[
            "pull_request_url"
        ],

        "pull_request_id": pr_result[
            "pull_request_id"
        ],

        "deployment_status": "pr_created",
    }

