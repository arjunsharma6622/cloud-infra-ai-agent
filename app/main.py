from fastapi import FastAPI
from pydantic import BaseModel
from app.agents.graph import compiled_graph
from dotenv import load_dotenv
import json
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
import sqlite3
from langgraph.types import Command
from app.database.schema import init_db

load_dotenv()

app = FastAPI(title="Infra AI Agent")

@app.on_event("startup")
def startup():

    init_db()

class ChatRequest(BaseModel):
    thread_id: str

    prompt: str | None = None

db_path = "checkpoints.sqlite"

@app.get("/chats")
def get_all_chats():
    try:
        # Query the SQLite checkpointer database directly for unique thread IDs
        conn_query = sqlite3.connect(db_path)
        cursor = conn_query.cursor()
        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
        threads = [row[0] for row in cursor.fetchall()]
        conn_query.close()
        return {"threads": threads}
    except Exception as e:
        return {"threads": []}

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

@app.get("/chat/{thread_id}/history")
def get_chat_history(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    state_snapshot = compiled_graph.get_state(config)
    
    if not state_snapshot.values:
        return {"messages": []}
    
    state_data = state_snapshot.values
    
    # Reconstruct the frontend payload based on the saved LangGraph state
    return {
        "user_prompt": state_data.get("user_prompt", ""),
        "spec": state_data.get("project_spec", {}),
        "plan": state_data.get("architecture_plan", ""),
        "code": state_data.get("generated_code", {})
    }


@app.post("/stream")
async def stream_assistant(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}

    snapshot = compiled_graph.get_state(config)

    async def event_generator():

        if snapshot.next:
            stream = compiled_graph.stream(
                Command(resume=request.prompt),
                config=config,                
            )
        else:
            initial_state = {
                "thread_id": request.thread_id,
                "messages": [HumanMessage(content=request.prompt)],
                "clarification_question": None,
                "validation_attempts": 0,
                "validation_passed": False,
                "validation_errors": "",
            }

            stream = compiled_graph.stream(
                initial_state,
                config=config,
            )

        for event in stream:
            
            if "__interrupt__" in event:
                print(event)

                print("Sending interrupt to client")

                interrupt = event["__interrupt__"][0]

                yield json.dumps({
                    "type": "interrupt",
                    "message": interrupt.value,
                }) + "\n"

                print("Interrupt yielded")

                return

            safe_event = {}

            for node_name, payload in event.items():
                if isinstance(payload, dict):
                    payload = payload.copy()
                    payload.pop("messages", None)

                safe_event[node_name] = payload

            yield json.dumps(safe_event) + "\n"

        print("EVENT Ended...")

    return StreamingResponse(
        event_generator(), 
        media_type="application/x-ndjson"
    )

