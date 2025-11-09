from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./app.db"
    COHERE_API_KEY: str | None = None
    KB_DIR: str = "./kb"
    # Preprocessamento do texto de transcrição: 'off' | 'basic' | 'llm'
    STT_PREPROCESS_MODE: str = "llm"

    # Modelo KittenTTS (ex: "KittenML/kitten-tts-nano-0.2")
    KITTEN_TTS_MODEL: str = "KittenML/kitten-tts-nano-0.2"
    # Voz padrão do KittenTTS (ex: 'expr-voice-2-f' do seu exemplo)
    KITTEN_TTS_VOICE_ID: str = "expr-voice-2-f"
    # Sample rate que o KittenTTS produz (do seu exemplo)
    KITTEN_TTS_SAMPLE_RATE: int = 24000
    # ----------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
    )

settings = Settings()