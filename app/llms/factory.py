import os

from typing import Type

from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic

from app.config import LLMProvider

def get_llm(
    provider: LLMProvider,
    model: str,
    **kwargs
):
    if provider == LLMProvider.GEMINI:
        return ChatGoogleGenerativeAI(
            model=model,
            **kwargs,
        )

    # elif provider == Provider.OPENAI:
    #     return ChatOpenAI(
    #         model=model,
    #         api_key=os.getenv("OPENAI_API_KEY"),
    #         **kwargs,
    #     )

    # elif provider == Provider.ANTHROPIC:
    #     return ChatAnthropic(
    #         model=model,
    #         api_key=os.getenv("ANTHROPIC_API_KEY"),
    #         **kwargs,
    #     )

    raise ValueError(f"Unsupported provider: {provider}")

def get_structured_llm(
    schema: Type,
    provider: LLMProvider,
    model: str,
    **kwargs
):
    llm = get_llm(
        provider=provider,
        model=model,
        **kwargs,
    )

    return llm.with_structured_output(schema)
