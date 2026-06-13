from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_project_root(
    starting_path: Path = Path.cwd(),
    markers: tuple = (".env", ".git", "requirements.txt"),
) -> Path:
    current_path = starting_path.resolve()
    for parent in [current_path] + list(current_path.parents):
        for marker in markers:
            if (parent / marker).exists():
                return parent
    return current_path


class Settings(BaseSettings):
    ENV: str = "dev"

    FASTAPI_PROJECT_NAME: str = "default"
    FASTAPI_PROJECT_VERSION: str = "1.0.0"
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000
    FASTAPI_DEBUG_MODE: bool = True
    FASTAPI_WORKERS: int = 1
    FASTAPI_CORS_ORIGINS: Optional[list[str]] = None

    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = True
    LOG_FILE_PATH: Path = Path("logs")
    LOG_MAX_SIZE_MB: int = 20
    LOG_BACKUP_COUNT: int = 5

    RETRY_MAX_ATTEMPTS: int = 5
    RETRY_WAIT_TIME: int = 2

    NEO4J_CONNECTOR_URI: Optional[str] = "bolt://localhost:7687"
    NEO4J_CONNECTOR_AUTH_USER: Optional[str] = None
    NEO4J_CONNECTOR_AUTH_PASSWORD: Optional[str] = None

    FAISS_DIMENSION: Optional[int] = 1024
    FAISS_INDEX_TYPE: Optional[str] = "flat"
    FAISS_PARAM_IVF_NLIST: Optional[int] = 100
    FAISS_PARAM_HNSW_M: Optional[int] = 32

    QWEN_API_KEY: Optional[str] = None
    QWEN_API_URL: Optional[str] = None
    QWEN_TEXT_API_KEY: Optional[str] = None
    QWEN_TEXT_API_URL: Optional[str] = None
    QWEN_EMBEDDING_API_KEY: Optional[str] = None
    QWEN_EMBEDDING_API_URL: Optional[str] = None
    OPENAI_API_URL: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ZHIPU_API_KEY: Optional[str] = None
    ZHIPU_API_URL: Optional[str] = None

    ROOT_PATH: Path = Field(default_factory=find_project_root)
    SEED: int = 42

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field
    @property
    def CONFIG_PATH(self) -> Path:
        return self.ROOT_PATH / "config"


@lru_cache
def get_settings() -> Settings:
    return Settings()
