from supabase import create_client, Client
from app.config import settings

# Supabase client - PRODUCTION READY 🚀
supabase: Client = create_client(
    supabase_url=settings.SUPABASE_URL,
    supabase_key=settings.SUPABASE_ANON_KEY
)

# Service role client for admin operations (like user registration)
supabase_admin: Client = create_client(
    supabase_url=settings.SUPABASE_URL,
    supabase_key=settings.SUPABASE_SERVICE_KEY
)

def get_supabase_client() -> Client:
    """Get Supabase client for regular database operations"""
    return supabase

def get_supabase_admin() -> Client:
    """Get Supabase admin client for privileged operations"""
    return supabase_admin