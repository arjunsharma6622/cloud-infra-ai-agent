from fastapi import APIRouter, Request, Depends, HTTPException
import json
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from app.database.chat_repository import ChatRepository
from app.database.constants import Role, MessageType
from app.schemas import ChatRequest, ArchitecturePlan
from fastapi.encoders import jsonable_encoder

# TEMP: generated files for validation
from app.config import archi
from app.tf_validation.workspace import create_workspace, write_files
from app.tf_validation.runner import terraform_init, terraform_validate
from app.tf_validation.parser import parse_validation_output
from app.services.terraform_generator import generate_terraform
from uuid import uuid4
from datetime import datetime
from app.tf_validation.logger import (
    log_attempt,
    log_stage,
    log_success,
    log_failure,
)
from app.tf_validation.logger import ValidationLogger

chat_repo = ChatRepository()

router = APIRouter()

#  TEMP: for validation node testing

@router.get("/validation", tags=["Testing/Validation"])
async def validationRoute():

    architecture_plan = ArchitecturePlan(
        architecture_markdown=archi,
        resources=[]
    )

    validation_run_id = (
        f"{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:6]}"
    )

    # -------------------------------------------------------
    # Initial Terraform Generation
    # -------------------------------------------------------

    generation_result = generate_terraform(
        architecture_plan=architecture_plan,
    )

    generated_files = generation_result["generated_code"]

    # -------------------------------------------------------
    # Validation Loop
    # -------------------------------------------------------

    for attempt in range(5):

        workspace = create_workspace(
            validation_run_id,
            attempt + 1,
        )

        validation_logger = ValidationLogger(workspace)

        log_attempt(
            validation_run_id,
            attempt + 1,
            workspace,
        )

        # Save everything that produced THIS attempt
        validation_logger.save_prompt(
            generation_result["generation_prompt"]
        )

        try:

            # -------------------------------------------------------
            # Write Terraform Files
            # -------------------------------------------------------

            log_stage("Writing Terraform files")

            write_files(
                workspace,
                generated_files,
            )

            log_success("Terraform files written.")

            # -------------------------------------------------------
            # Terraform Init
            # -------------------------------------------------------

            log_stage("terraform init")

            init_code, init_output = await terraform_init(
                workspace
            )

            if init_code != 0:

                log_failure("terraform init failed.")


                validation_logger.save_command_output(
                    command="terraform_init",
                    return_code=init_code,
                    output=init_output,
                )

                validation_logger.save_summary(
                    attempt=attempt + 1,
                    stage="terraform_init",
                    passed=False,
                )

                generation_result = generate_terraform(
                    architecture_plan=architecture_plan,
                    validation_attempts=attempt + 1,
                    validation_stage="init",
                    validation_errors=[
                        {
                            "file": "",
                            "severity": "error",
                            "summary": "Terraform init failed",
                            "detail": init_output,
                        }
                    ],
                    previous_code=generated_files,
                )

                generated_files = generation_result["generated_code"]

                continue

            log_success("terraform init succeeded.")

            # -------------------------------------------------------
            # Terraform Validate
            # -------------------------------------------------------

            log_stage("terraform validate")

            validate_code, validate_output = await terraform_validate(
                workspace,
            )

            passed, diagnostics = parse_validation_output(
                validate_output,
            )

            if passed and validate_code == 0:

                log_success("terraform validate succeeded.")

                validation_logger.save_summary(
                    attempt=attempt + 1,
                    stage="terraform_validate",
                    passed=True,
                )

                return {
                    "validation_passed": True,
                    "attempts": attempt + 1,
                    "generated_code": generated_files,
                }

            log_failure("terraform validate failed.")

            validation_logger.save_command_output(
                command="terraform_validate",
                return_code=validate_code,
                output=validate_output,
            )

            validation_logger.save_validation_json(
                diagnostics,
            )

            validation_logger.save_summary(
                attempt=attempt + 1,
                stage="terraform_validate",
                passed=False,
            )

            generation_result = generate_terraform(
                architecture_plan=architecture_plan,
                validation_attempts=attempt + 1,
                validation_stage="validate",
                validation_errors=diagnostics,
                previous_code=generated_files,
            )

            generated_files = generation_result["generated_code"]

        finally:
            print("DONE")
    # -------------------------------------------------------
    # Max Retries
    # -------------------------------------------------------

    validation_logger.save_summary(
        attempt=5,
        stage="max_retries",
        passed=False,
    )

    return {
        "validation_passed": False,
        "attempts": 5,
        "generated_code": generated_files,
        "validation_errors": (
            diagnostics
            if "diagnostics" in locals()
            else init_output
        ),
    }


@router.get("/chats", tags=["Chat"])
def get_all_chats():
    
    try:
        projects = chat_repo.list_projects()

        return {"threads": projects}
    except Exception as e:
        return {"threads": []}

@router.get("/chat/{thread_id}/history", tags=["Chat"])
def get_chat_history(thread_id: str):
    messages = chat_repo.get_messages(thread_id)
    
    return {
        "messages": messages
    }

# 1. Reusable dependency to fetch LangGraph from app state
def get_graph(request: Request):
    graph = getattr(request.app.state, "compiled_graph", None)
    if graph is None:
        raise HTTPException(status_code=500, detail="LangGraph engine not initialized")
    return graph

@router.post("/stream", tags=["Agent Stream"])
async def stream_assistant(
    request: ChatRequest, 
    compiled_graph = Depends(get_graph)
):
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

            clean_json_data = jsonable_encoder(safe_event)

            yield json.dumps(clean_json_data) + "\n"


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
                jsonable_encoder(
                    {
                        "project_spec": final_state.get("project_spec"),
                        "srs": final_state.get("srs_document"),
                        "architecture": final_state.get("architecture_plan"),
                        "terraform": final_state.get("generated_code"),
                    }
                )
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

