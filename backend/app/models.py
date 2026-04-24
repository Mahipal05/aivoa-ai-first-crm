from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class HCP(TimestampMixin, Base):
    __tablename__ = "hcps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    specialty: Mapped[str] = mapped_column(String(120), nullable=False)
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    territory: Mapped[str] = mapped_column(String(120), nullable=False)

    interactions: Mapped[list["Interaction"]] = relationship(back_populates="hcp")


class Material(TimestampMixin, Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    material_type: Mapped[str] = mapped_column(String(120), nullable=False)


class Interaction(TimestampMixin, Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    hcp_id: Mapped[int | None] = mapped_column(ForeignKey("hcps.id"), nullable=True)
    hcp_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    interaction_type: Mapped[str] = mapped_column(String(80), nullable=False)
    interaction_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    interaction_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    attendees: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    topics_discussed: Mapped[str] = mapped_column(Text, default="", nullable=False)
    materials_shared: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    samples_distributed: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(30), default="neutral", nullable=False)
    outcomes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    follow_up_actions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    ai_suggested_follow_up: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    ai_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    validation_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    hcp: Mapped[HCP | None] = relationship(back_populates="interactions")
    audits: Mapped[list["InteractionAudit"]] = relationship(back_populates="interaction")


class InteractionAudit(TimestampMixin, Base):
    __tablename__ = "interaction_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    interaction_id: Mapped[int] = mapped_column(ForeignKey("interactions.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    changed_fields: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    interaction: Mapped[Interaction] = relationship(back_populates="audits")


class SessionState(TimestampMixin, Base):
    __tablename__ = "session_states"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    messages: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    draft: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    validation: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    tool_events: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    last_saved_interaction_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
