import os
import asyncio
import base64
from pathlib import Path

from github import Github, Auth, InputGitTreeElement

from ..base import GitProvider

from nacl import public


class GitHubProvider(GitProvider):

    def __init__(
        self,
        owner: str,
    ):
        token = os.getenv("GITHUB_TOKEN")

        if not token:
            raise ValueError(
                "GITHUB_TOKEN environment variable is not set."
            )

        self.github = Github(
            auth=Auth.Token(token)
        )

        self.owner = owner

        self.repo = None

    # use repo methods
    def use_repo(self, repo_name: str):
        print(self.owner)
        print(repo_name)
        self.repo = self.github.get_repo(
            f"{self.owner}/{repo_name}"
        )

    def _require_repo(self):
        if self.repo is None:
            raise RuntimeError("Repo has not been initialized.")

        return self.repo

    # ==================================================
    # Branch SHA
    # ==================================================

    async def get_branch_sha(
        self,
        branch_name: str,
    ) -> str:

        return await asyncio.to_thread(
            self._get_branch_sha,
            branch_name,
        )

    def _get_branch_sha(
        self,
        branch_name: str,
    ) -> str:

        repo = self._require_repo()

        branch = repo.get_branch(
            branch_name
        )

        return branch.commit.sha

    # ==================================================
    # Create branch
    # ==================================================

    async def create_branch(
        self,
        branch_name: str,
        base_sha: str,
    ) -> None:

        await asyncio.to_thread(
            self._create_branch,
            branch_name,
            base_sha,
        )

    def _create_branch(
        self,
        branch_name: str,
        base_sha: str,
    ) -> None:

        repo = self._require_repo()

        repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=base_sha,
        )

    # ==================================================
    # Commit files
    # ==================================================

    async def commit_files(
        self,
        branch_name: str,
        files: dict[str, str],
        commit_message: str,
    ) -> str:

        return await asyncio.to_thread(
            self._commit_files,
            branch_name,
            files,
            commit_message,
        )

    def _commit_files(
        self,
        branch_name: str,
        files: dict[str, str],
        commit_message: str,
    ) -> str:

        # ------------------------------------------
        # Current branch HEAD
        # ------------------------------------------
        repo = self._require_repo()

        branch = repo.get_branch(
            branch_name
        )

        parent_commit = repo.get_git_commit(
            branch.commit.sha
        )

        # ------------------------------------------
        # Create blobs + tree elements
        # ------------------------------------------

        tree_elements = []

        for file_path, content in files.items():

            normalized_path = file_path.lstrip("/")

            if ".." in Path(normalized_path).parts:
                raise ValueError(
                    f"Invalid repo path: {file_path}"
                )

            blob = repo.create_git_blob(
                content=content,
                encoding="utf-8",
            )

            tree_elements.append(
                InputGitTreeElement(
                    path=normalized_path,
                    mode="100644",
                    type="blob",
                    sha=blob.sha,
                )
            )

        # ------------------------------------------
        # Create Git tree
        # ------------------------------------------

        tree = repo.create_git_tree(
            tree_elements,
            base_tree=parent_commit.tree,
        )

        # ------------------------------------------
        # Create commit
        # ------------------------------------------

        commit = repo.create_git_commit(
            message=commit_message,
            tree=tree,
            parents=[parent_commit],
        )

        # ------------------------------------------
        # Move branch to new commit
        # ------------------------------------------

        ref = repo.get_git_ref(
            f"heads/{branch_name}"
        )

        ref.edit(commit.sha)

        return commit.sha

    # ==================================================
    # Pull Request
    # ==================================================

    async def create_pull_request(
        self,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
    ) -> dict:

        return await asyncio.to_thread(
            self._create_pull_request,
            source_branch,
            target_branch,
            title,
            description,
        )

    def _create_pull_request(
        self,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
    ) -> dict:

        repo = self._require_repo()

        pull_request = repo.create_pull(
            title=title,
            body=description,
            head=source_branch,
            base=target_branch,
        )

        return {
            "id": pull_request.number,
            "url": pull_request.html_url,
        }

    async def create_repo(
        self,
        repo_name: str,
        description: str,
        private: bool = True,
    ) -> dict:

        return await asyncio.to_thread(
            self._create_repository,
            repo_name,
            description,
            private,
        )


    def _create_repository(
        self,
        repo_name: str,
        description: str,
        private: bool,
    ) -> dict:

        user = self.github.get_user()

        repo = user.create_repo(
            name=repo_name,
            description=description,
            private=private,
            auto_init=True,
        )

        self.repo = repo

        default_branch = repo.default_branch

        branch = repo.get_branch(default_branch)

        return {
            "name": repo.name,
            "full_name": repo.full_name,
            "url": repo.html_url,
            "clone_url": repo.clone_url,
            "default_branch": repo.default_branch,
            "initial_commit_sha": branch.commit.sha
        }  

    def _encrypt_secret(
        self,
        public_key: str,
        secret_value: str,
    ) -> str:

        public_key_bytes = base64.b64decode(
            public_key
        )

        sealed_box = public.SealedBox(
            public.PublicKey(public_key_bytes)
        )

        encrypted = sealed_box.encrypt(
            secret_value.encode("utf-8")
        )

        return base64.b64encode(
            encrypted
        ).decode("utf-8")

    async def set_repo_secret(self, name, value):

        await asyncio.to_thread(
            self._set_repo_secret,
            name=name,
            value=value
        )

    def _set_repo_secret(
        self,
        name: str,
        value: str,
    ) -> None:

        repo = self._require_repo()

        # get repo public key
        response = repo._requester.requestJsonAndCheck(
            "GET",
            f"/repos/{self.owner}/{repo.name}/actions/secrets/public-key"
        )

        key_data = response[1]

        public_key = key_data["key"]
        key_id = key_data["key_id"]

        # encrypt using libsodium
        encrypted_value = self._encrypt_secret(
            public_key=public_key,
            secret_value=value
        )

        repo._requester.requestJsonAndCheck(
            "PUT",
            f"/repos/{self.owner}/{repo.name}/actions/secrets/{name}",
            input={
                "encrypted_value": encrypted_value,
                "key_id": key_id,
            }
        )


    def _ensure_environment(
        self,
        environment_name: str,
    ) -> None:

        repo = self._require_repo()

        repo._requester.requestJsonAndCheck(
            "PUT",
            f"/repos/{self.owner}/{repo.name}"
            f"/environments/{environment_name}",
            input={},
        )

    async def set_repo_variable(
        self,
        name: str,
        value: str
    ) -> None:

        await asyncio.to_thread(
            self._set_repo_variable,
            name=name,
            value=value
        )


    def _set_repo_variable(
        self,
        name: str,
        value: str,
    ) -> None:

        repo = self._require_repo()

        # TODO: right now its only POST but we need to make it idempotent
        # first do GET to check if already exists, then POST or PATCH accordingly

        repo._requester.requestJsonAndCheck(
            "POST",
            f"/repos/{self.owner}/{repo.name}/actions/variables",
            input={
                "name": name,
                "value": value
            }
        )

    async def set_environment_secret(
        self,
        environment_name: str,
        name: str,
        value: str,
    ) -> None:

        await asyncio.to_thread(
            self._set_environment_secret,
            environment_name,
            name,
            value,
        )

    def _set_environment_secret(
        self,
        environment_name: str,
        name: str,
        value: str
    ) -> None:

        repo = self._require_repo()

        # ensure env exists
        self._ensure_environment(
            environment_name=environment_name
        )

        response = repo._requester.requestJsonAndCheck(
            "GET",
            f"/repos/{self.owner}/{repo.name}"
            f"/environments/{environment_name}"
            f"/secrets/public-key"
        )

        key_data = response[1]

        encrypted_value = self._encrypt_secret(
            key_data["key"],
            value
        )

        repo._requester.requestJsonAndCheck(
            "PUT",
            f"/repos/{self.owner}/{repo.name}"
            f"/environments/{environment_name}"
            f"/secrets/{name}",
            input={
                "encrypted_value": encrypted_value,
                "key_id": key_data["key_id"]
            }
        )

    async def set_environment_variable(
        self,
        environment_name: str,
        name: str,
        value: str
    ) -> None:

        await asyncio.to_thread(
            self._set_environment_variable,
            environment_name,
            name,
            value
        )

    def _set_environment_variable(
        self,
        environment_name: str,
        name: str,
        value: str
    ) -> None:

        repo = self._require_repo()

        # ensure env exists
        self._ensure_environment(
            environment_name=environment_name
        )

        repo._requester.requestJsonAndCheck(
            "POST",
            f"/repos/{self.owner}/{repo.name}"
            f"/environments/{environment_name}"
            f"/variables",
            input={
                "name": name,
                "value": value
            }
        )

    async def set_repo_secrets(
        self,
        secrets: dict[str, str]
    ) -> None:
        for name, value in secrets.items():
            await self.set_repo_secret(
                name=name,
                value=value
            )

    async def set_repo_variables(
        self,
        variables: dict[str, str]
    ) -> None:
        for name, value in variables.items():
            await self.set_repo_variable(
                name=name,
                value=value
            )

    async def set_environment_secrets(
        self,
        environment_name: str,
        secrets: dict[str, str],
    ) -> None:

        for name, value in secrets.items():
            await self.set_environment_secret(
                environment_name=environment_name,
                name=name,
                value=value,
            )


    async def set_environment_variables(
        self,
        environment_name: str,
        variables: dict[str, str],
    ) -> None:

        for name, value in variables.items():
            await self.set_environment_variable(
                environment_name=environment_name,
                name=name,
                value=value,
            )