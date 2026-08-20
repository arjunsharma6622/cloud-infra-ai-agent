from .base import GitProvider
from .providers.github import GitHubProvider

def get_git_provider(config) -> GitProvider:

    provider_name = config["provider"]

    if provider_name == "github":

        provider = GitHubProvider(
            owner=config["owner"]
        )

        # Repository is optional because the repository
        # may not exist yet during bootstrap.
        repo = config.get("repo")

        if repo:
            provider.use_repo(repo)

        return provider

    raise ValueError(
        f"Unsupported git provider: {provider_name}"
    )