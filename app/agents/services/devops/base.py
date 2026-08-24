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
    async def create_repo(
        self,
        repo_name: str,
        description: str,
        private: bool = True,
    ) -> dict:
        pass

    # ==============================
    # Repository secrets / variables
    # ==============================

    @abstractmethod
    async def set_repo_secret(
        self,
        name: str,
        value: str,
    ) -> None:
        pass

    @abstractmethod
    async def set_repo_variable(
        self,
        name: str,
        value: str,
    ) -> None:
        pass

    # ==============================
    # Environment secrets / variables
    # ==============================

    @abstractmethod
    async def set_environment_secret(
        self,
        environment_name: str,
        name: str,
        value: str,
    ) -> None:
        pass

    @abstractmethod
    async def set_environment_variable(
        self,
        environment_name: str,
        name: str,
        value: str,
    ) -> None:
        pass


    # set repo and env secters and vars
    @abstractmethod
    async def set_repo_secrets(
        self,
        secrets: dict[str, str]
    ) -> None:
        pass

    @abstractmethod
    async def set_repo_variables(
        self,
        variables: dict[str, str]
    ) -> None:
        pass

    @abstractmethod
    async def set_environment_secrets(
        self,
        environment_name: str,
        secrets: dict[str, str]
    ) -> None:
        pass

    @abstractmethod
    async def set_environment_variables(
        self,
        environment_name: str,
        variables: dict[str, str]
    ) -> None:
        pass
    
    