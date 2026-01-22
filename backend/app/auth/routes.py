"""Authentication and user management routes."""
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from .models import (
    UserCreate, UserUpdate, UserResponse, UserRole,
    Token, LoginRequest, ChangePasswordRequest
)
from .security import (
    create_access_token, get_current_user, get_admin_user,
    verify_password, hash_password, ACCESS_TOKEN_EXPIRE_MINUTES, TokenData
)
from .user_store import get_user_store

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    user_store = get_user_store()
    
    user = user_store.authenticate(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user_store.update_last_login(user.id)
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "role": user.role.value
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_store.to_response(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """Get current authenticated user info."""
    user_store = get_user_store()
    user = user_store.get_by_id(current_user.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user_store.to_response(user)


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Change current user's password."""
    user_store = get_user_store()
    user = user_store.get_by_id(current_user.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(request.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    user_store.update(user.id, UserUpdate(password=request.new_password))
    
    return {"message": "Password changed successfully"}


# Admin-only routes
@router.get("/users", response_model=List[UserResponse])
async def list_users(admin: TokenData = Depends(get_admin_user)):
    """List all users (admin only)."""
    user_store = get_user_store()
    users = user_store.get_all()
    return [user_store.to_response(user) for user in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    admin: TokenData = Depends(get_admin_user)
):
    """Create a new user (admin only)."""
    user_store = get_user_store()
    
    try:
        user = user_store.create(user_create)
        return user_store.to_response(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, admin: TokenData = Depends(get_admin_user)):
    """Get a specific user (admin only)."""
    user_store = get_user_store()
    user = user_store.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user_store.to_response(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    admin: TokenData = Depends(get_admin_user)
):
    """Update a user (admin only)."""
    user_store = get_user_store()
    
    try:
        user = user_store.update(user_id, user_update)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user_store.to_response(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: TokenData = Depends(get_admin_user)):
    """Delete a user (admin only)."""
    user_store = get_user_store()
    
    # Prevent self-deletion
    if user_id == admin.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    try:
        if not user_store.delete(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: str,
    admin: TokenData = Depends(get_admin_user)
):
    """Reset a user's password (admin only). Returns new temporary password."""
    user_store = get_user_store()
    user = user_store.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Generate temporary password
    import secrets
    temp_password = secrets.token_urlsafe(12)
    
    user_store.update(user_id, UserUpdate(password=temp_password))
    
    return {
        "message": "Password reset successfully",
        "temporary_password": temp_password,
        "note": "User should change this password after login"
    }

