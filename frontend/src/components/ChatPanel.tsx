import { useState } from "react";
import type { FormEvent } from "react";

import type { ChatMessage, ToolEvent } from "../types";

interface ChatPanelProps {
  messages: ChatMessage[];
  toolEvents: ToolEvent[];
  isSending: boolean;
  onSend: (message: string) => void;
}

const QUICK_PROMPTS = [
  {
    label: "Log sample note",
    prompt:
      "Met Dr. Anita Sharma today at 19:36, discussed Product X efficacy, positive sentiment, shared brochure and promised a follow-up in 2 weeks.",
  },
  {
    label: "Edit time and sentiment",
    prompt: "Actually update the sentiment to neutral and change the time to 20:10.",
  },
  {
    label: "Summarize",
    prompt: "Summarize the interaction and suggest next steps.",
  },
  {
    label: "Validate",
    prompt: "Validate the form for missing information.",
  },
  {
    label: "Save",
    prompt: "Save the interaction.",
  },
];

export function ChatPanel({ messages, toolEvents, isSending, onSend }: ChatPanelProps) {
  const [value, setValue] = useState("");

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || isSending) {
      return;
    }
    onSend(trimmed);
    setValue("");
  };

  return (
    <section className="panel chat-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">AI Assistant</p>
          <h2>Chat-driven interaction logging</h2>
        </div>
      </div>

      <div className="helper-card">
        Log the interaction here. The assistant controls the form and keeps the state in sync.
      </div>

      <div className="shortcut-block">
        <p className="eyebrow">Demo Shortcuts</p>
        <div className="quick-prompts">
          {QUICK_PROMPTS.map((prompt) => (
            <button
              key={prompt.label}
              type="button"
              title={prompt.prompt}
              onClick={() => {
                if (!isSending) {
                  onSend(prompt.prompt);
                }
              }}
              className="ghost-chip"
            >
              {prompt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="message-list">
        {messages.map((message) => (
          <article key={message.id} className={`message-bubble message-bubble--${message.role}`}>
            <p className="message-role">{message.role === "assistant" ? "AI Assistant" : "Field Rep"}</p>
            <p>{message.content}</p>
          </article>
        ))}
      </div>

      <div className="tool-strip">
        {toolEvents.slice(-3).map((event) => (
          <span key={`${event.tool_name}-${event.created_at}`} className={`tool-pill tool-pill--${event.status}`}>
            {event.tool_name}
          </span>
        ))}
      </div>

      <form className="composer" onSubmit={handleSubmit}>
        <textarea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="Describe the interaction, request edits, validate, summarize, or save."
          rows={3}
        />
        <button type="submit" disabled={isSending || !value.trim()}>
          {isSending ? "Logging..." : "Log"}
        </button>
      </form>
    </section>
  );
}
