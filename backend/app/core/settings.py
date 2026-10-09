from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b-instruct"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    OPENAI_COMPAT_BASE_URL: str = ""
    OPENAI_COMPAT_API_KEY: str = ""
    OPENAI_COMPAT_MODEL: str = ""
    DATABASE_URL: str
    RETRIEVAL_TOP_K: int = 6
    RETRIEVAL_MIN_SCORE: float = 0.30
    LLM_TIMEOUT_SECONDS: int = 120
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
