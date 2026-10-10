from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b-instruct"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    OPENAI_COMPAT_BASE_URL: str = ""
    OPENAI_COMPAT_API_KEY: str = ""
    OPENAI_COMPAT_MODEL: str = ""
    DATABASE_URL: str = "postgresql+asyncpg://lenny:lenny@localhost:5432/lenny_db"
    POSTGRES_USER: str = "lenny"
    POSTGRES_PASSWORD: str = "lenny"
    POSTGRES_DB: str = "lenny_db"
    RETRIEVAL_TOP_K: int = 6
    RETRIEVAL_MIN_SCORE: float = 0.30
    LLM_TIMEOUT_SECONDS: int = 120
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

