"""Azure Authentication Module."""
from .azure_auth import AzureAuthManager, get_auth_manager
from .models import User, UserRole, UserCreate, UserResponse, Token
from .security import get_current_user, get_admin_user, hash_password, verify_password
from .user_store import UserStore, get_user_store
from .routes import router as auth_router

__all__ = [
    "AzureAuthManager", 
    "get_auth_manager",
    "User",
    "UserRole",
    "UserCreate",
    "UserResponse",
    "Token",
    "get_current_user",
    "get_admin_user",
    "hash_password",
    "verify_password",
    "UserStore",
    "get_user_store",
    "auth_router"
]

