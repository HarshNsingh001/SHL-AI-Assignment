# SHL Assessment Agent

Production-ready FastAPI service implementing a fully deterministic SHL assessment
recommendation agent for the SHL AI Intern take-home assignment.

## What This Does

Given a conversation between a hiring manager and the assistant, the agent:

1. **Extracts** structured hiring constraints (role, job level, industry, skills, languages, purpose) from the conversation using deterministic regex and synonym matching.
2. **Queries** the SHL assessment catalog to retrieve relevant candidates.
3. **Applies** deterministic business rules to decide whether to ask a clarification question, produce recommendations, or handle an out-of-scope request.
4. **Generates** a Markdown-formatted reply with an assessment table when appropriate.

**No LLMs, no embeddings, no external APIs.** All logic is fully deterministic.

## Architecture

```text
POST /chat
    │
    ▼
ChatOrchestrator
    │
    ├── 1. ConversationManager   — tracks message history
    ├── 2. ConstraintExtractor   — deterministic regex + synonym extraction
    ├── 3. CatalogQueryService   — filter + rank catalog assessments
    ├── 4. BusinessRuleEngine    — decide next action (clarify / recommend / refuse)
    └── 5. RecommendationEngine  — build ranked shortlist
    │
    ▼
ResponseGenerator               — template-based Markdown reply (no LLM)
    │
    ▼
ChatResponse { reply, recommendations, end_of_conversation }
```

## Folder Structure

```text
shl-assessment-agent/
    app/
        api/          – FastAPI routes, schemas, dependency injection
        core/         – config, logging, exceptions
        models/       – Pydantic domain models
        services/     – all five pipeline services + catalog loader
    tests/            – unit and integration tests
    main.py
    requirements.txt
    .env.example
```

## How to Run

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy environment defaults:

```bash
cp .env.example .env
```

**Point the agent at the real SHL catalog** (add to `.env`):

```env
SHL_CATALOG_PATH=../data/catalog/shl_catalog.json
```

Start the API:

```bash
uvicorn main:app --reload
```

Visit the health endpoint:

```text
GET http://127.0.0.1:8000/health
```

Expected response:

```json
{ "status": "ok" }
```

Try the chat endpoint:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "We need to hire graduate financial analysts.", "conversation": []}'
```

## How to Test

Run the test suite:

```bash
pytest
```

Run formatting and static checks:

```bash
black --check .
ruff check .
mypy .
```

## Catalog Format

The agent natively supports the raw SHL catalog export format (`entity_id`, `link`,
string duration, `"yes"`/`"no"` booleans). No pre-processing is required — the
`CatalogLoader` adapts the raw file automatically on startup.
