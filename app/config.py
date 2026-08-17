from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Chatbot"
    app_env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000

    # Primary LLM provider: "groq" | "gemini" | "openrouter"
    llm_provider: str = "groq"
    # Optional: override the default model for the primary provider
    llm_model: str = ""
    # Comma-separated fallback providers tried in order when the primary fails
    llm_fallback_providers: str = ""

    groq_api_key: str = ""
    gemini_api_key: str = ""
    openrouter_api_key: str = ""

    # Gmail accounts used by the email-sending tool (App Passwords)
    gmail_user: str = ""
    gmail_app_password: str = ""
    gmail_user_2: str = ""
    gmail_app_password_2: str = ""

    request_timeout: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
