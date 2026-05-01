from pathlib import Path
from typing import Optional
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'python-dotenv'])
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)


class Settings:
    """Application settings with environment variable support."""
    
    def __init__(self):
        # Application
        self.APP_NAME: str = "Restaurant Recommendation API"
        self.APP_VERSION: str = "1.0.0"
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
        
        # API Configuration
        self.API_V1_PREFIX: str = "/api/v1"
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))
        
        # Security
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.API_KEY: Optional[str] = os.getenv("API_KEY")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        
        # Rate Limiting
        self.RATE_LIMIT_PER_MIN: int = int(os.getenv("RATE_LIMIT_PER_MIN", "120"))
        
        # Caching
        self.CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "120"))
        self.CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "1000"))
        
        # LLM Configuration (Groq)
        self.GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
        self.GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.GROQ_TIMEOUT_SECONDS: float = float(os.getenv("GROQ_TIMEOUT_SECONDS", "8.0"))
        self.GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "1000"))
        
        # Database Configuration
        self.DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
        
        # File Paths
        self.BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
        self.STORAGE_DIR: Path = self.BASE_DIR / "storage"
        self.RAW_DIR: Path = self.STORAGE_DIR / "raw"
        self.PREPARED_DIR: Path = self.STORAGE_DIR / "prepared"
        self.PROFILES_DIR: Path = self.STORAGE_DIR / "profiles"
        self.FEEDBACK_DIR: Path = self.STORAGE_DIR / "feedback"
        self.EXPERIMENTS_DIR: Path = self.STORAGE_DIR / "experiments"
        
        # Data Files
        self.RAW_DATA_FILE: Path = self.RAW_DIR / "restaurants.csv"
        self.PREPARED_DATA_FILE: Path = self.PREPARED_DIR / "restaurants.parquet"
        self.FEEDBACK_LOG_FILE: Path = self.FEEDBACK_DIR / "events.jsonl"
        self.EXPERIMENT_ASSIGNMENTS_FILE: Path = self.EXPERIMENTS_DIR / "assignments.json"
        
        # Dataset Configuration
        self.HF_DATASET_ID: str = "ManikaSaini/zomato-restaurant-recommendation"
        self.PROMPT_VERSION: str = "v1-groq-backend"
        
        # Monitoring
        self.METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        
        # Recommendation Settings
        self.DEFAULT_TOP_N: int = int(os.getenv("DEFAULT_TOP_N", "5"))
        self.MAX_CANDIDATES_FOR_LLM: int = int(os.getenv("MAX_CANDIDATES_FOR_LLM", "20"))


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
