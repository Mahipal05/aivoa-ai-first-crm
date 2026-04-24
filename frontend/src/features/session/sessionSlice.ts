import { createSlice } from "@reduxjs/toolkit";

import type { HCPSummary, InteractionRecord, MaterialSummary } from "../../types";
import { bootstrapApp, submitChatMessage } from "./appThunks";

interface SessionState {
  sessionId: string | null;
  llmMode: string;
  hcps: HCPSummary[];
  materials: MaterialSummary[];
  recentInteractions: InteractionRecord[];
  status: "idle" | "loading" | "ready" | "error";
  error: string | null;
}

const initialState: SessionState = {
  sessionId: null,
  llmMode: "mock",
  hcps: [],
  materials: [],
  recentInteractions: [],
  status: "idle",
  error: null,
};

const sessionSlice = createSlice({
  name: "session",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(bootstrapApp.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(bootstrapApp.fulfilled, (state, action) => {
        state.status = "ready";
        state.sessionId = action.payload.session.session_id;
        state.llmMode = action.payload.session.llm_mode;
        state.hcps = action.payload.session.hcps;
        state.materials = action.payload.session.materials;
        state.recentInteractions = action.payload.interactions;
      })
      .addCase(bootstrapApp.rejected, (state, action) => {
        state.status = "error";
        state.error = action.error.message ?? "Unable to initialize the app.";
      })
      .addCase(submitChatMessage.fulfilled, (state, action) => {
        state.llmMode = action.payload.response.llm_mode;
        state.recentInteractions = action.payload.interactions;
      })
      .addCase(submitChatMessage.rejected, (state, action) => {
        state.error = action.error.message ?? "Unable to process the chat request.";
      });
  },
});

export default sessionSlice.reducer;
