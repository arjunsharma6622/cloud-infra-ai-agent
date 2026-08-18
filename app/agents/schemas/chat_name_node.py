from pydantic import BaseModel, Field


class ChatNameResult(BaseModel):

    chat_name: str = Field(
        description=(
            "A short and meaningful title for the conversation. "
            "Maximum 6 words. The title should describe the main "
            "infrastructure requirement."
        )
    )