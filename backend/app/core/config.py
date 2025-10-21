from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./app.db"
    COHERE_API_KEY: str | None = None
    KB_DIR: str = "./kb"
    # Preprocessamento do texto de transcrição: 'off' | 'basic' | 'llm'
    STT_PREPROCESS_MODE: str = "llm"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
    )


settings = Settings()
