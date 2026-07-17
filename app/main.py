from fastapi import FastAPI
from pydantic import BaseModel
from app.agents.graph import compiled_graph
from dotenv import load_dotenv
import json
from fastapi.responses import StreamingResponse

load_dotenv()

app = FastAPI(title="Infra AI Agent")

class ChatRequest(BaseModel):
    prompt: str

@app.post("/chat")
def run_assistant(request: ChatRequest):
    initial_state = {
        "user_prompt": request.prompt,
        "validation_attempts": 0,
        "validation_passed": False,
        "validation_errors": ""
    }

    final_output = compiled_graph.invoke(initial_state)
    return final_output

# stream api
@app.post("/stream")
async def stream_assistant(request: ChatRequest):
    initial_state = {
        "user_prompt": request.prompt,
        "validation_attempts": 0,
        "validation_passed": False,
        "validation_errors": ""
    }

    async def event_generator():
        for event in compiled_graph.stream(initial_state):
            yield f"{json.dumps(event)}\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

# i want to create an infra on azure, i need this to be in a vpc in ap-south-1 region, and there should be 2 vms deployed (basic ones you decide), i want one vm to be in a private subnet, and other vm should be open to internet (as in it should be open to incoming and outgoing requests) while first vm should be closed to both, (decide cidr range yourself), i also want one rds db to be created
