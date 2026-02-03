from pydantic_settings import BaseSettings
from functools import lru_cache
import os

def find_env_file():
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        env_path = os.path.join(current, '.env')
        if os.path.exists(env_path):
            return env_path
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return '.env'

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    TIMEZONE: str = "Asia/Makassar"
    # Groq (free, fast)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-70b-versatile"

    class Config:
        env_file = find_env_file()
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()
