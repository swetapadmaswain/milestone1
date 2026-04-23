from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
RAW_DIR = STORAGE_DIR / "raw"
PREPARED_DIR = STORAGE_DIR / "prepared"

RAW_FILE = RAW_DIR / "zomato.csv"
PREPARED_PARQUET = PREPARED_DIR / "restaurants.parquet"
PREPARED_CSV = PREPARED_DIR / "restaurants.csv"

HF_DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)
