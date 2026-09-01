from fastapi import APIRouter, Request, Depends, HTTPException
import json

from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.database.chat_repository import ChatRepository
from app.database.constants import Role, MessageType
from app.schemas import ChatRequest, TerraformInputsRequest


chat_repo = ChatRepository()

router = APIRouter()


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
async def get_chat_history(
    thread_id: str,
    compiled_graph=Depends(get_graph),
):
    messages = chat_repo.get_messages(thread_id)

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    snapshot = await compiled_graph.aget_state(config)

    response = {
        "messages": messages
    }

    # --------------------------------------------------------
    # Check if the graph is currently waiting for input
    # --------------------------------------------------------

    if snapshot.next:
        terraform_input_request = None

        for task in snapshot.tasks:
            interrupts = getattr(task, "interrupts", [])

            for interrupt_event in interrupts:
                value = getattr(
                    interrupt_event,
                    "value",
                    None,
                )

                if (
                    isinstance(value, dict)
                    and value.get("type")
                    == "terraform_inputs_required"
                ):
                    terraform_input_request = {
                        "type": "terraform_inputs_required",
                        "variables": value.get("variables", []),
                    }
                    break

            if terraform_input_request:
                break

        # ----------------------------------------------------
        # Return the SAME structure that /stream returns
        # ----------------------------------------------------

        if terraform_input_request:
            response["terraform_inputs_required"] = (
                terraform_input_request
            )

    return response


