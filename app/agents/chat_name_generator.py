from langchain_core.messages import SystemMessage

from .state import AgentState
from .schemas.chat_name_node import ChatNameResult

from app.config import AgentType
from app.llms import get_agent_structured_llm

from .prompts import CHAT_NAME_SYSTEM_PROMPT


def chat_name_generator_node(state: AgentState) -> dict:

    print("\n--- [Agent] Chat Name Generator Working ---")

    structured_llm = get_agent_structured_llm(
        AgentType.PARSER,
        ChatNameResult
    )

    prompt = [
        SystemMessage(
            content=CHAT_NAME_SYSTEM_PROMPT
        ),
        *state.get("messages", []),
    ]

    result: ChatNameResult = structured_llm.invoke(prompt)

    chat_name = result.chat_name.strip()

    # Print generated chat name
    print("\n================================")
    print("GENERATED CHAT NAME")
    print("================================")
    print(chat_name)
    print("================================\n")

    return {
        "chat_name": chat_name
    }