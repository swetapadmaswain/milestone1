# Phase 4: Production Readiness (Groq-backed)

This folder contains a standalone implementation of **Phase 4** from `docs/phased-architecture.md`, extending previous phases with reliability, observability, safety, and cost-aware LLM operation.
It also includes **late Phase 2 alignment**: Groq now returns validated LLM ranking scores in addition to explanations, and these scores participate in final ranking.

## Included Components

- API gateway basics:
  - API key validation via `PHASE4_API_KEY` (optional)
  - Per-client in-memory rate limiting
  - Request validation through FastAPI/Pydantic
- Caching layer:
  - In-memory TTL cache for recommendation responses
  - Cache hit/miss counters exposed in metrics
- Monitoring and observability:
  - Endpoint latency tracking
  - Error/fallback counters
  - Groq token usage counters (`prompt_tokens`, `completion_tokens`)
  - `GET /metrics` endpoint
- Quality and safety guardrails:
  - Input sanitization for prompt-injection-like text
  - LLM output validation against known candidate names
  - Deterministic fallback explanation mode on failure
- LLM service:
  - Uses Groq Chat Completions API (`https://api.groq.com/openai/v1/chat/completions`)
  - Model configurable via `GROQ_MODEL`
  - Prompt version surfaced as `prompt_version` in response

## Project Structure

- `app/main.py` - FastAPI app, gateway checks, endpoints
- `app/data_pipeline.py` - ingestion and preprocessing pipeline
- `app/services.py` - personalization, experiments, guardrails, cache, rate-limiter, Groq integration, recommender
- `app/models.py` - request/response schemas
- `app/ui/index.html` - test UI for recommendations and metrics
- `storage/` - generated datasets, profiles, feedback logs, experiment assignments

## Setup

```bash
cd phase4-production
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

- `GROQ_API_KEY` (required for live LLM explanations)
- `GROQ_MODEL` (default: `llama-3.1-8b-instant`)
- `PHASE4_API_KEY` (optional API key enforcement)
- `PHASE4_RATE_LIMIT_PER_MIN` (default: `120`)
- `PHASE4_CACHE_TTL_SECONDS` (default: `120`)
- `PHASE4_LLM_TIMEOUT_SECONDS` (default: `8.0`)

## Run

```bash
uvicorn app.main:app --reload --port 8002
```

Open:

- `http://127.0.0.1:8002/`

## Endpoints

- `GET /health`
- `GET /metrics`
- `POST /ingest`
- `POST /recommend`
- `POST /feedback`
- `GET /profile/{session_id}?user_id=<optional>`

## Notes

- If Groq is unavailable or returns invalid output, responses still succeed with deterministic fallback explanations.
- Caching is in-memory and intended for demo/local deployment. Move to Redis for distributed production setups.
