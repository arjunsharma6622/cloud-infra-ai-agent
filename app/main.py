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
from app.database.chat_repository import ChatRepository
from app.database.constants import Role, MessageType
from app.deployment.service import save_generated_code

load_dotenv()

app = FastAPI(title="Infra AI Agent")

chat_repo = ChatRepository()

@app.on_event("startup")
def startup():

    init_db()

class ChatRequest(BaseModel):
    thread_id: str

    prompt: str | None = None

db_path = "checkpoints.sqlite"
from app.deployment.github import merge_pull_request

class DeployRequest(BaseModel):
    pr_number: int
    confirmation: str


@app.post("/deploy")
def deploy(req: DeployRequest):

    if req.confirmation.strip().upper() != "YES":
        return {
            "status": "cancelled",
            "message": "Deployment cancelled.",
        }

    merge_pull_request(req.pr_number)

    return {
        "status": "started",
        "message": "Deployment pipeline started.",
    }
@app.get("/chats")
def get_all_chats():
    try:
        projects = chat_repo.list_projects()

        return {"threads": projects}
    except Exception as e:
        return {"threads": []}

@app.get("/chat/{thread_id}/history")
def get_chat_history(thread_id: str):
    messages = chat_repo.get_messages(thread_id)
    
    return {
        "messages": messages
    }


@app.post("/stream")
async def stream_assistant(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}

    thread_id = request.thread_id
    user_prompt = request.prompt

    # DB: create a new proj if does not exist
    chat_repo.create_project(
        thread_id=thread_id,
        title=f"Proj-{thread_id[:8]}"
    )

    # DB : save user prompt in msg
    chat_repo.save_message(
        thread_id=thread_id,
        role=Role.USER,
        message_type=MessageType.TEXT,
        content=user_prompt
    )

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
                clarifying_question = interrupt.value

                # DB: save clarifying question in db
                print("Saving question to db")
                chat_repo.save_message(
                    thread_id=thread_id,
                    role=Role.ASSISTANT,
                    message_type=MessageType.CLARIFICATION,
                    content=clarifying_question
                )

                yield json.dumps({
                    "type": "interrupt",
                    "message": clarifying_question,
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

        # -------------------------------------------------
        # Graph completed
        # -------------------------------------------------

        final_state = compiled_graph.get_state(config).values

        deployment = save_generated_code(
            thread_id,
            final_state["generated_code"],
        )

        print("=" * 50)
        print("Deployment ID:", deployment["deployment_id"])
        print("Branch:", deployment["branch_name"])
        print("PR URL:", deployment["pr_url"])
        print("=" * 50)

        # -----------------------------
        # NEW: Send deployment metadata
        # to frontend
        # -----------------------------
        yield json.dumps({
            "type": "deployment",
            "deployment": deployment
        }) + "\n"

        # DB : save final state in db
        chat_repo.save_message(
            thread_id=thread_id,
            role=Role.ASSISTANT,
            message_type=MessageType.FINAL_OUTPUT,
            content=json.dumps(
                {
                    "project_spec": final_state.get("project_spec"),
                    "srs": final_state.get("srs_document"),
                    "architecture": final_state.get("architecture_plan"),
                    "terraform": final_state.get("generated_code"),
                    "deployment": deployment
                }
            ),
            metadata={
                "agent": "graph_complete"
            }
        )

        print("EVENT Ended...")

    return StreamingResponse(
        event_generator(),
        media_type="application/x-ndjson"
    )