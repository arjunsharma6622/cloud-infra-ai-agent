from abc import ABC, abstractmethod

class GitProvider(ABC):

    @abstractmethod
    async def get_branch_sha(
        self,
        branch_name: str
    ) -> str:
        pass

    @abstractmethod
    async def create_branch(
        self,
        branch_name: str,
        base_sha: str,
    ) -> None:
        pass

    @abstractmethod
    async def commit_files(
        self,
        branch_name: str,
        files: dict[str, str],
        commit_message: str,
    ) -> str:
        pass

    @abstractmethod
    async def create_pull_request(
        self,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str
    ) -> dict:
        pass

    @abstractmethod
    async def create_repository(
        self,
        repository_name: str,
        description: str,
        private: bool = True,
    ) -> dict:
        pass
