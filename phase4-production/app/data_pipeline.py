from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import pandas as pd

from .config import HF_DATASET_ID, PREPARED_CSV, PREPARED_PARQUET, RAW_FILE, ensure_dirs


@dataclass
class IngestionResult:
    raw_records: int
    prepared_records: int


class DataPipeline:
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

    def ingest_and_prepare(self) -> IngestionResult:
        ensure_dirs()
        raw_df = self._load_raw_df()
        raw_df.to_csv(RAW_FILE, index=False)

        prepared_df = self._prepare(raw_df)
        prepared_df.to_parquet(PREPARED_PARQUET, index=False)
        prepared_df.to_csv(PREPARED_CSV, index=False)
        return IngestionResult(raw_records=len(raw_df), prepared_records=len(prepared_df))

    def load_catalog(self) -> pd.DataFrame:
        if PREPARED_PARQUET.exists():
            return pd.read_parquet(PREPARED_PARQUET)
        if PREPARED_CSV.exists():
            return pd.read_csv(PREPARED_CSV)
        raise FileNotFoundError(
            "Prepared catalog not found. Call /ingest first to build the catalog."
        )

    def _load_raw_df(self) -> pd.DataFrame:
        if RAW_FILE.exists():
            return pd.read_csv(RAW_FILE)
        try:
            from datasets import load_dataset

            ds = load_dataset(HF_DATASET_ID, split="train")
            return ds.to_pandas()
        except Exception as exc:
            raise RuntimeError(
                "Unable to fetch dataset from Hugging Face and no local raw CSV found at "
                f"{RAW_FILE}."
            ) from exc

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        mapped_df = self._standardize_columns(df.copy())

        mapped_df["restaurant_name"] = mapped_df["restaurant_name"].astype(str).str.strip()
        mapped_df["location"] = mapped_df["location"].astype(str).str.strip().str.lower()
        mapped_df["location"] = mapped_df["location"].replace(
            {"bengaluru": "bangalore", "new delhi": "delhi"}
        )
        mapped_df["cuisine"] = mapped_df["cuisine"].astype(str).str.strip().str.lower()

        mapped_df["estimated_cost"] = mapped_df["estimated_cost"].apply(self._parse_cost)
        mapped_df["rating"] = mapped_df["rating"].apply(self._parse_rating)

        mapped_df = mapped_df.dropna(subset=self.REQUIRED_OUTPUT_COLUMNS)
        mapped_df = mapped_df[mapped_df["estimated_cost"] > 0]
        mapped_df = mapped_df[(mapped_df["rating"] >= 0) & (mapped_df["rating"] <= 5)]
        mapped_df = mapped_df.drop_duplicates(
            subset=["restaurant_name", "location", "cuisine"], keep="first"
        )
        return mapped_df[self.REQUIRED_OUTPUT_COLUMNS].reset_index(drop=True)

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        lowered = {col: col.strip().lower() for col in df.columns}
        df = df.rename(columns=lowered)
        rename_map: Dict[str, str] = {}
        for col in df.columns:
            if col in self.CANDIDATE_COLUMN_MAP:
                rename_map[col] = self.CANDIDATE_COLUMN_MAP[col]
        df = df.rename(columns=rename_map)

        missing = [c for c in self.REQUIRED_OUTPUT_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(
                f"Dataset is missing required columns after normalization: {missing}"
            )
        return df

    @staticmethod
    def _parse_cost(value) -> float | None:
        if pd.isna(value):
            return None
        text = str(value).strip().lower().replace(",", "")
        for token in ["rs.", "rs", "inr", "₹", "$"]:
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
        if pd.isna(value):
            return None
        text = str(value).strip().lower()
        if text in {"new", "-", "n/a", "na", "not rated"}:
            return None
        if "/" in text:
            text = text.split("/", maxsplit=1)[0].strip()
        filtered = "".join(ch for ch in text if ch.isdigit() or ch == ".")
        if filtered.replace(".", "", 1).isdigit():
            return float(filtered)
        return None


def budget_to_cost_range(budget: str) -> Tuple[float, float]:
    normalized = budget.strip().lower()
    if normalized == "low":
        return (0, 500)
    if normalized == "medium":
        return (500, 1500)
    if normalized == "high":
        return (1500, float("inf"))
    raise ValueError("Invalid budget. Supported values: low, medium, high.")
