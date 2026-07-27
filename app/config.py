import os
from enum import Enum

class LLMProvider(str, Enum):
    GEMINI = "gemini"
    # OPENAI = "openai"
    # ANTHROPIC = "anthropic"

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-3.1-flash-lite")

MODEL_CONFIG = {
    "parser": {
        "provider": LLMProvider.GEMINI,
        "model": os.getenv("PARSER_MODEL", DEFAULT_MODEL),
    },
    "srs": {
        "provider": LLMProvider.GEMINI,
        "model": os.getenv("SRS_MODEL", DEFAULT_MODEL),
    },
    "architecture": {
        "provider": LLMProvider.GEMINI,
        "model": os.getenv("ARCHITECTURE_MODEL", DEFAULT_MODEL),
    },
    "generator": {
        "provider": LLMProvider.GEMINI,
        "model": os.getenv("GENERATOR_MODEL", DEFAULT_MODEL),
    },
    "validator": {
        "provider": LLMProvider.GEMINI,
        "model": os.getenv("VALIDATOR_MODEL", DEFAULT_MODEL),
    },
}

class AgentType(str, Enum):
    PARSER = "parser"
    SRS = "srs"
    ARCHITECTURE = "architecture"
    GENERATOR = "generator"
    VALIDATOR = "validator"