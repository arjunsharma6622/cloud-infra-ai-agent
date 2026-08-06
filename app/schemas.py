from pydantic import BaseModel

class ArchitecturePlan(BaseModel):
    architecture_markdown: str
    resources: list[str]

# class ProjectPlan(BaseModel):
