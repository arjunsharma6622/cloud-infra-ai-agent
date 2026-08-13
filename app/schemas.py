from pydantic import BaseModel
from typing import Dict

# class ProjectPlan(BaseModel):

# DB/Req, Res Schemas
class ChatRequest(BaseModel):
    thread_id: str
    prompt: str | None = None

class GitHubPRTestRequest(BaseModel):
    owner: str
    repository: str
    target_branch: str = "dev"
    files: Dict[str, str]