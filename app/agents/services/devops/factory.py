from .base import GitProvider
from .providers.github import GitHubProvider

def get_git_provider(
    config: dict
) -> GitProvider:

    provider = config["provider"]

    if provider == "github":

        return GitHubProvider(
            owner=config["owner"],
            repository=config["repository"]
        )

    raise ValueError(
        f"Unsupported Git provider: {provider}"
    )
