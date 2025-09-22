from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
from app.services.auth_service import auth_service
from app.auth_deps import get_current_user

router = APIRouter()

# Pydantic models for request/response
class UserSignUp(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    university: Optional[str] = None

class UserSignIn(BaseModel):
    email: EmailStr
    password: str

class PasswordReset(BaseModel):
    email: EmailStr

class RefreshToken(BaseModel):
    refresh_token: str

class EmailVerification(BaseModel):
    token: str
    type: str = "signup"

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def sign_up(user_data: UserSignUp) -> Dict[str, Any]:
    """
    Register a new user
    """
    metadata = {}
    if user_data.full_name:
        metadata["full_name"] = user_data.full_name
    if user_data.university:
        metadata["university"] = user_data.university
    
    result = await auth_service.sign_up(
        email=user_data.email,
        password=user_data.password,
        metadata=metadata
    )
    
    return result

@router.post("/signin")
async def sign_in(user_data: UserSignIn) -> Dict[str, Any]:
    """
    Authenticate user and return access token
    """
    result = await auth_service.sign_in(
        email=user_data.email,
        password=user_data.password
    )
    
    return result

@router.post("/signout")
async def sign_out(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, str]:
    """
    Sign out current user
    """
    # In Supabase, we don't need to pass the token to sign out
    # The client handles this
    return {"message": "Successfully signed out"}

@router.post("/refresh")
async def refresh_access_token(token_data: RefreshToken) -> Dict[str, Any]:
    """
    Refresh access token using refresh token
    """
    result = await auth_service.refresh_token(token_data.refresh_token)
    return result

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset) -> Dict[str, str]:
    """
    Send password reset email
    """
    result = await auth_service.reset_password(reset_data.email)
    return result

@router.post("/verify-email")
async def verify_email(verification_data: EmailVerification) -> Dict[str, str]:
    """
    Verify email with token
    """
    result = await auth_service.verify_email(
        token=verification_data.token,
        type=verification_data.type
    )
    return result

@router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get current user information
    """
    return {
        "user": current_user,
        "message": "User authenticated successfully"
    }

@router.get("/health")
async def auth_health_check():
    """
    Check if authentication service is working
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "provider": "supabase"
    }