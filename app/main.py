from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from app.agents.graph import create_graph
from app.database.schema import init_db
import shutil
from app.api.routes import router as api_router

app = FastAPI(title="Infra AI Agent")

app.include_router(api_router)

@app.on_event("startup")
async def startup():

    init_db()

    # adding compiled graph to the fastapi state
    app.state.compiled_graph = await create_graph()

    if shutil.which("terraform") is None:
        raise RuntimeError("Terraform executable not found.")
