from fastapi import APIRouter, Request, Depends, HTTPException
import json

from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.database.chat_repository import ChatRepository
from app.database.constants import Role, MessageType
from app.schemas import ChatRequest


chat_repo = ChatRepository()

router = APIRouter()


# ============================================================
# GET ALL CHATS
# ============================================================

@router.get("/chats", tags=["Chat"])
def get_all_chats():

    try:
        projects = chat_repo.list_projects()

        return {
            "threads": projects
        }

    except Exception:
        return {
            "threads": []
        }


# ============================================================
# GET CHAT HISTORY
# ============================================================

@router.get("/chat/{thread_id}/history", tags=["Chat"])
def get_chat_history(thread_id: str):

    messages = chat_repo.get_messages(thread_id)

    return {
        "messages": messages
    }


# ============================================================
# LANGGRAPH DEPENDENCY
# ============================================================

def get_graph(request: Request):

    graph = getattr(
        request.app.state,
        "compiled_graph",
        None,
    )

    if graph is None:
        raise HTTPException(
            status_code=500,
            detail="LangGraph engine not initialized",
        )

    return graph


# ============================================================
# STREAM
# ============================================================

@router.post("/stream", tags=["Agent Stream"])
async def stream_assistant(
    request: ChatRequest,
    compiled_graph=Depends(get_graph),
):

    config = {
        "configurable": {
            "thread_id": request.thread_id
        }
    }

    thread_id = request.thread_id
    user_prompt = request.prompt

    # --------------------------------------------------------
    # Create project if it does not exist
    # --------------------------------------------------------

    chat_repo.create_project(
        thread_id=thread_id,
        title=f"Proj-{thread_id[:8]}",
    )

    # --------------------------------------------------------
    # Save user message
    # --------------------------------------------------------

    chat_repo.save_message(
        thread_id=thread_id,
        role=Role.USER,
        message_type=MessageType.TEXT,
        content=user_prompt,
    )

    # --------------------------------------------------------
    # Check whether this is a new execution or a resume
    # --------------------------------------------------------

    snapshot = await compiled_graph.aget_state(config)

    async def event_generator():

        # ====================================================
        # START / RESUME GRAPH
        # ====================================================

        if snapshot.next:

            # Existing interrupted graph
            stream = compiled_graph.astream(
                Command(resume=user_prompt),
                config=config,
            )

        else:

            # New graph execution
            initial_state = {

                "thread_id": thread_id,

                "messages": [
                    HumanMessage(
                        content=user_prompt
                    )
                ],

                "clarification_question": None,

                # ----------------------------
                # Requirements
                # ----------------------------

                "project_spec": {},
                "srs_document": "",

                # ----------------------------
                # Architecture
                # ----------------------------

                "architecture_plan": "",
                "cloud_provider": "",
                "terraform_resources": [],

                # ----------------------------
                # Project Planning
                # ----------------------------

                "project_plan": {},

                # ----------------------------
                # Generation
                # ----------------------------

                "current_generation_unit": None,
                "generation_unit_index": 0,

                "generated_units": {},
                "generated_code": {},

                "generation_prompt": "",

                "generation_mode": "initial",

                # ----------------------------
                # Repair
                # ----------------------------

                "units_to_regenerate": [],
                "current_repair_index": 0,

                # ----------------------------
                # Validation
                # ----------------------------

                "validation_run_id": "",
                "validation_stage": "",
                "validation_passed": False,
                "validation_errors": [],
                "validation_attempts": 0,

                # ----------------------------
                # Devops
                # ----------------------------

                "repository_config": {
                    "provider": "github",
                    "owner": "arjunsharma6622",
                    "repository": "cloud-infra-ai-agent-devops-test-repo",
                    "target_branch": "dev",
                },
            }

            stream = compiled_graph.astream(
                initial_state,
                config=config,
            )

        # ====================================================
        # STATUS STATE
        # ====================================================

        generation_started = False
        validation_started = False

        # ====================================================
        # PROCESS GRAPH EVENTS
        # ====================================================

        async for event in stream:

            # ------------------------------------------------
            # CLARIFICATION INTERRUPT
            # ------------------------------------------------

            if "__interrupt__" in event:

                interrupt = event[
                    "__interrupt__"
                ][0]

                clarifying_question = (
                    interrupt.value
                )

                chat_repo.save_message(
                    thread_id=thread_id,
                    role=Role.ASSISTANT,
                    message_type=MessageType.CLARIFICATION,
                    content=clarifying_question,
                )

                yield json.dumps({
                    "type": "interrupt",
                    "message": clarifying_question,
                }) + "\n"

                return

            # ------------------------------------------------
            # INTENT PARSER
            # ------------------------------------------------

            if "intent_parser" in event:

                yield json.dumps({
                    "type": "status",
                    "status": "parsing",
                    "message": "🧠 Parsing requirements...",
                }) + "\n"

            # ------------------------------------------------
            # SRS
            # ------------------------------------------------

            elif "srs_generator" in event:

                yield json.dumps({
                    "type": "status",
                    "status": "generating_srs",
                    "message": "📝 Generating SRS...",
                }) + "\n"

            # ------------------------------------------------
            # ARCHITECTURE
            # ------------------------------------------------

            elif "architecture_planner" in event:

                yield json.dumps({
                    "type": "status",
                    "status": "designing_architecture",
                    "message": "🏗️ Designing architecture...",
                }) + "\n"

            # ------------------------------------------------
            # PROJECT PLANNER
            # ------------------------------------------------

            elif "project_planner" in event:

                yield json.dumps({
                    "type": "status",
                    "status": "planning_terraform",
                    "message": "📐 Planning Terraform project...",
                }) + "\n"

            # ------------------------------------------------
            # TERRAFORM GENERATION
            # ------------------------------------------------

            elif "iac_generator" in event:

                # The generator may run many times because
                # generation is unit-by-unit and may also run
                # during repair.
                #
                # Frontend should only know that Terraform
                # generation has started.

                if not generation_started:

                    generation_started = True

                    yield json.dumps({
                        "type": "status",
                        "status": "generating_terraform",
                        "message": "💻 Generating Terraform...",
                    }) + "\n"

            # ------------------------------------------------
            # VALIDATION
            # ------------------------------------------------

            elif "validation_agent" in event:

                validator = event[
                    "validation_agent"
                ]

                validation_passed = validator.get(
                    "validation_passed",
                    False,
                )

                # First validation / subsequent validation
                # runs are intentionally hidden from frontend.

                if validation_passed:

                    yield json.dumps({
                        "type": "status",
                        "status": "validated",
                        "message": "✅ Terraform validation passed.",
                    }) + "\n"

                else:

                    yield json.dumps({
                        "type": "status",
                        "status": "validation_failed",
                        "message": (
                            "⚠️ Terraform validation failed. "
                            "Repairing and validating again..."
                        ),
                    }) + "\n"

        # ====================================================
        # GRAPH COMPLETED
        # ====================================================

        final_state = (
            await compiled_graph.aget_state(
                config
            )
        ).values

        # ----------------------------------------------------
        # Build FINAL output
        # ----------------------------------------------------

        final_output = {

            "project_spec": final_state.get(
                "project_spec",
                {},
            ),

            "srs": final_state.get(
                "srs_document",
                "",
            ),

            "architecture": final_state.get(
                "architecture_plan",
                "",
            ),

            "cloud_provider": final_state.get(
                "cloud_provider",
                "",
            ),

            "terraform_resources": final_state.get(
                "terraform_resources",
                [],
            ),

            "project_plan": final_state.get(
                "project_plan",
                {},
            ),

            "terraform": final_state.get(
                "generated_code",
                {},
            ),

            # DevOps
            "git_branch": final_state.get("git_branch", ""),
            "git_commit_id": final_state.get("git_commit_id", ""),
            "pull_request_url": final_state.get("pull_request_url", ""),
            "pull_request_id": final_state.get("pull_request_id"),
            "deployment_status": final_state.get(
                "deployment_status",
                "",
            ),
        }

        # ----------------------------------------------------
        # Save ONLY final output to chat DB
        # ----------------------------------------------------

        chat_repo.save_message(
            thread_id=thread_id,
            role=Role.ASSISTANT,
            message_type=MessageType.FINAL_OUTPUT,
            content=json.dumps(
                jsonable_encoder(
                    final_output
                )
            ),
            metadata={
                "agent": "graph_complete",
            },
        )

        # ----------------------------------------------------
        # Send final output to frontend
        # ----------------------------------------------------

        success = final_state.get(
            "validation_passed",
            False,
        )

        yield json.dumps(
            {
                "type": "complete",
                "success": success,
                "output": jsonable_encoder(
                    final_output
                ),
            }
        ) + "\n"

        print("EVENT Ended...")


    return StreamingResponse(
        event_generator(),
        media_type="application/x-ndjson",
    )