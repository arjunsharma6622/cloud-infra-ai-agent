from fastapi import APIRouter, Request, Depends, HTTPException
import json
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from app.database.chat_repository import ChatRepository
from app.database.constants import Role, MessageType
from app.schemas import ChatRequest
from fastapi.encoders import jsonable_encoder

from app.agents.services.get_tf_docs import get_terraform_docs

chat_repo = ChatRepository()

router = APIRouter()

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

                "architecture_plan": "",
                "cloud_provider": "",
                "terraform_resources": [],

                "validation_attempts": 0,
                "validation_passed": False,
                "validation_errors": [],
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
                        "cloud_provider": final_state.get("cloud_provider"),
                        "terraform_resources": final_state.get("terraform_resources"),
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



@router.get("/get-resource-docs")
async def get_resource_docs():
    resources = [
    "azurerm_resource_group",
    "azurerm_virtual_network",
    "azurerm_subnet",
    "azurerm_network_security_group",
    "azurerm_linux_virtual_machine_scale_set",
    "azurerm_lb",
    "azurerm_lb_backend_address_pool",
    "azurerm_lb_probe",
    "azurerm_lb_rule",
    "azurerm_postgresql_flexible_server",
    "azurerm_postgresql_flexible_server_configuration",
    "azurerm_postgresql_flexible_server_database",
    "azurerm_bastion_host",
    "azurerm_key_vault",
    "azurerm_key_vault_secret",
    "azurerm_log_analytics_workspace",
    "azurerm_storage_account",
    "azurerm_private_endpoint",
    "azurerm_user_assigned_identity",
    ]
    docs = get_terraform_docs(
        cloud_provider="azurerm",
        terraform_types=resources
    )

    return docs
