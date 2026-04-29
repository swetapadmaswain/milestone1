from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "Restaurant Recommendation API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    API_KEY: Optional[str] = Field(default=None, env="API_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Rate Limiting
    RATE_LIMIT_PER_MIN: int = Field(default=120, env="RATE_LIMIT_PER_MIN")
    
    # Caching
    CACHE_TTL_SECONDS: int = Field(default=120, env="CACHE_TTL_SECONDS")
    CACHE_MAX_SIZE: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    # LLM Configuration (Groq)
    GROQ_API_KEY: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    GROQ_MODEL: str = Field(default="llama-3.1-8b-instant", env="GROQ_MODEL")
    GROQ_TIMEOUT_SECONDS: float = Field(default=8.0, env="GROQ_TIMEOUT_SECONDS")
    GROQ_MAX_TOKENS: int = Field(default=1000, env="GROQ_MAX_TOKENS")
    
    # Database Configuration
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # File Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    RAW_DIR: Path = STORAGE_DIR / "raw"
    PREPARED_DIR: Path = STORAGE_DIR / "prepared"
    PROFILES_DIR: Path = STORAGE_DIR / "profiles"
    FEEDBACK_DIR: Path = STORAGE_DIR / "feedback"
    EXPERIMENTS_DIR: Path = STORAGE_DIR / "experiments"
    
    # Data Files
    RAW_DATA_FILE: Path = RAW_DIR / "restaurants.csv"
    PREPARED_DATA_FILE: Path = PREPARED_DIR / "restaurants.parquet"
    FEEDBACK_LOG_FILE: Path = FEEDBACK_DIR / "events.jsonl"
    EXPERIMENT_ASSIGNMENTS_FILE: Path = EXPERIMENTS_DIR / "assignments.json"
    
    # Dataset Configuration
    HF_DATASET_ID: str = "ManikaSaini/zomato-restaurant-recommendation"
    PROMPT_VERSION: str = "v1-groq-backend"
    
    # Monitoring
    METRICS_ENABLED: bool = Field(default=True, env="METRICS_ENABLED")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Recommendation Settings
    DEFAULT_TOP_N: int = Field(default=5, env="DEFAULT_TOP_N")
    MAX_CANDIDATES_FOR_LLM: int = Field(default=20, env="MAX_CANDIDATES_FOR_LLM")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def ensure_directories() -> None:
    """Create necessary directories if they don't exist."""
    directories = [
        settings.STORAGE_DIR,
        settings.RAW_DIR,
        settings.PREPARED_DIR,
        settings.PROFILES_DIR,
        settings.FEEDBACK_DIR,
        settings.EXPERIMENTS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
