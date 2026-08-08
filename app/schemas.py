from pydantic import BaseModel

class ArchitecturePlan(BaseModel):
    architecture_markdown: str
    resources: list[str]

# class ProjectPlan(BaseModel):

# DB/Req, Res Schemas
class ChatRequest(BaseModel):
    thread_id: str
    prompt: str | None = None