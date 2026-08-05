# app/deployment/github.py

import requests
import os


def trigger_workflow(deployment_id: str):

    token = os.getenv("GITHUB_TOKEN")

    owner = os.getenv("GITHUB_OWNER")

    repo = os.getenv("GITHUB_REPO")

    workflow = "deploy.yml"

    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches"

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