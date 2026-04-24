from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from .models import HCP, Interaction, InteractionAudit, Material, SessionState
from .schemas import (
    ChatMessage,
    HCPSummary,
    InteractionDraft,
    InteractionRecord,
    MaterialSummary,
    SessionSnapshot,
    ToolEvent,
    ValidationReport,
)


class CRMService:
    def __init__(self, db: Session):
        self.db = db

    def default_draft(self) -> InteractionDraft:
        now = datetime.now()
        return InteractionDraft(
            interaction_date=now.strftime("%Y-%m-%d"),
            interaction_time=now.strftime("%H:%M"),
        )

    def welcome_message(self) -> ChatMessage:
        return ChatMessage(
            role="assistant",
            content=(
                "Describe the HCP interaction in natural language and I will populate the form, "
                "validate it, and save it when you ask."
            ),
        )

    def list_hcps(self) -> list[HCPSummary]:
        items = self.db.query(HCP).order_by(HCP.name.asc()).all()
        return [HCPSummary.model_validate(item, from_attributes=True) for item in items]

    def list_materials(self) -> list[MaterialSummary]:
        items = self.db.query(Material).order_by(Material.name.asc()).all()
        return [MaterialSummary.model_validate(item, from_attributes=True) for item in items]

    def create_or_get_session(self, session_id: str | None = None) -> SessionSnapshot:
        session = self.db.get(SessionState, session_id) if session_id else None
        if session is None:
            session = SessionState(
                session_id=session_id or str(uuid4()),
                messages=[self.welcome_message().model_dump()],
                draft=self.default_draft().model_dump(mode="json"),
                validation=ValidationReport().model_dump(),
                tool_events=[],
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
        return self._to_snapshot(session)

    def get_session(self, session_id: str) -> SessionSnapshot:
        session = self.db.get(SessionState, session_id)
        if session is None:
            return self.create_or_get_session(session_id=session_id)
        return self._to_snapshot(session)

    def save_session_snapshot(
        self,
        session_id: str,
        draft: InteractionDraft,
        messages: list[ChatMessage],
        validation: ValidationReport,
        tool_events: list[ToolEvent],
        last_saved_interaction_id: int | None,
        llm_mode: str,
    ) -> SessionSnapshot:
        session = self.db.get(SessionState, session_id)
        if session is None:
            session = SessionState(session_id=session_id)
            self.db.add(session)
        session.draft = draft.model_dump(mode="json")
        session.messages = [message.model_dump() for message in messages]
        session.validation = validation.model_dump()
        session.tool_events = [event.model_dump() for event in tool_events]
        session.last_saved_interaction_id = last_saved_interaction_id
        self.db.commit()
        self.db.refresh(session)
        snapshot = self._to_snapshot(session)
        snapshot.llm_mode = llm_mode
        return snapshot

    def resolve_hcp_id(self, hcp_name: str) -> int | None:
        if not hcp_name.strip():
            return None
        match = (
            self.db.query(HCP)
            .filter(HCP.name.ilike(hcp_name.strip()))
            .one_or_none()
        )
        return match.id if match else None

    def save_interaction(self, draft: InteractionDraft, validation: ValidationReport, event_type: str) -> int:
        interaction = Interaction(
            hcp_id=self.resolve_hcp_id(draft.hcp_name),
            hcp_name=draft.hcp_name,
            interaction_type=draft.interaction_type.value,
            interaction_date=datetime.strptime(draft.interaction_date, "%Y-%m-%d").date()
            if draft.interaction_date
            else None,
            interaction_time=datetime.strptime(draft.interaction_time, "%H:%M").time()
            if draft.interaction_time
            else None,
            attendees=draft.attendees,
            topics_discussed=draft.topics_discussed,
            materials_shared=draft.materials_shared,
            samples_distributed=draft.samples_distributed,
            sentiment=draft.sentiment.value,
            outcomes=draft.outcomes,
            follow_up_actions=draft.follow_up_actions,
            ai_suggested_follow_up=draft.ai_suggested_follow_up,
            ai_summary=draft.ai_summary,
            source_text=draft.source_text,
            validation_snapshot=validation.model_dump(),
        )
        self.db.add(interaction)
        self.db.commit()
        self.db.refresh(interaction)

        audit = InteractionAudit(
            interaction_id=interaction.id,
            event_type=event_type,
            changed_fields=["*"],
            payload=draft.model_dump(mode="json"),
        )
        self.db.add(audit)
        self.db.commit()
        return interaction.id

    def list_recent_interactions(self, limit: int = 8) -> list[InteractionRecord]:
        items = (
            self.db.query(Interaction)
            .order_by(Interaction.updated_at.desc())
            .limit(limit)
            .all()
        )
        return [
            InteractionRecord(
                id=item.id,
                hcp_name=item.hcp_name,
                interaction_type=item.interaction_type,
                interaction_date=item.interaction_date.isoformat() if item.interaction_date else None,
                sentiment=item.sentiment,
                topics_discussed=item.topics_discussed,
                ai_summary=item.ai_summary,
            )
            for item in items
        ]

    def _to_snapshot(self, session: SessionState) -> SessionSnapshot:
        return SessionSnapshot(
            session_id=session.session_id,
            draft=InteractionDraft.model_validate(session.draft or self.default_draft().model_dump()),
            messages=[ChatMessage.model_validate(item) for item in (session.messages or [])],
            validation=ValidationReport.model_validate(session.validation or {}),
            tool_events=[ToolEvent.model_validate(item) for item in (session.tool_events or [])],
            last_saved_interaction_id=session.last_saved_interaction_id,
            llm_mode="mock",
            hcps=self.list_hcps(),
            materials=self.list_materials(),
        )
