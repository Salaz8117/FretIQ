"""
FretIQ App - Configuration Module
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # AI Provider API Keys
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    nvidia_api_key: Optional[str] = Field(default=None, alias="NVIDIA_API_KEY")
    grok_api_key: Optional[str] = Field(default=None, alias="GROK_API_KEY")
    kimi_api_key: Optional[str] = Field(default=None, alias="KIMI_API_KEY")
    
    # Local AI Gateway
    free_llmapi_url: Optional[str] = Field(default=None, alias="FREE_LLMAPI_URL")
    free_llmapi_key: Optional[str] = Field(default=None, alias="FREE_LLMAPI_KEY")
    
    # Search API Keys
    serpapi_key: Optional[str] = Field(default=None, alias="SERPAPI_KEY")
    bing_api_key: Optional[str] = Field(default=None, alias="BING_API_KEY")
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    
    # Cloud/Other APIs
    cloudflare_api_token: Optional[str] = Field(default=None, alias="CLOUDFLARE_API_TOKEN")
    cloudflare_account_id: Optional[str] = Field(default=None, alias="CLOUDFLARE_ACCOUNT_ID")
    modelscope_api_key: Optional[str] = Field(default=None, alias="MODELSCOPE_API_KEY")
    ollama_cloud_key: Optional[str] = Field(default=None, alias="OLLAMA_CLOUD_KEY")
    
    # App Settings
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Cache Settings
    cache_ttl: int = Field(default=3600, alias="CACHE_TTL")
    max_cache_size: int = Field(default=1000, alias="MAX_CACHE_SIZE")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=30, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, alias="RATE_LIMIT_WINDOW")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Available instruments
INSTRUMENTS = [
    "guitar",
    "ukulele",
    "piano",
    "banjo",
    "mandolin",
    "bass",
    "violin",
    "cello",
]

# Instrument-specific chord/note formats
INSTRUMENT_FORMATS = {
    "guitar": ["chords", "tabs", "strumming", "fingerpicking"],
    "ukulele": ["chords", "tabs", "strumming"],
    "piano": ["chords", "notes", "sheet_music"],
    "banjo": ["chords", "tabs", "rolls"],
    "mandolin": ["chords", "tabs"],
    "bass": ["tabs", "notes"],
    "violin": ["notes", "sheet_music"],
    "cello": ["notes", "sheet_music"],
}

# Difficulty levels
DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"]