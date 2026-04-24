from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .agent.graph import InteractionAgent
from .agent.llm import build_llm_client
from .config import get_settings
from .database import Base, SessionLocal, engine, get_db
from .schemas import (
    BootstrapRequest,
    ChatRequest,
    ChatResponse,
    InteractionListResponse,
    SessionResponse,
)
from .seed import seed_reference_data
from .services import CRMService


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.seed_on_startup:
        db = SessionLocal()
        try:
            seed_reference_data(db)
        finally:
            db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_service(db: Session = Depends(get_db)) -> CRMService:
    return CRMService(db)


@app.get("/health")
def health_check():
    return {"status": "ok", "llm_mode": "groq" if settings.groq_api_key else "mock"}


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "bootstrap": f"{settings.api_v1_prefix}/bootstrap",
        "note": "Open the React UI at http://localhost:5173 and keep this backend terminal running.",
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return {}


@app.get(f"{settings.api_v1_prefix}")
@app.get(f"{settings.api_v1_prefix}/")
def api_root():
    return {
        "name": settings.app_name,
        "status": "running",
        "message": "This is the API base path. Use the listed endpoints or open the React UI at http://localhost:5173.",
        "endpoints": {
            "bootstrap_get": f"{settings.api_v1_prefix}/bootstrap",
            "bootstrap_post": f"{settings.api_v1_prefix}/bootstrap",
            "session": f"{settings.api_v1_prefix}/sessions/{{session_id}}",
            "chat": f"{settings.api_v1_prefix}/sessions/{{session_id}}/chat",
            "interactions": f"{settings.api_v1_prefix}/interactions",
            "health": "/health",
            "docs": "/docs",
        },
    }


@app.post(f"{settings.api_v1_prefix}/bootstrap", response_model=SessionResponse)
def bootstrap(payload: BootstrapRequest | None = None, service: CRMService = Depends(get_service)):
    snapshot = service.create_or_get_session(payload.session_id if payload else None)
    snapshot.llm_mode = "groq" if settings.groq_api_key else "mock"
    return snapshot


@app.get(f"{settings.api_v1_prefix}/bootstrap", response_model=SessionResponse)
def bootstrap_get(service: CRMService = Depends(get_service)):
    snapshot = service.create_or_get_session()
    snapshot.llm_mode = "groq" if settings.groq_api_key else "mock"
    return snapshot


@app.get(f"{settings.api_v1_prefix}/sessions/{{session_id}}", response_model=SessionResponse)
def get_session(session_id: str, service: CRMService = Depends(get_service)):
    snapshot = service.get_session(session_id)
    snapshot.llm_mode = "groq" if settings.groq_api_key else "mock"
    return snapshot


@app.post(f"{settings.api_v1_prefix}/sessions/{{session_id}}/chat", response_model=ChatResponse)
def chat_with_assistant(
    session_id: str,
    payload: ChatRequest,
    service: CRMService = Depends(get_service),
):
    snapshot = service.get_session(session_id)
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    agent = InteractionAgent(build_llm_client(settings), service)
    result = agent.process_turn(snapshot.messages, snapshot.draft.model_dump(mode="json"), payload.message.strip())
    tool_events = [*snapshot.tool_events[-4:], result["tool_event"]]
    persisted = service.save_session_snapshot(
        session_id=session_id,
        draft=result["draft"],
        messages=result["messages"],
        validation=result["validation"],
        tool_events=tool_events,
        last_saved_interaction_id=result["last_saved_interaction_id"] or snapshot.last_saved_interaction_id,
        llm_mode=agent.llm.mode,
    )
    return ChatResponse(
        session_id=session_id,
        assistant_message=result["assistant_message"],
        draft=persisted.draft,
        validation=persisted.validation,
        tool_events=persisted.tool_events,
        last_saved_interaction_id=persisted.last_saved_interaction_id,
        llm_mode=agent.llm.mode,
    )


@app.get(f"{settings.api_v1_prefix}/interactions", response_model=InteractionListResponse)
def list_interactions(service: CRMService = Depends(get_service)):
    return InteractionListResponse(items=service.list_recent_interactions())
