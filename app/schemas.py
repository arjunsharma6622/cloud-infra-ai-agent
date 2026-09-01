from pydantic import (
    BaseModel,
    Field,
)
from typing import Dict, Any

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

class ConfigItem(BaseModel):
    name: str
    value: str

class GitHubConfigTestRequest(BaseModel):
    repository: str

    repo_secret: ConfigItem
    repo_variable: ConfigItem

    environment_name: str

    environment_secret: ConfigItem
    environment_variable: ConfigItem
    

class TerraformInputsRequest(BaseModel):

    values: Dict[str, Any] = Field(
        default_factory=dict
    )
    