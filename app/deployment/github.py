import os
import requests
from github import Github


def merge_pull_request(pr_number: int):

    github = Github(os.getenv("GITHUB_TOKEN"))

    repo = github.get_repo(
        f"{os.getenv('GITHUB_OWNER')}/{os.getenv('GITHUB_REPO')}"
    )

    pr = repo.get_pull(pr_number)

    if pr.state != "open":
        raise Exception(
            f"Pull Request #{pr_number} is already closed."
        )

    result = pr.merge(
        commit_message=f"Merge PR #{pr_number} from AI Agent",
        merge_method="merge",   # merge / squash / rebase
    )

    if not result.merged:
        raise Exception(result.message)

    return {
        "merged": True,
        "message": result.message,
    }


def trigger_workflow(deployment_id: str):

    token = os.getenv("GITHUB_TOKEN")

    owner = os.getenv("GITHUB_OWNER")

    repo = os.getenv("GITHUB_REPO")

    workflow = "deploy.yml"

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/actions/workflows/{workflow}/dispatches"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    payload = {
        "ref": "main",
        "inputs": {
            "deployment_id": deployment_id,
        },
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
    )

    if response.status_code != 204:
        raise Exception(response.text)

    return True