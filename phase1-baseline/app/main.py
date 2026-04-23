from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .data_pipeline import DataPipeline
from .models import IngestionResponse, RecommendationRequest, RecommendationResponse
from .recommender import Recommender

app = FastAPI(title="Phase 1 Restaurant Recommender", version="1.0.0")

pipeline = DataPipeline()
recommender = Recommender()
UI_FILE = Path(__file__).resolve().parent / "ui" / "index.html"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def ui_home():
    if not UI_FILE.exists():
        raise HTTPException(status_code=500, detail="UI file missing.")
    return UI_FILE.read_text(encoding="utf-8")


@app.post("/ingest", response_model=IngestionResponse)
def ingest_data():
    try:
        result = pipeline.ingest_and_prepare()
        return IngestionResponse(
            message="Ingestion and preprocessing completed.",
            raw_records=result.raw_records,
            prepared_records=result.prepared_records,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/catalog/stats")
def catalog_stats():
    try:
        catalog = pipeline.load_catalog()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "records": len(catalog),
        "locations": int(catalog["location"].nunique()),
        "cuisines": int(catalog["cuisine"].nunique()),
        "rating_range": [float(catalog["rating"].min()), float(catalog["rating"].max())],
        "cost_range": [
            float(catalog["estimated_cost"].min()),
            float(catalog["estimated_cost"].max()),
        ],
    }


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest):
    try:
        catalog = pipeline.load_catalog()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        run_result = recommender.recommend(catalog, request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return RecommendationResponse(
        total_candidates=len(catalog),
        returned_count=len(run_result.recommendations),
        fallback_used=run_result.fallback_used,
        relaxation_steps=run_result.relaxation_steps,
        recommendations=run_result.recommendations,
    )