async def process_graph_stream(
    stream,
    thread_id: str,
    compiled_graph,
):
    generation_started = False

    async for event in stream:

        # ====================================================
        # INTERRUPTS
        # ====================================================

        if "__interrupt__" in event:

            interrupt_event = event[
                "__interrupt__"
            ][0]

            value = interrupt_event.value

            # ----------------------------------------------
            # Terraform inputs
            # ----------------------------------------------

            if (
                isinstance(value, dict)
                and value.get("type")
                == "terraform_inputs_required"
            ):

                yield json.dumps({
                    "type": (
                        "terraform_inputs_required"
                    ),
                    "variables": value[
                        "variables"
                    ],
                }) + "\n"

                return

            # ----------------------------------------------
            # Normal clarification
            # ----------------------------------------------

            chat_repo.save_message(
                thread_id=thread_id,
                role=Role.ASSISTANT,
                message_type=(
                    MessageType.CLARIFICATION
                ),
                content=value,
            )

            yield json.dumps({
                "type": "interrupt",
                "message": value,
            }) + "\n"

            return

        # ====================================================
        # INTENT
        # ====================================================

        if "intent_parser" in event:

            yield json.dumps({
                "type": "status",
                "status": "parsing",
                "message": (
                    "🧠 Parsing requirements..."
                ),
            }) + "\n"

        # ====================================================
        # SRS
        # ====================================================

        elif "srs_generator" in event:

            yield json.dumps({
                "type": "status",
                "status": "generating_srs",
                "message": (
                    "📝 Generating SRS..."
                ),
            }) + "\n"

        # ====================================================
        # ARCHITECTURE
        # ====================================================

        elif "architecture_planner" in event:

            yield json.dumps({
                "type": "status",
                "status": (
                    "designing_architecture"
                ),
                "message": (
                    "🏗️ Designing architecture..."
                ),
            }) + "\n"

        # ====================================================
        # PROJECT PLANNER
        # ====================================================

        elif "project_planner" in event:

            yield json.dumps({
                "type": "status",
                "status": "planning_terraform",
                "message": (
                    "📐 Planning Terraform project..."
                ),
            }) + "\n"

        # ====================================================
        # TERRAFORM GENERATION
        # ====================================================

        elif "iac_generator" in event:

            if not generation_started:

                generation_started = True

                yield json.dumps({
                    "type": "status",
                    "status": (
                        "generating_terraform"
                    ),
                    "message": (
                        "💻 Generating Terraform..."
                    ),
                }) + "\n"

        # ====================================================
        # VALIDATION
        # ====================================================

        elif "validation_agent" in event:

            validator = event[
                "validation_agent"
            ]

            validation_passed = validator.get(
                "validation_passed",
                False,
            )

            if validation_passed:

                yield json.dumps({
                    "type": "status",
                    "status": "validated",
                    "message": (
                        "✅ Terraform validation passed."
                    ),
                }) + "\n"

            else:

                yield json.dumps({
                    "type": "status",
                    "status": (
                        "validation_failed"
                    ),
                    "message": (
                        "⚠️ Terraform validation failed. "
                        "Repairing and validating again..."
                    ),
                }) + "\n"

        # ====================================================
        # REPOSITORY
        # ====================================================

        elif "repo_bootstrap" in event:

            yield json.dumps({
                "type": "status",
                "status": "repo_bootstrapped",
                "message": (
                    "📦 Repository created."
                ),
            }) + "\n"

        # ====================================================
        # TERRAFORM INPUT CONFIGURATION
        # ====================================================

        elif "terraform_inputs" in event:

            yield json.dumps({
                "type": "status",
                "status": (
                    "configuring_github"
                ),
                "message": (
                    "🔐 Configuring GitHub "
                    "secrets and variables..."
                ),
            }) + "\n"

        # ====================================================
        # CREATE PR
        # ====================================================

        elif "create_pr" in event:

            yield json.dumps({
                "type": "status",
                "status": "creating_pr",
                "message": (
                    "🚀 Creating infrastructure PR..."
                ),
            }) + "\n"

    # ============================================================
    # GRAPH COMPLETED
    # ============================================================

    final_state = (
        await compiled_graph.aget_state(
            {
                "configurable": {
                    "thread_id": thread_id,
                }
            }
        )
    ).values

    # ------------------------------------------------------------
    # Build final output
    # ------------------------------------------------------------

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

        # Terraform inputs
        "terraform_inputs": final_state.get(
            "terraform_inputs",
            [],
        ),

        "terraform_inputs_status": final_state.get(
            "terraform_inputs_status",
            {},
        ),

        # DevOps
        "git_branch": final_state.get(
            "git_branch",
            "",
        ),

        "git_commit_id": final_state.get(
            "git_commit_id",
            "",
        ),

        "pull_request_url": final_state.get(
            "pull_request_url",
            "",
        ),

        "pull_request_id": final_state.get(
            "pull_request_id",
        ),

        "deployment_status": final_state.get(
            "deployment_status",
            "",
        ),

        "deployment_error": final_state.get(
            "deployment_error",
        ),
    }

    # ------------------------------------------------------------
    # Save final assistant message
    # ------------------------------------------------------------

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

    # ------------------------------------------------------------
    # Send final output to frontend
    # ------------------------------------------------------------

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




# ============================================================
# STREAM
# ============================================================

