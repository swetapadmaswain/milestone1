import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
RAW_DIR = STORAGE_DIR / "raw"
PREPARED_DIR = STORAGE_DIR / "prepared"
FEEDBACK_DIR = STORAGE_DIR / "feedback"
PROFILE_DIR = STORAGE_DIR / "profiles"
EXPERIMENT_DIR = STORAGE_DIR / "experiments"

RAW_FILE = RAW_DIR / "zomato.csv"
PREPARED_PARQUET = PREPARED_DIR / "restaurants.parquet"
PREPARED_CSV = PREPARED_DIR / "restaurants.csv"
FEEDBACK_LOG = FEEDBACK_DIR / "events.jsonl"
EXPERIMENT_ASSIGNMENTS = EXPERIMENT_DIR / "assignments.json"

HF_DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"
PROMPT_VERSION = "v1-phase3-groq"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
LLM_TIMEOUT_SECONDS = float(os.getenv("PHASE3_LLM_TIMEOUT_SECONDS", "8.0"))
LLM_MAX_RETRIES = int(os.getenv("PHASE3_LLM_MAX_RETRIES", "2"))


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
