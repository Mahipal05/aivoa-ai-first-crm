from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any, Iterable, Protocol, TypeVar

from dateutil import parser as date_parser
from groq import Groq
from pydantic import BaseModel, ValidationError

from ..config import Settings
from ..schemas import (
    AgentDecision,
    DraftPatch,
    InteractionDraft,
    InteractionType,
    ReferenceContext,
    Sentiment,
    SummaryResult,
    ValidationReport,
)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMClient(Protocol):
    mode: str

    def plan_tool(
        self, history: list[dict[str, str]], user_message: str, draft: InteractionDraft
    ) -> AgentDecision: ...

    def extract_log_patch(
        self, user_message: str, draft: InteractionDraft, references: ReferenceContext
    ) -> DraftPatch: ...

    def extract_edit_patch(
        self, user_message: str, draft: InteractionDraft, references: ReferenceContext
    ) -> DraftPatch: ...

    def summarize(self, draft: InteractionDraft) -> SummaryResult: ...

    def validate(self, draft: InteractionDraft) -> ValidationReport: ...


class GroqLLMClient:
    mode = "groq"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = Groq(api_key=settings.groq_api_key)
        self.models = [settings.groq_model, *settings.groq_fallback_models]
        self.fallback = MockLLMClient()

    def _is_service_tier_error(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return "service_tier" in message and "not available" in message

    def _create_completion(self, model_name: str, system_prompt: str, user_prompt: str, schema_json: str):
        request_kwargs = {
            "model": model_name,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"{system_prompt}\n"
                        "Return a single JSON object and nothing else.\n"
                        f"Target JSON schema:\n{schema_json}"
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
        }

        if self.settings.groq_service_tier:
            request_kwargs["service_tier"] = self.settings.groq_service_tier

        try:
            return self.client.chat.completions.create(**request_kwargs)
        except Exception as exc:
            if self.settings.groq_service_tier and self._is_service_tier_error(exc):
                request_kwargs.pop("service_tier", None)
                return self.client.chat.completions.create(**request_kwargs)
            raise

    def _invoke_json(self, schema: type[SchemaT], system_prompt: str, user_prompt: str) -> SchemaT:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        last_error: Exception | None = None
        for model_name in self.models:
            try:
                completion = self._create_completion(model_name, system_prompt, user_prompt, schema_json)
                content = completion.choices[0].message.content or "{}"
                return schema.model_validate(json.loads(content))
            except (ValidationError, json.JSONDecodeError, Exception) as exc:  # noqa: PERF203
                last_error = exc
        raise RuntimeError(f"Unable to get structured response from Groq: {last_error}") from last_error

    def plan_tool(
        self, history: list[dict[str, str]], user_message: str, draft: InteractionDraft
    ) -> AgentDecision:
        history_excerpt = "\n".join(f"{item['role']}: {item['content']}" for item in history[-6:])
        try:
            return self._invoke_json(
                AgentDecision,
                system_prompt=(
                    "You are the orchestration brain for an HCP interaction logging assistant. "
                    "Select exactly one tool for the user's latest request. "
                    "Use edit_interaction for corrections, clear_form for reset requests, "
                    "summarize_interaction for summary/brief asks, validate_interaction when the user asks to check completeness, "
                    "save_interaction when the user asks to save or submit, otherwise use log_interaction."
                ),
                user_prompt=(
                    f"Conversation history:\n{history_excerpt}\n\n"
                    f"Current draft:\n{draft.model_dump_json(indent=2)}\n\n"
                    f"Latest user message:\n{user_message}"
                ),
            )
        except Exception:
            return self.fallback.plan_tool(history, user_message, draft)

    def extract_log_patch(
        self, user_message: str, draft: InteractionDraft, references: ReferenceContext
    ) -> DraftPatch:
        try:
            return self._invoke_json(
                DraftPatch,
                system_prompt=(
                    "Extract structured HCP interaction details from the user's note. "
                    "Only fill fields grounded in the note. Keep dates as YYYY-MM-DD, time as HH:MM (24-hour). "
                    "If a field is not mentioned, return null for it. "
                    "materials_shared should capture brochures, PDFs, leaflets, and reprints. "
                    "samples_distributed should capture sample kits or physical samples."
                ),
                user_prompt=(
                    f"Known HCP names: {references.hcp_names}\n"
                    f"Known material names: {references.material_names}\n"
                    f"Current draft defaults:\n{draft.model_dump_json(indent=2)}\n\n"
                    f"User note:\n{user_message}"
                ),
            )
        except Exception:
            return self.fallback.extract_log_patch(user_message, draft, references)

    def extract_edit_patch(
        self, user_message: str, draft: InteractionDraft, references: ReferenceContext
    ) -> DraftPatch:
        try:
            return self._invoke_json(
                DraftPatch,
                system_prompt=(
                    "Update only the fields explicitly changed in the correction request. "
                    "Preserve every untouched field by returning null for it. "
                    "Populate changed_fields with only the fields that should be modified."
                ),
                user_prompt=(
                    f"Known HCP names: {references.hcp_names}\n"
                    f"Known material names: {references.material_names}\n"
                    f"Current draft:\n{draft.model_dump_json(indent=2)}\n\n"
                    f"Correction request:\n{user_message}"
                ),
            )
        except Exception:
            return self.fallback.extract_edit_patch(user_message, draft, references)

    def summarize(self, draft: InteractionDraft) -> SummaryResult:
        try:
            return self._invoke_json(
                SummaryResult,
                system_prompt=(
                    "Create a concise life-sciences sales call summary and two or three follow-up suggestions. "
                    "Base the summary only on the structured draft."
                ),
                user_prompt=f"Draft:\n{draft.model_dump_json(indent=2)}",
            )
        except Exception:
            return self.fallback.summarize(draft)

    def validate(self, draft: InteractionDraft) -> ValidationReport:
        try:
            return self._invoke_json(
                ValidationReport,
                system_prompt=(
                    "Review the HCP interaction draft for completeness. "
                    "Mark it valid only if HCP name, date, time, interaction type, and at least one discussion point or outcome are present."
                ),
                user_prompt=f"Draft:\n{draft.model_dump_json(indent=2)}",
            )
        except Exception:
            return self.fallback.validate(draft)


class MockLLMClient:
    mode = "mock"

    positive_words = {"positive", "interested", "engaged", "good", "favorable", "appreciated"}
    negative_words = {"negative", "concerned", "hesitant", "unhappy", "declined", "not interested"}

    def plan_tool(
        self, history: list[dict[str, str]], user_message: str, draft: InteractionDraft
    ) -> AgentDecision:
        message = user_message.lower()
        if any(token in message for token in ["clear", "reset", "start over"]):
            return AgentDecision(tool_name="clear_form", reason="User asked to reset the form.")
        if any(token in message for token in ["summary", "summarize", "brief"]):
            return AgentDecision(tool_name="summarize_interaction", reason="User asked for a summary.")
        if any(token in message for token in ["validate", "check", "complete", "missing"]):
            return AgentDecision(tool_name="validate_interaction", reason="User asked for validation.")
        if any(token in message for token in ["save", "submit", "log it"]):
            return AgentDecision(tool_name="save_interaction", reason="User asked to save the interaction.")
        if any(token in message for token in ["change", "update", "correct", "edit", "replace"]):
            return AgentDecision(tool_name="edit_interaction", reason="User asked to modify an existing draft.")
        return AgentDecision(tool_name="log_interaction", reason="Default logging flow.")

    def extract_log_patch(
        self, user_message: str, draft: InteractionDraft, references: ReferenceContext
    ) -> DraftPatch:
        patch = DraftPatch(source_text=user_message)
        patch.hcp_name = self._find_hcp_name(user_message, references.hcp_names)
        patch.interaction_type = self._infer_interaction_type(user_message)
        patch.interaction_date = self._find_date(user_message) or None
        patch.interaction_time = self._find_time(user_message) or None
        patch.sentiment = self._infer_sentiment(user_message)
        patch.materials_shared = self._find_materials(user_message, references.material_names)
        patch.samples_distributed = self._find_samples(user_message, references.material_names)
        patch.attendees = self._find_attendees(user_message)
        patch.topics_discussed = self._extract_topic_clause(user_message, ["discussed", "covered", "spoke about"])
        patch.outcomes = self._extract_topic_clause(user_message, ["agreed", "outcome", "result", "decided"])
        patch.follow_up_actions = self._extract_actions(user_message)
        patch.changed_fields = [
            field
            for field, value in patch.model_dump(exclude={"notes", "changed_fields"}).items()
            if value not in (None, [], "")
        ]
        patch.notes = "Mock extractor used heuristic parsing."
        return patch

    def extract_edit_patch(
        self, user_message: str, draft: InteractionDraft, references: ReferenceContext
    ) -> DraftPatch:
        message = user_message.lower()
        patch = DraftPatch()
        if "sentiment" in message:
            patch.sentiment = self._infer_sentiment(user_message)
        if "date" in message:
            patch.interaction_date = self._find_date(user_message)
        if "time" in message:
            patch.interaction_time = self._find_time(user_message)
        if "hcp" in message or "doctor" in message or "dr." in message:
            patch.hcp_name = self._find_hcp_name(user_message, references.hcp_names)
        if "interaction type" in message or any(word in message for word in ["meeting", "call", "email", "conference"]):
            patch.interaction_type = self._infer_interaction_type(user_message)
        if "topic" in message or "discussion" in message:
            patch.topics_discussed = self._extract_topic_clause(
                user_message, ["topic", "topics", "discussion", "discussed"]
            )
        if "outcome" in message:
            patch.outcomes = self._extract_topic_clause(user_message, ["outcome", "result", "agreed"])
        if "follow" in message or "next step" in message:
            patch.follow_up_actions = self._extract_actions(user_message)
        if "material" in message or "brochure" in message or "leaflet" in message:
            patch.materials_shared = self._find_materials(user_message, references.material_names)
        if "sample" in message:
            patch.samples_distributed = self._find_samples(user_message, references.material_names)
        patch.changed_fields = [
            field
            for field, value in patch.model_dump(exclude={"notes", "changed_fields"}).items()
            if value not in (None, [], "")
        ]
        patch.notes = "Mock edit parser updated only detected fields."
        return patch

    def summarize(self, draft: InteractionDraft) -> SummaryResult:
        summary = (
            f"{draft.hcp_name or 'The HCP'} had a {draft.interaction_type.value.lower()} interaction. "
            f"Topics: {draft.topics_discussed or 'not captured yet'}. "
            f"Outcome: {draft.outcomes or 'pending confirmation'}."
        )
        suggestions = draft.follow_up_actions[:3] or [
            "Share the most relevant clinical material.",
            "Schedule a follow-up within two weeks.",
        ]
        return SummaryResult(ai_summary=summary, ai_suggested_follow_up=suggestions)

    def validate(self, draft: InteractionDraft) -> ValidationReport:
        missing_fields = []
        if not draft.hcp_name:
            missing_fields.append("hcp_name")
        if not draft.interaction_date:
            missing_fields.append("interaction_date")
        if not draft.interaction_time:
            missing_fields.append("interaction_time")
        if not draft.topics_discussed and not draft.outcomes:
            missing_fields.append("topics_discussed_or_outcomes")
        warnings = []
        if draft.sentiment == Sentiment.negative and not draft.follow_up_actions:
            warnings.append("Negative sentiment is captured but no follow-up action has been added.")
        return ValidationReport(
            is_valid=not missing_fields,
            missing_fields=missing_fields,
            warnings=warnings,
        )

    def _find_hcp_name(self, text: str, known_names: Iterable[str]) -> str | None:
        for name in known_names:
            if name.lower() in text.lower():
                return name
        match = re.search(r"(Dr\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
        return match.group(1) if match else None

    def _infer_interaction_type(self, text: str) -> InteractionType:
        lower = text.lower()
        if "call" in lower or "phone" in lower:
            return InteractionType.call
        if "email" in lower or "mail" in lower:
            return InteractionType.email
        if "conference" in lower or "event" in lower:
            return InteractionType.conference
        if "whatsapp" in lower or "message" in lower:
            return InteractionType.whatsapp
        return InteractionType.meeting

    def _infer_sentiment(self, text: str) -> Sentiment:
        lower = text.lower()
        if any(word in lower for word in self.negative_words):
            return Sentiment.negative
        if any(word in lower for word in self.positive_words):
            return Sentiment.positive
        return Sentiment.neutral

    def _find_date(self, text: str) -> str | None:
        lower = text.lower()
        today = datetime.now()
        if "today" in lower:
            return today.strftime("%Y-%m-%d")
        if "yesterday" in lower:
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")
        for token in re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text):
            try:
                return date_parser.parse(token, dayfirst=True).strftime("%Y-%m-%d")
            except (ValueError, OverflowError):
                continue
        return None

    def _find_time(self, text: str) -> str | None:
        match = re.search(r"\b(\d{1,2}[:.]\d{2})\b", text)
        if not match:
            return None
        return match.group(1).replace(".", ":")

    def _find_materials(self, text: str, known_materials: Iterable[str]) -> list[str]:
        matches = [name for name in known_materials if name.lower() in text.lower()]
        if "brochure" in text.lower() and "Product X efficacy brochure" not in matches:
            matches.append("Product X efficacy brochure")
        if "leaflet" in text.lower() and "Patient support leaflet" not in matches:
            matches.append("Patient support leaflet")
        if "reprint" in text.lower() and "Phase III clinical reprint" not in matches:
            matches.append("Phase III clinical reprint")
        return matches

    def _find_samples(self, text: str, known_materials: Iterable[str]) -> list[str]:
        matches = [name for name in known_materials if "sample" in name.lower() and name.lower() in text.lower()]
        if "sample" in text.lower() and not matches:
            matches.append("Starter sample kit")
        return matches

    def _find_attendees(self, text: str) -> list[str]:
        names = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b", text)
        return [name for name in names if not name.startswith("Dr")][:3]

    def _extract_topic_clause(self, text: str, anchors: list[str]) -> str | None:
        lower = text.lower()
        for anchor in anchors:
            if anchor in lower:
                idx = lower.index(anchor)
                snippet = text[idx:]
                return snippet[:160].strip(" ,.-")
        return None

    def _extract_actions(self, text: str) -> list[str]:
        lower = text.lower()
        actions = []
        if "follow" in lower:
            actions.append("Schedule a follow-up discussion.")
        if "send" in lower or "share" in lower:
            actions.append("Send the agreed material to the HCP.")
        if "sample" in lower:
            actions.append("Confirm sample dispatch with the field team.")
        return actions


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.groq_api_key:
        return GroqLLMClient(settings)
    return MockLLMClient()
