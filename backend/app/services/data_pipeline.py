from dataclasses import dataclass
from typing import Dict, List, Tuple
import asyncio
import json
import time
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from app.core.config import settings
from app.models.database import RestaurantDB
from app.services.metrics_service import MetricsService


@dataclass
class IngestionResult:
    """Result of data ingestion process."""
    raw_records: int
    prepared_records: int
    processing_time: float
    errors: List[str]


class DataPipeline:
    """Service for data ingestion, preparation, and catalog management."""
    
    REQUIRED_OUTPUT_COLUMNS = [
        "restaurant_name",
        "location", 
        "cuisine",
        "estimated_cost",
        "rating",
    ]

    CANDIDATE_COLUMN_MAP: Dict[str, str] = {
        "name": "restaurant_name",
        "restaurant_name": "restaurant_name",
        "restaurant": "restaurant_name",
        "city": "location",
        "location": "location",
        "locality": "location",
        "cuisines": "cuisine",
        "cuisine": "cuisine",
        "approx_cost(for two people)": "estimated_cost",
        "approx_cost_for_two_people": "estimated_cost",
        "cost_for_two": "estimated_cost",
        "estimated_cost": "estimated_cost",
        "rate": "rating",
        "rating": "rating",
        "aggregate_rating": "rating",
    }

    def __init__(self, metrics_service: MetricsService):
        self.metrics_service = metrics_service
        self._catalog_cache = None
        self._cache_timestamp = None

    async def ingest_and_prepare(self) -> IngestionResult:
        """Ingest raw data and prepare it for recommendations."""
        start_time = time.time()
        errors = []
        
        try:
            # Load raw data
            raw_df = await self._load_raw_df()
            raw_records = len(raw_df)
            
            # Save raw data
            await self._save_raw_data(raw_df)
            
            # Prepare data
            prepared_df = await self._prepare_data(raw_df)
            prepared_records = len(prepared_df)
            
            # Save prepared data
            await self._save_prepared_data(prepared_df)
            
            # Update cache
            self._catalog_cache = prepared_df
            self._cache_timestamp = time.time()
            
            processing_time = time.time() - start_time
            
            self.metrics_service.increment_counter("data.ingestion.success")
            self.metrics_service.set_gauge("data.raw_records", raw_records)
            self.metrics_service.set_gauge("data.prepared_records", prepared_records)
            
            return IngestionResult(
                raw_records=raw_records,
                prepared_records=prepared_records,
                processing_time=processing_time,
                errors=errors,
            )
            
        except Exception as exc:
            self.metrics_service.increment_counter("data.ingestion.error")
            errors.append(str(exc))
            raise RuntimeError(f"Data ingestion failed: {exc}") from exc

    async def load_catalog(self) -> pd.DataFrame:
        """Load the restaurant catalog for recommendations."""
        # Check cache first
        if (self._catalog_cache is not None and 
            self._cache_timestamp is not None and
            time.time() - self._cache_timestamp < 300):  # 5 minutes cache
            return self._catalog_cache.copy()
        
        try:
            if settings.PREPARED_DATA_FILE.exists():
                catalog = pd.read_parquet(settings.PREPARED_DATA_FILE)
            elif settings.RAW_DATA_FILE.exists():
                catalog = await self._prepare_data(pd.read_csv(settings.RAW_DATA_FILE))
                await self._save_prepared_data(catalog)
            else:
                # Load from Hugging Face and prepare
                raw_df = await self._load_raw_df()
                catalog = await self._prepare_data(raw_df)
                await self._save_prepared_data(catalog)
            
            # Update cache
            self._catalog_cache = catalog
            self._cache_timestamp = time.time()
            
            return catalog.copy()
            
        except Exception as exc:
            self.metrics_service.increment_counter("data.catalog_load_error")
            raise FileNotFoundError(
                "Restaurant catalog not found. Please run data ingestion first."
            ) from exc

    async def get_catalog_info(self) -> Dict:
        """Get information about the current catalog."""
        try:
            catalog = await self.load_catalog()
            
            info = {
                "total_restaurants": len(catalog),
                "unique_locations": catalog["location"].nunique(),
                "unique_cuisines": catalog["cuisine"].nunique(),
                "avg_rating": catalog["rating"].mean(),
                "avg_cost": catalog["estimated_cost"].mean(),
                "rating_distribution": catalog["rating"].value_counts().to_dict(),
                "cost_distribution": {
                    "low": len(catalog[catalog["estimated_cost"] <= 500]),
                    "medium": len(catalog[(catalog["estimated_cost"] > 500) & (catalog["estimated_cost"] <= 1500)]),
                    "high": len(catalog[catalog["estimated_cost"] > 1500]),
                },
                "top_locations": catalog["location"].value_counts().head(10).to_dict(),
                "top_cuisines": catalog["cuisine"].value_counts().head(10).to_dict(),
            }
            
            return info
            
        except Exception as exc:
            self.metrics_service.increment_counter("data.catalog_info_error")
            raise RuntimeError(f"Failed to get catalog info: {exc}") from exc

    async def _load_raw_df(self) -> pd.DataFrame:
        """Load raw dataset from Hugging Face or local file."""
        if settings.RAW_DATA_FILE.exists():
            self.metrics_service.increment_counter("data.load_local")
            return pd.read_csv(settings.RAW_DATA_FILE)
        
        try:
            self.metrics_service.increment_counter("data.load_huggingface")
            ds = load_dataset(settings.HF_DATASET_ID, split="train")
            return ds.to_pandas()
        except Exception as exc:
            raise RuntimeError(
                f"Unable to fetch dataset from Hugging Face and no local file found at {settings.RAW_DATA_FILE}"
            ) from exc

    async def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare and clean the raw dataset."""
        try:
            # Standardize columns
            mapped_df = await self._standardize_columns(df.copy())
            
            # Clean and normalize data
            mapped_df["restaurant_name"] = mapped_df["restaurant_name"].astype(str).str.strip()
            mapped_df["location"] = mapped_df["location"].astype(str).str.strip().str.lower()
            mapped_df["location"] = mapped_df["location"].replace({
                "bengaluru": "bangalore",
                "new delhi": "delhi",
            })
            mapped_df["cuisine"] = mapped_df["cuisine"].astype(str).str.strip().str.lower()
            
            # Parse numeric fields
            mapped_df["estimated_cost"] = mapped_df["estimated_cost"].apply(self._parse_cost)
            mapped_df["rating"] = mapped_df["rating"].apply(self._parse_rating)
            
            # Filter invalid data
            mapped_df = mapped_df.dropna(subset=self.REQUIRED_OUTPUT_COLUMNS)
            mapped_df = mapped_df[mapped_df["estimated_cost"] > 0]
            mapped_df = mapped_df[(mapped_df["rating"] >= 0) & (mapped_df["rating"] <= 5)]
            
            # Remove duplicates
            mapped_df = mapped_df.drop_duplicates(
                subset=["restaurant_name", "location", "cuisine"], 
                keep="first"
            )
            
            # Select required columns
            result = mapped_df[self.REQUIRED_OUTPUT_COLUMNS].reset_index(drop=True)
            
            self.metrics_service.set_gauge("data.prepared_records", len(result))
            
            return result
            
        except Exception as exc:
            self.metrics_service.increment_counter("data.preparation_error")
            raise RuntimeError(f"Data preparation failed: {exc}") from exc

    async def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names."""
        # Convert to lowercase and strip
        lowered = {col: col.strip().lower() for col in df.columns}
        df = df.rename(columns=lowered)
        
        # Map to standard names
        rename_map = {}
        for col in df.columns:
            if col in self.CANDIDATE_COLUMN_MAP:
                rename_map[col] = self.CANDIDATE_COLUMN_MAP[col]
        df = df.rename(columns=rename_map)
        
        # Check for required columns
        missing = [c for c in self.REQUIRED_OUTPUT_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(
                f"Dataset is missing required columns after normalization: {missing}"
            )
        
        return df

    @staticmethod
    def _parse_cost(value) -> float | None:
        """Parse cost value into normalized float."""
        if pd.isna(value):
            return None
        
        text = str(value).strip().lower().replace(",", "")
        for token in ["rs.", "rs", "inr", "â¹", "$"]:
            text = text.replace(token, "")
        
        if "-" in text:
            parts = [p.strip() for p in text.split("-") if p.strip()]
            nums = [float(p) for p in parts if p.replace(".", "", 1).isdigit()]
            if nums:
                return sum(nums) / len(nums)
        
        if text.replace(".", "", 1).isdigit():
            return float(text)
        
        return None

    @staticmethod
    def _parse_rating(value) -> float | None:
        """Parse rating value into normalized float."""
        if pd.isna(value):
            return None
        
        text = str(value).strip().lower()
        if text in {"new", "-", "n/a", "na", "not rated"}:
            return None
        
        if "/" in text:
            text = text.split("/", maxsplit=1)[0].strip()
        
        filtered = "".join(ch for ch in text if ch.isdigit() or ch == ".")
        if filtered.replace(".", "", 1).isdigit():
            rating = float(filtered)
            return min(max(rating, 0.0), 5.0)  # Clamp to 0-5 range
        
        return None

    async def _save_raw_data(self, df: pd.DataFrame) -> None:
        """Save raw data to file."""
        settings.RAW_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(settings.RAW_DATA_FILE, index=False)

    async def _save_prepared_data(self, df: pd.DataFrame) -> None:
        """Save prepared data to file."""
        settings.PREPARED_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(settings.PREPARED_DATA_FILE, index=False)
        df.to_csv(settings.PREPARED_DATA_FILE.with_suffix(".csv"), index=False)


def budget_to_cost_range(budget: str) -> Tuple[float, float]:
    """Convert budget category to cost range."""
    normalized = budget.strip().lower()
    if normalized == "low":
        return (0, 500)
    elif normalized == "medium":
        return (500, 1500)
    elif normalized == "high":
        return (1500, float("inf"))
    else:
        raise ValueError("Invalid budget. Supported values: low, medium, high.")
