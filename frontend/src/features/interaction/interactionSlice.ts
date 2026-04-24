import { createSlice } from "@reduxjs/toolkit";

import type { InteractionDraft, ToolEvent, ValidationReport } from "../../types";
import { bootstrapApp, submitChatMessage } from "../session/appThunks";

const emptyDraft: InteractionDraft = {
  hcp_name: "",
  interaction_type: "Meeting",
  interaction_date: "",
  interaction_time: "",
  attendees: [],
  topics_discussed: "",
  materials_shared: [],
  samples_distributed: [],
  sentiment: "neutral",
  outcomes: "",
  follow_up_actions: [],
  ai_suggested_follow_up: [],
  ai_summary: "",
  source_text: "",
};

const emptyValidation: ValidationReport = {
  is_valid: false,
  missing_fields: [],
  warnings: [],
};

interface InteractionState {
  draft: InteractionDraft;
  validation: ValidationReport;
  toolEvents: ToolEvent[];
  lastSavedInteractionId: number | null;
}

const initialState: InteractionState = {
  draft: emptyDraft,
  validation: emptyValidation,
  toolEvents: [],
  lastSavedInteractionId: null,
};

const interactionSlice = createSlice({
  name: "interaction",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(bootstrapApp.fulfilled, (state, action) => {
        state.draft = action.payload.session.draft;
        state.validation = action.payload.session.validation;
        state.toolEvents = action.payload.session.tool_events;
        state.lastSavedInteractionId = action.payload.session.last_saved_interaction_id;
      })
      .addCase(submitChatMessage.fulfilled, (state, action) => {
        state.draft = action.payload.response.draft;
        state.validation = action.payload.response.validation;
        state.toolEvents = action.payload.response.tool_events;
        state.lastSavedInteractionId = action.payload.response.last_saved_interaction_id;
      });
  },
});

export default interactionSlice.reducer;
