from supabase import create_client, Client
from typing import Optional
import os
from app.config import settings

class SupabaseConfig:
    def __init__(self):
        self.url: str = settings.SUPABASE_URL
        self.key: str = settings.SUPABASE_ANON_KEY
        self.service_key: str = settings.SUPABASE_SERVICE_KEY
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and ANON_KEY must be set in environment variables")
        
        self.client: Client = create_client(self.url, self.key)
        
        # Service client for admin operations
        if self.service_key:
            self.service_client: Client = create_client(self.url, self.service_key)
        else:
            self.service_client = None
    
    def get_client(self) -> Client:
        """Get the regular Supabase client"""
        return self.client
    
    def get_service_client(self) -> Optional[Client]:
        """Get the service client for admin operations"""
        return self.service_client

# Global Supabase instance
supabase_config = None

def get_supabase() -> Client:
    """Get Supabase client instance"""
    global supabase_config
    if supabase_config is None:
        supabase_config = SupabaseConfig()
    return supabase_config.get_client()

def get_supabase_admin() -> Optional[Client]:
    """Get Supabase service client for admin operations"""
    global supabase_config
    if supabase_config is None:
        supabase_config = SupabaseConfig()
    return supabase_config.get_service_client()