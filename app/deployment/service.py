import os
import uuid
from git import Repo

# Path to your LOCAL clone of cloud-infra-deployments
DEPLOYMENT_REPO = r"C:\Users\Administrator\Desktop\AI_AGENT\cloud-infra-deployments"


TERRAFORM_ROOT = os.path.join(
    DEPLOYMENT_REPO,
    "terraform",
    "deployments"
)


def save_generated_code(thread_id: str, generated_code: dict):

    deployment_id = str(uuid.uuid4())

    deployment_folder = os.path.join(
        TERRAFORM_ROOT,
        deployment_id
    )

    os.makedirs(deployment_folder, exist_ok=True)

    # Write terraform files
    for filename, content in generated_code.items():

        filepath = os.path.join(
            deployment_folder,
            filename
        )

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(content)

    # Open local git repository
    repo = Repo(DEPLOYMENT_REPO)

    # Stage all changes
    repo.git.add(A=True)

    # Commit
    repo.index.commit(
        f"Generated deployment {deployment_id}"
    )

    # Push to GitHub
    origin = repo.remote("origin")
    origin.push()

    return deployment_id