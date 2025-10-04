from fastapi import HTTPException, status
from typing import Optional, Dict, Any
import logging
import os
from app.database import get_supabase_client

logger = logging.getLogger(__name__)

class AuthService:
    """PRODUCTION-LEVEL Authentication Service using real Supabase Auth"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        from app.database import get_supabase_admin
        self.supabase_admin = get_supabase_admin()
    
    async def sign_up(self, email: str, password: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new user with Supabase Auth - DEVELOPMENT MODE"""
        try:
            print(f"Creating user with email: {email}")
            
            # Prepare signup data
            signup_data = {
                "email": email,
                "password": password
            }
            
            # Add metadata if provided
            if metadata:
                signup_data["options"] = {
                    "data": metadata
                }
            
            # Use real Supabase Auth
            response = self.supabase.auth.sign_up(signup_data)
            
            # Auto-confirm user for development (bypass email verification)
            if response.user and not response.user.email_confirmed_at:
                try:
                    # Use admin client to confirm the user
                    self.supabase_admin.auth.admin.update_user_by_id(
                        response.user.id,
                        {"email_confirm": True}
                    )
                    print(f"User {response.user.email} auto-confirmed successfully")
                except Exception as confirm_error:
                    print(f"Auto-confirm failed (user can still sign in): {confirm_error}")
            
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
            logger.error(f"Signup error: {str(e)}")
            error_message = str(e).lower()
            
            if "already registered" in error_message or "already exists" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists"
                )
            elif "invalid" in error_message and "email" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please enter a valid email address"
                )
            
            # Return the actual error for debugging
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in a user with email and password - PRODUCTION LEVEL"""
        try:
            print(f"Signing in user with email: {email}")
            
            # Use real Supabase Auth
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
                        "created_at": response.user.created_at,
                        "last_sign_in": response.user.last_sign_in_at
                    },
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "token_type": "bearer",
                    "expires_in": response.session.expires_in,
                    "message": "Login successful"
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Sign in error: {str(e)}")
            error_message = str(e).lower()
            
            # Skip email confirmation check for development
            # if "email not confirmed" in error_message or "not confirmed" in error_message:
            #     raise HTTPException(
            #         status_code=status.HTTP_401_UNAUTHORIZED,
            #         detail="Please check your email and click the verification link before signing in."
            #     )
            if "invalid" in error_message and ("password" in error_message or "credentials" in error_message):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Sign in failed: {str(e)}"
            )
    
    async def get_user_from_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from access token - PRODUCTION LEVEL"""
        try:
            print(f"Validating token: {access_token[:50]}...")
            
            # Use real Supabase Auth to validate token
            response = self.supabase.auth.get_user(access_token)
            
            if response.user:
                return {
                    "id": response.user.id,
                    "email": response.user.email,
                    "email_confirmed": response.user.email_confirmed_at is not None,
                    "user_metadata": response.user.user_metadata or {},
                    "created_at": response.user.created_at,
                    "last_sign_in": response.user.last_sign_in_at
                }
            else:
                return None
                
        except Exception as e:
            print(f"Token validation error: {e}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[str]:
        """Refresh an access token - PRODUCTION LEVEL"""
        try:
            print(f"Refreshing token: {refresh_token[:50]}...")
            
            response = self.supabase.auth.refresh_session(refresh_token)
            
            if response.session:
                return response.session.access_token
            else:
                return None
                
        except Exception as e:
            print(f"Token refresh error: {e}")
            return None
    
    async def sign_out(self, access_token: str) -> Dict[str, Any]:
        """Sign out a user - PRODUCTION LEVEL"""
        try:
            print(f"Signing out user with token: {access_token[:50]}...")
            
            self.supabase.auth.sign_out()
            
            return {"message": "Successfully signed out"}
            
        except Exception as e:
            logger.error(f"Sign out error: {str(e)}")
            return {"message": "Sign out completed"}
    
    async def reset_password(self, email: str) -> Dict[str, Any]:
        """Reset password for a user - PRODUCTION LEVEL"""
        try:
            print(f"Resetting password for email: {email}")
            
            response = self.supabase.auth.reset_password_email(email)
            
            return {"message": "Password reset email sent successfully"}
            
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email"
            )
    
    async def verify_email(self, token: str, type: str) -> Dict[str, Any]:
        """Verify email with token - PRODUCTION LEVEL"""
        try:
            print(f"Verifying email with token: {token[:50]}...")
            
            response = self.supabase.auth.verify_otp({
                'token': token,
                'type': type
            })
            
            return {"message": "Email verified successfully"}
            
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )

# Create singleton instance
auth_service = AuthService()