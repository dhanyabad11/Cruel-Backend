from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    """Supabase User Model - Production Ready 🚀"""
    id: Optional[int] = None
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    notification_preferences: Optional[str] = None
    created_at: Optional[datetime] = None
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash password for secure storage"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)