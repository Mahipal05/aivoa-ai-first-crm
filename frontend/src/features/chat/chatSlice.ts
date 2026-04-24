import { createSlice } from "@reduxjs/toolkit";

import type { ChatMessage } from "../../types";
import { bootstrapApp, submitChatMessage } from "../session/appThunks";

interface ChatState {
  messages: ChatMessage[];
  status: "idle" | "sending";
  error: string | null;
}

const initialState: ChatState = {
  messages: [],
  status: "idle",
  error: null,
};

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(bootstrapApp.fulfilled, (state, action) => {
        state.messages = action.payload.session.messages;
        state.error = null;
      })
      .addCase(submitChatMessage.pending, (state, action) => {
        state.status = "sending";
        state.error = null;
        state.messages.push({
          id: `pending-${Date.now()}`,
          role: "user",
          content: action.meta.arg.message,
          created_at: new Date().toISOString(),
        });
      })
      .addCase(submitChatMessage.fulfilled, (state, action) => {
        state.status = "idle";
        state.messages[state.messages.length - 1] = {
          id: `user-${Date.now()}`,
          role: "user",
          content: action.payload.userMessage,
          created_at: new Date().toISOString(),
        };
        state.messages.push(action.payload.response.assistant_message);
      })
      .addCase(submitChatMessage.rejected, (state, action) => {
        state.status = "idle";
        state.error = action.error.message ?? "Unable to send the message.";
      });
  },
});

export default chatSlice.reducer;
