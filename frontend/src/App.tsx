import { useEffect } from "react";

import { ChatPanel } from "./components/ChatPanel";
import { FormPanel } from "./components/FormPanel";
import { useAppDispatch, useAppSelector } from "./app/hooks";
import { bootstrapApp, submitChatMessage } from "./features/session/appThunks";

const SESSION_STORAGE_KEY = "aivoa-session-id";

export default function App() {
  const dispatch = useAppDispatch();
  const session = useAppSelector((state) => state.session);
  const interaction = useAppSelector((state) => state.interaction);
  const chat = useAppSelector((state) => state.chat);

  useEffect(() => {
    const existing = window.localStorage.getItem(SESSION_STORAGE_KEY);
    void dispatch(bootstrapApp(existing));
  }, [dispatch]);

  useEffect(() => {
    if (session.sessionId) {
      window.localStorage.setItem(SESSION_STORAGE_KEY, session.sessionId);
    }
  }, [session.sessionId]);

  const handleSend = (message: string) => {
    if (!session.sessionId) {
      return;
    }
    void dispatch(submitChatMessage({ sessionId: session.sessionId, message }));
  };

  const handleRetry = () => {
    const existing = window.localStorage.getItem(SESSION_STORAGE_KEY);
    void dispatch(bootstrapApp(existing));
  };

  return (
    <div className="page-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">AIVOA.AI Assignment</p>
          <h1>AI-First CRM HCP Module</h1>
          <p className="subtle">
            LangGraph orchestrates the AI assistant, while Groq-backed extraction keeps the form and chat state aligned.
          </p>
        </div>
        <div className="header-stats">
          <span className="header-chip">LLM Mode: {session.llmMode}</span>
          <span className="header-chip">HCPs: {session.hcps.length}</span>
          <span className="header-chip">Materials: {session.materials.length}</span>
        </div>
      </header>

      {session.error && (
        <div className="error-banner">
          <span>{session.error}</span>
          <button type="button" onClick={handleRetry}>
            Retry backend connection
          </button>
        </div>
      )}

      <main className="app-layout">
        <FormPanel
          draft={interaction.draft}
          validation={interaction.validation}
          lastToolEvent={interaction.toolEvents.at(-1)}
          recentInteractions={session.recentInteractions}
        />
        <ChatPanel
          messages={chat.messages}
          toolEvents={interaction.toolEvents}
          isSending={chat.status === "sending" || session.status === "loading"}
          onSend={handleSend}
        />
      </main>
    </div>
  );
}
