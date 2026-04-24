import { createAsyncThunk } from "@reduxjs/toolkit";

import { bootstrapSession, fetchInteractions, sendChatMessage } from "../../api/client";

export const bootstrapApp = createAsyncThunk(
  "session/bootstrapApp",
  async (sessionId: string | null | undefined) => {
    const [session, interactions] = await Promise.all([
      bootstrapSession(sessionId),
      fetchInteractions(),
    ]);
    return { session, interactions: interactions.items };
  },
);

export const submitChatMessage = createAsyncThunk(
  "chat/submitChatMessage",
  async (payload: { sessionId: string; message: string }) => {
    const response = await sendChatMessage(payload.sessionId, payload.message);
    const interactions = await fetchInteractions();
    return { response, userMessage: payload.message, interactions: interactions.items };
  },
);
