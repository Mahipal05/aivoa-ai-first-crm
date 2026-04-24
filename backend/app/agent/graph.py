from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ..schemas import ChatMessage, ChatRole, InteractionDraft, ToolExecutionResult
from ..services import CRMService
from .llm import LLMClient
from .tools import build_tools


class GraphState(TypedDict):
    history: list[dict]
    latest_user_message: str
    draft: dict
    selected_tool: str
    planner_reason: str
    tool_result: dict
    assistant_message: str
    validation: dict
    last_saved_interaction_id: int | None


class InteractionAgent:
    def __init__(self, llm: LLMClient, service: CRMService):
        self.llm = llm
        self.service = service
        self.tools = build_tools(llm, service)
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(GraphState)
        builder.add_node("plan", self._plan_node)
        builder.add_node("run_tool", self._run_tool_node)
        builder.add_node("respond", self._respond_node)
        builder.add_edge(START, "plan")
        builder.add_edge("plan", "run_tool")
        builder.add_edge("run_tool", "respond")
        builder.add_edge("respond", END)
        return builder.compile()

    def _plan_node(self, state: GraphState) -> dict:
        decision = self.llm.plan_tool(
            state["history"],
            state["latest_user_message"],
            InteractionDraft.model_validate(state["draft"]),
        )
        return {
            "selected_tool": decision.tool_name,
            "planner_reason": decision.reason,
        }

    def _run_tool_node(self, state: GraphState) -> dict:
        tool = self.tools[state["selected_tool"]]
        result = tool.invoke(
            {
                "latest_user_message": state["latest_user_message"],
                "draft": state["draft"],
            }
        )
        tool_result = ToolExecutionResult.model_validate(result)
        return {
            "tool_result": tool_result.model_dump(mode="json"),
            "draft": tool_result.draft.model_dump(mode="json"),
            "validation": tool_result.validation.model_dump(),
            "assistant_message": tool_result.assistant_message,
            "last_saved_interaction_id": tool_result.last_saved_interaction_id,
        }

    def _respond_node(self, state: GraphState) -> dict:
        return {"assistant_message": state["assistant_message"]}

    def process_turn(self, history: list[ChatMessage], draft: dict, user_message: str) -> dict:
        history_payload = [message.model_dump(mode="json") for message in history]
        result = self.graph.invoke(
            {
                "history": history_payload,
                "latest_user_message": user_message,
                "draft": draft,
                "selected_tool": "log_interaction",
                "planner_reason": "",
                "tool_result": {},
                "assistant_message": "",
                "validation": {},
                "last_saved_interaction_id": None,
            }
        )
        assistant_message = ChatMessage(role=ChatRole.assistant, content=result["assistant_message"])
        tool_result = ToolExecutionResult.model_validate(result["tool_result"])
        updated_history = [*history, ChatMessage(role=ChatRole.user, content=user_message), assistant_message]
        return {
            "assistant_message": assistant_message,
            "draft": tool_result.draft,
            "validation": tool_result.validation,
            "tool_event": tool_result.tool_event,
            "last_saved_interaction_id": result.get("last_saved_interaction_id"),
            "messages": updated_history,
        }
