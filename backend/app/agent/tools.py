from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from ..schemas import InteractionDraft, ReferenceContext, ToolEvent, ToolExecutionResult
from ..services import CRMService
from .llm import LLMClient


def _merge_draft(current: InteractionDraft, patch: dict[str, Any]) -> InteractionDraft:
    update_payload = {
        key: value
        for key, value in patch.items()
        if key in type(current).model_fields and value is not None
    }
    return current.model_copy(update=update_payload)


def build_tools(llm: LLMClient, service: CRMService) -> dict[str, Any]:
    references = ReferenceContext(
        hcp_names=[item.name for item in service.list_hcps()],
        material_names=[item.name for item in service.list_materials()],
    )

    @tool("log_interaction")
    def log_interaction(latest_user_message: str, draft: dict[str, Any]) -> dict[str, Any]:
        """Extract structured data from natural language and populate the form draft."""

        current = InteractionDraft.model_validate(draft)
        patch = llm.extract_log_patch(latest_user_message, current, references)
        updated = _merge_draft(current, patch.model_dump())
        validation = llm.validate(updated)
        event = ToolEvent(
            tool_name="log_interaction",
            summary="Interaction details were extracted from the chat and applied to the form.",
            changed_fields=patch.changed_fields,
            status="success",
        )
        return ToolExecutionResult(
            draft=updated,
            validation=validation,
            tool_event=event,
            assistant_message=(
                f"I populated the form for {updated.hcp_name or 'the HCP'} and captured "
                f"{', '.join(patch.changed_fields) if patch.changed_fields else 'the available details'}."
            ),
        ).model_dump(mode="json")

    @tool("edit_interaction")
    def edit_interaction(latest_user_message: str, draft: dict[str, Any]) -> dict[str, Any]:
        """Apply partial field updates while preserving every unmentioned field."""

        current = InteractionDraft.model_validate(draft)
        patch = llm.extract_edit_patch(latest_user_message, current, references)
        updated = _merge_draft(current, patch.model_dump())
        validation = llm.validate(updated)
        event = ToolEvent(
            tool_name="edit_interaction",
            summary="Requested corrections were applied without touching unrelated fields.",
            changed_fields=patch.changed_fields,
            status="success",
        )
        changed = ", ".join(patch.changed_fields) if patch.changed_fields else "the requested field"
        return ToolExecutionResult(
            draft=updated,
            validation=validation,
            tool_event=event,
            assistant_message=f"I updated {changed} and left the rest of the form untouched.",
        ).model_dump(mode="json")

    @tool("clear_form")
    def clear_form(latest_user_message: str, draft: dict[str, Any]) -> dict[str, Any]:
        """Reset the form draft back to its default empty state."""

        updated = service.default_draft()
        validation = llm.validate(updated)
        event = ToolEvent(
            tool_name="clear_form",
            summary="The form was cleared and reset to default date/time values.",
            changed_fields=["*"],
            status="success",
        )
        return ToolExecutionResult(
            draft=updated,
            validation=validation,
            tool_event=event,
            assistant_message="The draft has been cleared. You can describe a new interaction whenever you're ready.",
        ).model_dump(mode="json")

    @tool("summarize_interaction")
    def summarize_interaction(latest_user_message: str, draft: dict[str, Any]) -> dict[str, Any]:
        """Generate an AI summary and suggested next steps from the current form state."""

        current = InteractionDraft.model_validate(draft)
        summary = llm.summarize(current)
        updated = current.model_copy(
            update={
                "ai_summary": summary.ai_summary,
                "ai_suggested_follow_up": summary.ai_suggested_follow_up,
            }
        )
        validation = llm.validate(updated)
        event = ToolEvent(
            tool_name="summarize_interaction",
            summary="An AI summary and follow-up recommendations were added to the draft.",
            changed_fields=["ai_summary", "ai_suggested_follow_up"],
            status="success",
        )
        return ToolExecutionResult(
            draft=updated,
            validation=validation,
            tool_event=event,
            assistant_message=summary.ai_summary,
        ).model_dump(mode="json")

    @tool("validate_interaction")
    def validate_interaction(latest_user_message: str, draft: dict[str, Any]) -> dict[str, Any]:
        """Check the form for missing fields, ambiguities, and save readiness."""

        current = InteractionDraft.model_validate(draft)
        validation = llm.validate(current)
        event = ToolEvent(
            tool_name="validate_interaction",
            summary="The current draft was checked for completeness.",
            changed_fields=[],
            status="warning" if not validation.is_valid else "success",
        )
        if validation.is_valid:
            message = "The form is complete and ready to save."
        else:
            message = f"The form still needs: {', '.join(validation.missing_fields)}."
        return ToolExecutionResult(
            draft=current,
            validation=validation,
            tool_event=event,
            assistant_message=message,
        ).model_dump(mode="json")

    @tool("save_interaction")
    def save_interaction(latest_user_message: str, draft: dict[str, Any]) -> dict[str, Any]:
        """Persist the current interaction draft to the SQL database when it is valid."""

        current = InteractionDraft.model_validate(draft)
        if not current.ai_summary:
            summary = llm.summarize(current)
            current = current.model_copy(
                update={
                    "ai_summary": summary.ai_summary,
                    "ai_suggested_follow_up": summary.ai_suggested_follow_up,
                }
            )
        validation = llm.validate(current)
        if not validation.is_valid:
            event = ToolEvent(
                tool_name="save_interaction",
                summary="Save was blocked because required fields are missing.",
                changed_fields=[],
                status="warning",
            )
            return ToolExecutionResult(
                draft=current,
                validation=validation,
                tool_event=event,
                assistant_message=(
                    "I did not save the interaction yet because the draft is incomplete. "
                    f"Missing: {', '.join(validation.missing_fields)}."
                ),
            ).model_dump(mode="json")

        interaction_id = service.save_interaction(current, validation, "saved_via_ai_assistant")
        event = ToolEvent(
            tool_name="save_interaction",
            summary=f"Interaction #{interaction_id} was saved to the database.",
            changed_fields=[],
            status="success",
        )
        return ToolExecutionResult(
            draft=current,
            validation=validation,
            tool_event=event,
            assistant_message=f"The interaction has been saved successfully as record #{interaction_id}.",
            last_saved_interaction_id=interaction_id,
        ).model_dump(mode="json")

    return {
        "log_interaction": log_interaction,
        "edit_interaction": edit_interaction,
        "clear_form": clear_form,
        "summarize_interaction": summarize_interaction,
        "validate_interaction": validate_interaction,
        "save_interaction": save_interaction,
    }
