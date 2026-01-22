"""User storage and management."""
import json
import os
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path

from .models import UserInDB, UserCreate, UserUpdate, UserRole, UserResponse
from .security import hash_password, verify_password


class UserStore:
    """Simple file-based user storage. Replace with database in production."""
    
    def __init__(self, storage_path: str = None):
        """Initialize user store."""
        if storage_path is None:
            storage_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'data', 'users.json'
            )
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.users: Dict[str, UserInDB] = {}
        self._load()
        self._ensure_admin()
    
    def _load(self):
        """Load users from file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for user_data in data:
                        user = UserInDB(**user_data)
                        self.users[user.id] = user
            except Exception as e:
                print(f"Error loading users: {e}")
                self.users = {}
    
    def _save(self):
        """Save users to file."""
        try:
            data = [user.model_dump(mode='json') for user in self.users.values()]
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def _ensure_admin(self):
        """Ensure default admin user exists."""
        admin_exists = any(
            user.role == UserRole.ADMIN and user.username == "admin"
            for user in self.users.values()
        )
        
        if not admin_exists:
            admin_password = os.getenv("ADMIN_PASSWORD", "Admin@123456")
            admin_user = UserInDB(
                email="admin@azure-chatbot.local",
                username="admin",
                full_name="System Administrator",
                role=UserRole.ADMIN,
                hashed_password=hash_password(admin_password),
                is_active=True
            )
            self.users[admin_user.id] = admin_user
            self._save()
            print(f"Created default admin user: admin / {admin_password}")
    
    def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def get_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username."""
        for user in self.users.values():
            if user.username.lower() == username.lower():
                return user
        return None
    
    def get_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email."""
        for user in self.users.values():
            if user.email.lower() == email.lower():
                return user
        return None
    
    def get_all(self) -> List[UserInDB]:
        """Get all users."""
        return list(self.users.values())
    
    def create(self, user_create: UserCreate) -> UserInDB:
        """Create a new user."""
        # Check if username or email exists
        if self.get_by_username(user_create.username):
            raise ValueError("Username already exists")
        if self.get_by_email(user_create.email):
            raise ValueError("Email already exists")
        
        user = UserInDB(
            email=user_create.email,
            username=user_create.username,
            full_name=user_create.full_name,
            role=user_create.role,
            hashed_password=hash_password(user_create.password),
            is_active=True
        )
        
        self.users[user.id] = user
        self._save()
        return user
    
    def update(self, user_id: str, user_update: UserUpdate) -> Optional[UserInDB]:
        """Update a user."""
        user = self.users.get(user_id)
        if not user:
            return None
        
        update_data = user_update.model_dump(exclude_unset=True)
        
        # Check for duplicate username/email
        if 'username' in update_data and update_data['username']:
            existing = self.get_by_username(update_data['username'])
            if existing and existing.id != user_id:
                raise ValueError("Username already exists")
        
        if 'email' in update_data and update_data['email']:
            existing = self.get_by_email(update_data['email'])
            if existing and existing.id != user_id:
                raise ValueError("Email already exists")
        
        # Hash password if provided
        if 'password' in update_data and update_data['password']:
            update_data['hashed_password'] = hash_password(update_data['password'])
            del update_data['password']
        
        # Update user
        for field, value in update_data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        self._save()
        return user
    
    def delete(self, user_id: str) -> bool:
        """Delete a user."""
        if user_id in self.users:
            # Prevent deleting the last admin
            user = self.users[user_id]
            if user.role == UserRole.ADMIN:
                admin_count = sum(1 for u in self.users.values() if u.role == UserRole.ADMIN)
                if admin_count <= 1:
                    raise ValueError("Cannot delete the last admin user")
            
            del self.users[user_id]
            self._save()
            return True
        return False
    
    def authenticate(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user."""
        user = self.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user
    
    def update_last_login(self, user_id: str):
        """Update user's last login time."""
        if user_id in self.users:
            self.users[user_id].last_login = datetime.utcnow()
            self._save()
    
    def to_response(self, user: UserInDB) -> UserResponse:
        """Convert UserInDB to UserResponse (without password)."""
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            role=user.role,
            created_at=user.created_at,
            last_login=user.last_login
        )


# Global user store instance
_user_store: Optional[UserStore] = None


def get_user_store() -> UserStore:
    """Get the global user store instance."""
    global _user_store
    if _user_store is None:
        _user_store = UserStore()
    return _user_store

