import os

from dotenv import load_dotenv
from github import Github

load_dotenv()


def merge_pull_request(pr_number: int):

    token = os.getenv("GITHUB_TOKEN")
    owner = os.getenv("GITHUB_OWNER")
    repo_name = os.getenv("GITHUB_REPO")

    if not token:
        raise ValueError(
            "GITHUB_TOKEN is not configured."
        )

    if not owner:
        raise ValueError(
            "GITHUB_OWNER is not configured."
        )

    if not repo_name:
        raise ValueError(
            "GITHUB_REPO is not configured."
        )

    github = Github(token)

    repo = github.get_repo(
        f"{owner}/{repo_name}"
    )

    pr = repo.get_pull(pr_number)

    print(
        f"Checking Pull Request #{pr_number}"
    )

    if pr.state != "open":

        raise Exception(
            f"Pull Request #{pr_number} "
            f"is already {pr.state}."
        )

    if pr.base.ref != "main":

        raise Exception(
            f"Pull Request #{pr_number} "
            "does not target main."
        )

    if pr.head.ref != "dev":

        raise Exception(
            f"Pull Request #{pr_number} "
            "does not come from dev."
        )

    if pr.mergeable is False:

        raise Exception(
            f"Pull Request #{pr_number} "
            "cannot currently be merged."
        )

    result = pr.merge(
        commit_message=(
            f"Merge Terraform deployment PR "
            f"#{pr_number}"
        ),
        merge_method="merge",
    )

    if not result.merged:

        raise Exception(
            result.message
        )

    print(
        f"Pull Request #{pr_number} "
        "merged successfully."
    )

    return {
        "merged": True,
        "message": result.message,
    }