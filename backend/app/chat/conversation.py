"""Conversation state management for chatbot."""
import uuid
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from ..models.schemas import (
    ConversationSession,
    ConversationState,
    ResourceType,
    ChatMessage
)


class ConversationManager:
    """Manages conversation sessions and state."""
    
    def __init__(self):
        """Initialize conversation manager."""
        self.sessions: Dict[str, ConversationSession] = {}
        self.session_timeout = timedelta(hours=1)
    
    def create_session(self) -> str:
        """Create a new conversation session."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = ConversationSession(
            session_id=session_id,
            state=ConversationState.INITIAL,
            messages=[]
        )
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get an existing session or None if not found."""
        return self.sessions.get(session_id)
    
    def get_or_create_session(self, session_id: str) -> ConversationSession:
        """Get existing session or create new one."""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationSession(
                session_id=session_id,
                state=ConversationState.INITIAL,
                messages=[]
            )
        return self.sessions[session_id]
    
    def update_session(
        self,
        session_id: str,
        **kwargs
    ) -> ConversationSession:
        """Update session attributes."""
        session = self.get_or_create_session(session_id)
        
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        return session
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a message to the session history."""
        session = self.get_or_create_session(session_id)
        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata
        )
        session.messages.append(message)
    
    def set_state(
        self,
        session_id: str,
        state: ConversationState
    ) -> None:
        """Set the conversation state."""
        session = self.get_or_create_session(session_id)
        session.state = state
    
    def set_resource_type(
        self,
        session_id: str,
        resource_type: ResourceType
    ) -> None:
        """Set the selected resource type."""
        session = self.get_or_create_session(session_id)
        session.resource_type = resource_type
    
    def set_subscription(
        self,
        session_id: str,
        subscription_id: str
    ) -> None:
        """Set the subscription ID."""
        session = self.get_or_create_session(session_id)
        session.subscription_id = subscription_id
    
    def set_resource_group(
        self,
        session_id: str,
        resource_group: str,
        create_new: bool = False
    ) -> None:
        """Set the resource group."""
        session = self.get_or_create_session(session_id)
        session.resource_group = resource_group
        session.create_new_rg = create_new
    
    def set_region(
        self,
        session_id: str,
        region: str
    ) -> None:
        """Set the Azure region."""
        session = self.get_or_create_session(session_id)
        session.region = region
    
    def update_config(
        self,
        session_id: str,
        key: str,
        value: Any
    ) -> None:
        """Update a configuration parameter."""
        session = self.get_or_create_session(session_id)
        session.config[key] = value
    
    def set_config(
        self,
        session_id: str,
        config: Dict[str, Any]
    ) -> None:
        """Set the entire configuration."""
        session = self.get_or_create_session(session_id)
        session.config = config
    
    def set_execution_method(
        self,
        session_id: str,
        method: str
    ) -> None:
        """Set the execution method (azure_sdk or terraform)."""
        session = self.get_or_create_session(session_id)
        session.execution_method = method
    
    def get_resource_summary(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """Get a summary of the configured resource."""
        session = self.get_or_create_session(session_id)
        
        return {
            "resource_type": session.resource_type.value if session.resource_type else None,
            "subscription_id": session.subscription_id,
            "resource_group": session.resource_group,
            "create_new_rg": session.create_new_rg,
            "region": session.region,
            "configuration": session.config
        }
    
    def reset_session(self, session_id: str) -> ConversationSession:
        """Reset a session to initial state."""
        self.sessions[session_id] = ConversationSession(
            session_id=session_id,
            state=ConversationState.INITIAL,
            messages=[]
        )
        return self.sessions[session_id]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions. Returns count of removed sessions."""
        # In a production system, you'd track last activity time
        # For now, this is a placeholder
        return 0


# Global conversation manager instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> ConversationManager:
    """Get the global conversation manager instance."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager

