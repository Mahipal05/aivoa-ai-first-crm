# Demo Script

## 10-15 Minute Walkthrough

### 1. Product Overview

- Explain that the left panel is an AI-controlled HCP interaction form.
- Explain that the right panel is the only input surface for the user.
- Mention Redux state synchronization and LangGraph orchestration.

### 2. Tool Demonstration Prompts

Use these prompts in order:

1. `Met Dr. Anita Sharma today at 19:36, discussed Product X efficacy, positive sentiment, shared brochure and sample kit, agreed to review the data in 2 weeks.`
   Expected: `log_interaction` populates the form.

2. `Update the sentiment to neutral and change the time to 20:10.`
   Expected: `edit_interaction` updates only sentiment and time.

3. `Summarize the interaction and suggest next steps.`
   Expected: `summarize_interaction` fills AI summary and follow-up recommendations.

4. `Validate the form for missing information.`
   Expected: `validate_interaction` reports readiness or missing fields.

5. `Save the interaction.`
   Expected: `save_interaction` persists the record and shows a saved id.

6. `Clear the form and start over.`
   Expected: `clear_form` resets the draft.

### 3. Architecture Talking Points

- Planner node chooses the tool from the latest user intent.
- Tool node executes extraction, editing, validation, summary, or save.
- The backend sends the full updated draft back to Redux after every message.
- The form never relies on manual user edits, so the chat and form stay consistent.

### 4. What To Mention About Models

- The assignment requested `gemma2-9b-it`, so that is the primary configured Groq model.
- As of April 22, 2026, Groq's deprecation page lists `gemma2-9b-it` as deprecated on October 8, 2025.
- Because of that, the backend includes fallback models through env configuration.
