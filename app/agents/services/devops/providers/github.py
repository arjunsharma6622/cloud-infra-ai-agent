import os
import asyncio

from github import Github, Auth, InputGitTreeElement

from ..base import GitProvider


class GitHubProvider(GitProvider):

    def __init__(
        self,
        owner: str,
        repository: str,
    ):
        token = os.getenv("GITHUB_TOKEN")

        if not token:
            raise ValueError(
                "GITHUB_TOKEN environment variable is not set."
            )

        self.github = Github(
            auth=Auth.Token(token)
        )

        self.repo = self.github.get_repo(
            f"{owner}/{repository}"
        )

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

        branch = self.repo.get_branch(
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

        self.repo.create_git_ref(
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

        branch = self.repo.get_branch(
            branch_name
        )

        parent_commit = self.repo.get_git_commit(
            branch.commit.sha
        )

        # ------------------------------------------
        # Create blobs + tree elements
        # ------------------------------------------

        tree_elements = []

        for file_path, content in files.items():

            blob = self.repo.create_git_blob(
                content=content,
                encoding="utf-8",
            )

            tree_elements.append(
                InputGitTreeElement(
                    path=file_path.lstrip("/"),
                    mode="100644",
                    type="blob",
                    sha=blob.sha,
                )
            )

        # ------------------------------------------
        # Create Git tree
        # ------------------------------------------

        tree = self.repo.create_git_tree(
            tree_elements,
            base_tree=parent_commit.tree,
        )

        # ------------------------------------------
        # Create commit
        # ------------------------------------------

        commit = self.repo.create_git_commit(
            message=commit_message,
            tree=tree,
            parents=[parent_commit],
        )

        # ------------------------------------------
        # Move branch to new commit
        # ------------------------------------------

        ref = self.repo.get_git_ref(
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

        pull_request = self.repo.create_pull(
            title=title,
            body=description,
            head=source_branch,
            base=target_branch,
        )

        return {
            "id": pull_request.number,
            "url": pull_request.html_url,
        }

    async def create_repository(
        self,
        repository_name: str,
        description: str,
        private: bool = True,
    ) -> dict:

        return await asyncio.to_thread(
            self._create_repository,
            repository_name,
            description,
            private,
        )


    def _create_repository(
        self,
        repository_name: str,
        description: str,
        private: bool,
    ) -> dict:

        user = self.github.get_user()

        repo = user.create_repo(
            name=repository_name,
            description=description,
            private=private,
            auto_init=True,
        )

        return {
            "name": repo.name,
            "full_name": repo.full_name,
            "url": repo.html_url,
            "clone_url": repo.clone_url,
            "default_branch": repo.default_branch,
        }  

