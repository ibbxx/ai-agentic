from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    DATABASE_URL: str = ""
    TIMEZONE: str = "Asia/Makassar"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
        extra = "ignore" # Allow extra fields in .env

@lru_cache()
def get_settings():
    return Settings()
