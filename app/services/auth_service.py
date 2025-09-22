from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import jwt
from datetime import datetime, timedelta
from app.supabase_client import get_supabase
from app.config import settings

class SupabaseAuthService:
    def __init__(self):
        self.supabase = get_supabase()
    
    async def sign_up(self, email: str, password: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Register a new user with Supabase Auth"""
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": metadata or {}
                }
            })
            
            if response.user:
                return {
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "email_confirmed": response.user.email_confirmed_at is not None,
                        "created_at": response.user.created_at
                    },
                    "session": response.session.access_token if response.session else None,
                    "message": "User created successfully. Please check your email for verification."
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create user"
                )
                
        except Exception as e:
            if "already registered" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {str(e)}"
            )
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user with email and password"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                return {
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "email_confirmed": response.user.email_confirmed_at is not None,
                        "last_sign_in": response.user.last_sign_in_at
                    },
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at,
                    "token_type": "bearer"
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
                
        except Exception as e:
            if "invalid" in str(e).lower() or "wrong" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Login failed: {str(e)}"
            )
    
    async def sign_out(self, access_token: str) -> Dict[str, str]:
        """Sign out user and invalidate session"""
        try:
            # Set the session for the client
            self.supabase.auth.set_session(access_token, "")
            
            # Sign out
            self.supabase.auth.sign_out()
            
            return {"message": "Successfully signed out"}
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sign out failed: {str(e)}"
            )
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            
            if response.session:
                return {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at,
                    "token_type": "bearer"
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token refresh failed: {str(e)}"
            )
    
    async def reset_password(self, email: str) -> Dict[str, str]:
        """Send password reset email"""
        try:
            self.supabase.auth.reset_password_email(email)
            
            return {"message": "Password reset email sent"}
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password reset failed: {str(e)}"
            )
    
    async def get_user_from_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from access token"""
        try:
            # Set the session
            self.supabase.auth.set_session(access_token, "")
            
            # Get user
            user = self.supabase.auth.get_user()
            
            if user.user:
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "email_confirmed": user.user.email_confirmed_at is not None,
                    "user_metadata": user.user.user_metadata,
                    "created_at": user.user.created_at,
                    "last_sign_in": user.user.last_sign_in_at
                }
            else:
                return None
                
        except Exception:
            return None
    
    async def verify_email(self, token: str, type: str = "signup") -> Dict[str, str]:
        """Verify email with verification token"""
        try:
            response = self.supabase.auth.verify_otp({
                "token": token,
                "type": type
            })
            
            if response.user:
                return {"message": "Email verified successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid verification token"
                )
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email verification failed: {str(e)}"
            )

# Global auth service instance
auth_service = SupabaseAuthService()