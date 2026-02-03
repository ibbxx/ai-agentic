"""
Supabase Client - REST API connection to Supabase.
"""
from supabase import create_client, Client
from core.config import get_settings
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

@lru_cache()
def get_supabase() -> Client:
    """Get Supabase client singleton."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def init_tables():
    """Initialize tables in Supabase if they don't exist.
    NOTE: Run this SQL in Supabase SQL Editor first."""
    logger.info("Tables should be created via Supabase SQL Editor")
    pass
