"""统一 Web 应用；知识管理已实现，对话页面和接口仍为 TODO。"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from knowledge.errors import KnowledgeError
from knowledge.repository import initialize
from web.routes import router

@asynccontextmanager
async def lifespan(app):
    initialize()
    yield

app = FastAPI(title='Fermata — 通用 Agent', lifespan=lifespan)
app.include_router(router)

@app.exception_handler(KnowledgeError)
async def knowledge_error(request: Request, exc: KnowledgeError):
    return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail})

@app.get('/')
def home():
    return FileResponse(Path(__file__).parent / 'templates/knowledge.html')

# TODO: 对话接口和页面接入 agent.runtime，待 Agent 主流程完成后实现。
