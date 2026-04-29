# Phase 2: LLM-Augmented Ranking and Explanations (Groq)

Standalone implementation of Phase 2 from `docs/phased-architecture.md`.

## Includes

- Prompt builder with strict JSON schema contract.
- Groq orchestrator with retries + timeout.
- Response parser/validator rejecting unknown restaurants.
- Deterministic fallback when LLM fails.
- Explanations and confidence tags in output.

## Setup

```bash
cd phase2-llm
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Environment

- `GROQ_API_KEY` (required for live LLM responses)
- `GROQ_MODEL` (default: `llama-3.1-8b-instant`)
- `PHASE2_LLM_TIMEOUT_SECONDS` (default: `8.0`)
- `PHASE2_LLM_MAX_RETRIES` (default: `2`)

## Run

```bash
uvicorn app.main:app --reload --port 8003
```

Open: `http://127.0.0.1:8003/`

## Endpoints

- `GET /health`
- `POST /ingest`
- `POST /recommend`
