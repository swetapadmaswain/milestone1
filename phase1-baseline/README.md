# Phase 1 Baseline: Restaurant Recommendation System

This folder contains a standalone implementation of **Phase 1** from `docs/phased-architecture.md`:

- Dataset ingestion service
- Data preparation and normalization pipeline
- Restaurant catalog store (local Parquet/CSV)
- Basic web UI as primary preference input source
- Preference input API (for programmatic access)
- Rule-based filter and deterministic ranking (top-N)

## Project Structure

- `app/main.py` - FastAPI application
- `app/ui/index.html` - basic web UI for user input
- `app/models.py` - request/response schemas
- `app/data_pipeline.py` - ingestion + preprocessing + persistence
- `app/recommender.py` - deterministic filtering + scoring
- `app/config.py` - configuration paths
- `storage/` - generated raw and prepared datasets

## Setup

```bash
cd phase1-baseline
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run API

```bash
uvicorn app.main:app --reload --port 8000
```

Open the UI at:

- `http://127.0.0.1:8000/`

## Endpoints

- `GET /health` - service health
- `POST /ingest` - run ingestion + preprocessing
- `POST /recommend` - get top-N recommendations
- `GET /catalog/stats` - catalog-level stats
- `GET /` - basic web UI for input and results

## Notes

- Ingestion tries Hugging Face dataset id:
  - `ManikaSaini/zomato-restaurant-recommendation`
- If online ingestion fails, place a local CSV at:
  - `phase1-baseline/storage/raw/zomato.csv`
- Ranking is deterministic and reproducible.
- If strict filters return no matches, the recommender applies controlled fallback:
  1) relax minimum rating by 0.5,
  2) relax cuisine constraint,
  3) widen budget band while keeping location fixed.
