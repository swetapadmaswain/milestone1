# Phase 3: Personalization and Learning Loop

This folder contains a standalone implementation of **Phase 3** from `docs/phased-architecture.md`.
It now incorporates **late Phase 2 integration** by using Groq-driven LLM ranking/explanations with schema validation and deterministic fallback.

## Included Components

- Feedback capture:
  - Explicit signals (`like`, `dislike`)
  - Implicit signals (`click`, `dwell`, `conversion`, `skip`)
- User profile service:
  - Stores user/session event history
  - Builds time-decayed cuisine and budget affinity
- Hybrid ranking engine:
  - Combines rule score + Groq LLM score + personalization score
- Experimentation layer:
  - Sticky A/B variant assignment (`control`, `balanced`, `personal_heavy`)
  - Variant-specific score weights
- LLM layer inherited from Phase 2:
  - Prompt builder with strict JSON response schema
  - Groq orchestration with retries/timeouts
  - Output validation against known candidates
  - Fallback metadata in response (`fallback_used`, `fallback_reason`, `prompt_version`)

## Project Structure

- `app/main.py` - FastAPI app and API routes
- `app/data_pipeline.py` - ingestion and preparation pipeline
- `app/recommender.py` - personalization, experiments, hybrid ranking
- `app/models.py` - API schemas
- `app/ui/index.html` - basic interactive web UI
- `storage/` - generated datasets, feedback logs, user profiles, experiment assignments

## Setup

```bash
cd phase3-personalization
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --port 8001
```

Open UI:

- `http://127.0.0.1:8001/`

## Endpoints

- `GET /health`
- `POST /ingest`
- `POST /recommend`
- `POST /feedback`
- `GET /profile/{session_id}?user_id=<optional>`

## Notes

- For cold-start users (no history), personalization score defaults to `0.0`.
- Session constraints remain hard filters; historical preferences only influence ranking.
- A/B assignment is sticky per `user_id` (or per `session_id` if user id is absent).
