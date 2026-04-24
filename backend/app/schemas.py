from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class InteractionType(str, Enum):
    meeting = "Meeting"
    call = "Call"
    email = "Email"
    conference = "Conference"
    whatsapp = "WhatsApp"


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class ChatRole(str, Enum):
    assistant = "assistant"
    user = "user"


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: ChatRole
    content: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ToolEvent(BaseModel):
    tool_name: str
    status: Literal["success", "warning", "error"] = "success"
    summary: str
    changed_fields: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ValidationReport(BaseModel):
    is_valid: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class HCPSummary(BaseModel):
    id: int
    name: str
    specialty: str
    organization: str
    city: str
    territory: str


class MaterialSummary(BaseModel):
    id: int
    name: str
    material_type: str


class InteractionDraft(BaseModel):
    hcp_name: str = ""
    interaction_type: InteractionType = InteractionType.meeting
    interaction_date: str = ""
    interaction_time: str = ""
    attendees: list[str] = Field(default_factory=list)
    topics_discussed: str = ""
    materials_shared: list[str] = Field(default_factory=list)
    samples_distributed: list[str] = Field(default_factory=list)
    sentiment: Sentiment = Sentiment.neutral
    outcomes: str = ""
    follow_up_actions: list[str] = Field(default_factory=list)
    ai_suggested_follow_up: list[str] = Field(default_factory=list)
    ai_summary: str = ""
    source_text: str = ""


class DraftPatch(BaseModel):
    hcp_name: str | None = None
    interaction_type: InteractionType | None = None
    interaction_date: str | None = None
    interaction_time: str | None = None
    attendees: list[str] | None = None
    topics_discussed: str | None = None
    materials_shared: list[str] | None = None
    samples_distributed: list[str] | None = None
    sentiment: Sentiment | None = None
    outcomes: str | None = None
    follow_up_actions: list[str] | None = None
    ai_suggested_follow_up: list[str] | None = None
    ai_summary: str | None = None
    source_text: str | None = None
    changed_fields: list[str] = Field(default_factory=list)
    notes: str = ""


class AgentDecision(BaseModel):
    tool_name: Literal[
        "log_interaction",
        "edit_interaction",
        "clear_form",
        "summarize_interaction",
        "validate_interaction",
        "save_interaction",
    ]
    reason: str = ""


class SummaryResult(BaseModel):
    ai_summary: str = ""
    ai_suggested_follow_up: list[str] = Field(default_factory=list)


class SessionSnapshot(BaseModel):
    session_id: str
    draft: InteractionDraft
    messages: list[ChatMessage]
    validation: ValidationReport
    tool_events: list[ToolEvent]
    last_saved_interaction_id: int | None = None
    llm_mode: str
    hcps: list[HCPSummary] = Field(default_factory=list)
    materials: list[MaterialSummary] = Field(default_factory=list)


class BootstrapRequest(BaseModel):
    session_id: str | None = None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    session_id: str
    assistant_message: ChatMessage
    draft: InteractionDraft
    validation: ValidationReport
    tool_events: list[ToolEvent]
    last_saved_interaction_id: int | None = None
    llm_mode: str


class SessionResponse(SessionSnapshot):
    pass


class InteractionRecord(BaseModel):
    id: int
    hcp_name: str
    interaction_type: str
    interaction_date: str | None
    sentiment: str
    topics_discussed: str
    ai_summary: str


class InteractionListResponse(BaseModel):
    items: list[InteractionRecord]


class ToolExecutionResult(BaseModel):
    draft: InteractionDraft
    validation: ValidationReport
    tool_event: ToolEvent
    assistant_message: str
    last_saved_interaction_id: int | None = None


class ReferenceContext(BaseModel):
    hcp_names: list[str] = Field(default_factory=list)
    material_names: list[str] = Field(default_factory=list)


class InteractionDraftState(BaseModel):
    history: list[ChatMessage] = Field(default_factory=list)
    latest_user_message: str
    draft: InteractionDraft
    selected_tool: str = "log_interaction"
    planner_reason: str = ""
    tool_result: dict[str, Any] = Field(default_factory=dict)
    assistant_message: str = ""
    validation: ValidationReport = Field(default_factory=ValidationReport)
    last_saved_interaction_id: int | None = None
