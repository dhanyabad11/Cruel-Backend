from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from datetime import timedelta
from app.database import get_supabase_client, get_supabase_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.utils.auth import (
    authenticate_user_supabase, 
    create_access_token, 
    get_current_active_user
)
from app.config import settings

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, supabase_admin: Client = Depends(get_supabase_admin)):
    """Register a new user with Supabase (using admin client)"""
    # Check if user already exists (use admin client to bypass RLS)
    existing_user = supabase_admin.table('users').select('*').eq('email', user_data.email).execute()
    if existing_user.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user in Supabase (use admin client to bypass RLS)
    hashed_password = User.get_password_hash(user_data.password)
    user_insert = {
        'email': user_data.email,
        'username': user_data.username,
        'full_name': user_data.full_name,
        'phone': user_data.phone,
        'hashed_password': hashed_password,
        'is_active': True,
        'is_verified': False
    }
    
    result = supabase_admin.table('users').insert(user_insert).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    user = result.data[0]
    return UserResponse(
        id=user['id'],
        email=user['email'],
        username=user['username'],
        full_name=user['full_name'],
        phone=user.get('phone'),
        is_active=user['is_active'],
        is_verified=user['is_verified'],
        created_at=user['created_at']
    )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, supabase_admin: Client = Depends(get_supabase_admin)):
    """Login user and return access token"""
    user = authenticate_user_supabase(supabase_admin, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            phone=user.phone,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at
        )
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        phone=current_user.phone,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_active_user)):
    """Refresh the access token"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(current_user)
    }