from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class Message(BaseModel):
    """对话消息"""
    role: str  # user / assistant / system
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class SessionBase(BaseModel):
    title: Optional[str] = None
    meta_data: Dict[str, Any] = Field(default_factory=dict)


class SessionCreate(SessionBase):
    pass


class SessionUpdate(SessionBase):
    messages: Optional[List[Message]] = None


class SessionResponse(SessionBase):
    id: int
    session_id: str
    user_id: int
    messages: List[Message]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