@router.post(
    "/stream",
    tags=["Agent Stream"],
)
async def stream_assistant(
    request: ChatRequest,
    compiled_graph=Depends(get_graph),
):

    thread_id = request.thread_id

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    user_prompt = request.prompt

    chat_repo.create_project(
        thread_id=thread_id,
        title=f"Proj-{thread_id[:8]}",
    )

    chat_repo.save_message(
        thread_id=thread_id,
        role=Role.USER,
        message_type=MessageType.TEXT,
        content=user_prompt,
    )

    snapshot = await compiled_graph.aget_state(
        config
    )

    # --------------------------------------------------------
    # Existing interrupted graph
    # --------------------------------------------------------

    if snapshot.next:

        terraform_interrupt = False

        for task in snapshot.tasks:

            interrupts = getattr(
                task,
                "interrupts",
                [],
            )

            for interrupt_event in interrupts:

                value = getattr(
                    interrupt_event,
                    "value",
                    None,
                )

                if (
                    isinstance(value, dict)
                    and value.get("type")
                    == "terraform_inputs_required"
                ):
                    terraform_interrupt = True
                    break

            if terraform_interrupt:
                break

        # ----------------------------------------------------
        # Terraform input interrupt
        # ----------------------------------------------------

        if terraform_interrupt:

            raise HTTPException(
                status_code=409,
                detail={
                    "code": "TERRAFORM_INPUTS_REQUIRED",
                    "message": (
                        "This project is waiting for "
                        "Terraform inputs."
                    ),
                },
            )

        # ----------------------------------------------------
        # Otherwise this is the normal clarification
        # interrupt.
        #
        # /stream is allowed to resume it.
        # ----------------------------------------------------

    if snapshot.next:

    # ----------------------------------------------------
    # Existing clarification interrupt
    # ----------------------------------------------------

        stream = compiled_graph.astream(
            Command(
                resume=user_prompt
            ),
            config=config,
        )

    else:

        initial_state = {

            "thread_id": thread_id,

            "messages": [
                HumanMessage(
                    content=user_prompt
                )
            ],

            "clarification_question": None,

            # Requirements
            "project_spec": {},
            "srs_document": "",

            # Architecture
            "architecture_plan": "",
            "cloud_provider": "",
            "terraform_resources": [],

            # Project planning
            "project_plan": {},

            # Generation
            "current_generation_unit": None,
            "generation_unit_index": 0,
            "generated_units": {},
            "generated_code": {},
            "generation_prompt": "",
            "generation_mode": "initial",

            # Repair
            "units_to_regenerate": [],
            "current_repair_index": 0,

            # Validation
            "validation_run_id": "",
            "validation_stage": "",
            "validation_passed": False,
            "validation_errors": [],
            "validation_attempts": 0,

            # Terraform inputs
            "terraform_inputs": [],
            "terraform_inputs_status": {},

            # DevOps
            "repo_config": {
                "provider": "github",
                "owner": "arjunsharma6622-temp1",
            },

            "git_branch": "",
            "git_commit_id": "",
            "pull_request_url": "",
            "pull_request_id": "",
            "deployment_status": "",
            "deployment_error": None,
        }

        stream = compiled_graph.astream(
            initial_state,
            config=config,
        )

    return StreamingResponse(
        process_graph_stream(
            stream,
            thread_id,
            compiled_graph=compiled_graph
        ),
        media_type="application/x-ndjson",
    )


# terraform inputs post

@router.post(
    "/project/{thread_id}/terraform-inputs",
    tags=["Terraform"],
)
async def submit_terraform_inputs(
    thread_id: str,
    request: TerraformInputsRequest,
    compiled_graph=Depends(get_graph),
):

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    # ========================================================
    # Verify checkpoint / interrupted state
    # ========================================================

    snapshot = await compiled_graph.aget_state(
        config
    )

    if not snapshot.next:

        raise HTTPException(
            status_code=409,
            detail=(
                "Project is not waiting for "
                "Terraform inputs."
            ),
        )

    # ========================================================
    # Verify the current interrupt is Terraform input
    # ========================================================

    tasks = snapshot.tasks

    terraform_interrupt = False

    for task in tasks:

        interrupts = getattr(
            task,
            "interrupts",
            [],
        )

        for interrupt_event in interrupts:

            value = getattr(
                interrupt_event,
                "value",
                None,
            )

            if (
                isinstance(value, dict)
                and value.get("type")
                == "terraform_inputs_required"
            ):

                terraform_interrupt = True
                break

        if terraform_interrupt:
            break

    if not terraform_interrupt:

        raise HTTPException(
            status_code=409,
            detail=(
                "Project is waiting for a different "
                "type of input."
            ),
        )

    # ========================================================
    # Resume graph
    # ========================================================

    stream = compiled_graph.astream(
        Command(
            resume={
                "values": request.values,
            }
        ),
        config=config,
    )

    return StreamingResponse(
        process_graph_stream(
            stream,
            thread_id,
            compiled_graph=compiled_graph
        ),
        media_type="application/x-ndjson",
    )

