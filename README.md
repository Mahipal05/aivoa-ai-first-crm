# AIVOA AI-First CRM HCP Module

This repository implements the Task 1 assignment as a full-stack, production-minded split-screen HCP interaction logger. The left panel is an AI-controlled interaction form, and the right panel is a LangGraph-powered assistant chat. Users do not manually fill the form; they describe the interaction in natural language and the AI updates, validates, summarizes, and saves the form state.

## What is included

- `frontend/`: React + Vite + Redux Toolkit UI using Google Inter
- `backend/`: FastAPI + LangGraph orchestration + Groq-ready LLM integration
- `docs/architecture.md`: architecture and workflow breakdown
- `docs/demo-script.md`: recording guide and demo prompts
- `docker-compose.yml`: Postgres setup for review/demo

## Assignment Fit

This implementation covers the requested split-screen behavior and keeps state consistent between the AI assistant and the form.

### Required LangGraph tools

1. `log_interaction`
2. `edit_interaction`
3. `clear_form`
4. `summarize_interaction`
5. `validate_interaction`
6. `save_interaction`

### Key behaviors

- Natural-language interaction logging into a structured HCP form
- Partial edits that only update specified fields
- AI-generated summaries and follow-up recommendations
- Validation before save
- SQL persistence with audit entries
- Redux-backed frontend state synchronization

## Tech Stack

- Frontend: React 19, Redux Toolkit, Vite, TypeScript
- Backend: FastAPI, SQLAlchemy, LangGraph, LangChain Core tools
- LLM: Groq API
- Database: Postgres-ready configuration with SQLite fallback for local dev/tests
- Styling: Inter font, responsive split-screen layout

## Recommended Runtime

- Python: 3.11
- Node.js: 22 LTS

The current workspace previously reported Node `25.1.0`. If Vite throws `spawn EPERM` or other startup/build issues locally, switch to Node 22 LTS first.

## Groq Model Note

The assignment explicitly asked for `gemma2-9b-it`, so it is configured as the primary model in `backend/.env.example`.

As of April 22, 2026, Groq's deprecation page lists `gemma2-9b-it` as deprecated on October 8, 2025. To keep the assignment aligned with the brief while still remaining runnable, the backend supports fallback models through `GROQ_FALLBACK_MODELS`.

Leave `GROQ_SERVICE_TIER` blank unless your Groq org explicitly supports a paid tier value. The backend will run without it.

## Architecture Summary

The backend uses a small LangGraph agent:

1. Planner node inspects the latest user message and current draft.
2. Tool node executes exactly one intent-specific tool.
3. Response node returns the assistant message.
4. FastAPI persists the updated session snapshot.
5. Redux updates the chat and form in one cycle.

See [docs/architecture.md](docs/architecture.md) for the full flow.

## Local Setup

### 1. Start Postgres (recommended for assignment review)

```bash
docker compose up -d
```

This compose file exposes Postgres on `localhost:5433` to avoid conflicts with an existing local database on `5432`.

### 2. Backend

```bash
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r backend/requirements.txt
copy backend\.env.example backend\.env
```

Update `backend/.env` with your Groq API key:

```env
GROQ_API_KEY=your_key_here
DATABASE_URL=postgresql+psycopg://crm:crm@localhost:5433/aivoa_crm
```

Run the API:

```bash
cd backend
..\.venv\Scripts\python -m uvicorn app.main:app --reload
```

If you want zero setup, you can temporarily change `DATABASE_URL` to `sqlite:///./crm.db`.

### 3. Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend default URL: `http://localhost:5173`

Backend default URL: `http://localhost:8000`

## Fastest Way To Run On Windows

From the repo root:

```powershell
npm run backend
```

In a second terminal:

```powershell
npm run frontend
```

Optional shortcuts:

```powershell
cd frontend
npm start
```

```powershell
npm run test:backend
```

## Verification

Frontend build:

```bash
cd frontend
npm run build
```

Backend tests:

```bash
cd backend
..\.venv\Scripts\python -m pytest app/tests/test_api.py
```

## Suggested Demo Flow

1. Log an interaction in natural language.
2. Correct only one or two fields.
3. Ask the assistant for a summary.
4. Ask the assistant to validate the draft.
5. Save the interaction.
6. Clear the form to show reset behavior.

See [docs/demo-script.md](docs/demo-script.md) for the exact prompts.

## API Endpoints

- `POST /api/bootstrap`
- `GET /api/sessions/{session_id}`
- `POST /api/sessions/{session_id}/chat`
- `GET /api/interactions`
- `GET /health`

## Expected Outcome

Reviewers should see:

- a working split-screen HCP logging interface,
- LangGraph-driven tool orchestration,
- LLM-based extraction and partial correction,
- state consistency between chat and form,
- and a save path backed by SQL persistence.
