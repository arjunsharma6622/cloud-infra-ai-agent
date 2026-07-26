from enum import Enum

class LLMProvider(str, Enum):
    GEMINI = "gemini"
    # OPENAI = "openai"
    # ANTHROPIC = "anthropic"

MODEL_CONFIG = {
    "parser": {
        "provider": LLMProvider.GEMINI,
        "model": "gemini-3.1-flash-lite",
    },
    "architecture": {
        "provider": LLMProvider.GEMINI,
        "model": "gemini-3.1-flash-lite",
    },
    "generator": {
        "provider": LLMProvider.GEMINI,
        "model": "gemini-3.1-flash-lite",
    },
    "validator": {
        "provider": LLMProvider.GEMINI,
        "model": "gemini-3.1-flash-lite",
    },
}

class AgentType(str, Enum):
    PARSER = "parser"
    ARCHITECTURE = "architecture"
    GENERATOR = "generator"
    VALIDATOR = "validator"