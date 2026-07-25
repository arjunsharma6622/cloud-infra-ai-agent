from .factory import get_llm, get_structured_llm
from app.config import MODEL_CONFIG

__all__ = [
    "get_llm",
    "get_structured_llm",
]

def get_agent_llm(agent_name: str):
    cfg = MODEL_CONFIG[agent_name]
    return get_llm(
        provider=cfg["provider"],
        model=cfg["model"],
    )


def get_agent_structured_llm(agent_name: str, schema):
    return get_agent_llm(agent_name).with_structured_output(schema)