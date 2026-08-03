from fastapi import FastAPI
from pydantic import BaseModel
from app.agents.graph import create_graph
from dotenv import load_dotenv
import json
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from app.database.schema import init_db
from app.database.chat_repository import ChatRepository
from app.database.constants import Role, MessageType
import shutil

# TEMP: generated files for validation
from .config import archi
from app.tf_validation.workspace import create_workspace, write_files
from app.tf_validation.runner import terraform_init, terraform_validate
from app.tf_validation.parser import parse_validation_output
from app.services.terraform_generator import generate_terraform


load_dotenv()

app = FastAPI(title="Infra AI Agent")

chat_repo = ChatRepository()

@app.on_event("startup")
async def startup():

    init_db()

    # adding compiled graph to the fastapi state
    app.state.compiled_graph = await create_graph()

    if shutil.which("terraform") is None:
        raise RuntimeError("Terraform executable not found.")

class ChatRequest(BaseModel):
    thread_id: str

    prompt: str | None = None

db_path = "checkpoints.sqlite"

#  TEMP: for validation node testing
@app.get("/validation")
async def validation():

    print("validation")

    architecture_plan = archi

    generated_files = generate_terraform(
        architecture_plan=architecture_plan
    )

    for attempt in range(5):
        print(f"\n========== Validation Attempt {attempt+1} ==========")

        print(generated_files)
        
        workspace = create_workspace()

        try:
            write_files(workspace, generated_files)

            # TERRAFORM INIT
            init_code, init_output = await terraform_init(workspace)

            if init_code != 0:

                generated_files = generate_terraform(
                    architecture_plan=architecture_plan,
                    validation_attempts=attempt+1,
                    validation_stage="init",
                    validation_errors=[
                        {
                            "file": "",
                            "severify": "error",
                            "summary": "Terraform Init failed",
                            "detail": init_output,
                        }
                    ],
                    previous_code=generated_files
                )

                continue

            # TERRAFORM VALIDATE
            validate_code, validate_output = await terraform_validate(workspace)
            passed, diagnostics = parse_validation_output(validate_output)

            if passed and validate_code==0:
                return {
                    "validation_passed": True,
                    "attempts": attempt+1,
                    "generated_code": generated_files
                }

            generated_files = generate_terraform(
                architecture_plan=architecture_plan,
                validation_attempts=attempt+1,
                validation_stage="validate",
                validation_errors=diagnostics,
                previous_code=generated_files,
            )
                  
        finally:
            print("DONE")

    return {
        "validation_passed": False,
        "attempts": 5,
        "generated_code": generated_files,
        "validation_errors": diagnostics if 'diagnostics' in locals() else init_output,
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

    # DB: create a new proj if dose not exist
    chat_repo.create_project(thread_id=thread_id, title=f"Proj-{thread_id[:8]}")

    # DB : save user prompt in msg
    chat_repo.save_message(
        thread_id=thread_id, 
        role=Role.USER, 
        message_type=MessageType.TEXT, 
        content=user_prompt
    )

    compiled_graph = app.state.compiled_graph

    snapshot = await compiled_graph.aget_state(config)

    async def event_generator():

        if snapshot.next :
            stream = compiled_graph.astream(
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

            stream = compiled_graph.astream(
                initial_state,
                config=config,
            )

        async for event in stream:
            
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

        # Graph completed
        final_state = (
            await compiled_graph.aget_state(config)
        ).values

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

