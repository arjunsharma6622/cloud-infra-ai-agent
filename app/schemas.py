from pydantic import BaseModel

# class ProjectPlan(BaseModel):

# DB/Req, Res Schemas
class ChatRequest(BaseModel):
    thread_id: str
    prompt: str | None = None