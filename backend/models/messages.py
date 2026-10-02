from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class Citation(BaseModel):
    source_type: str  # "document" | "message" | "plan"
    document_id: Optional[str] = None
    filename: Optional[str] = None
    page: Optional[int] = None
    snippet: Optional[str] = None

    @field_validator("document_id", mode="before")
    @classmethod
    def convert_object_id(cls, v):
        if v is not None and not isinstance(v, str):
            return str(v)
        return v

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)

class MessageResponse(BaseModel):
    id: str
    workspace_id: str
    channel_id: str
    sender_type: str  # "user" | "agent"
    sender_id: str
    sender_name: str
    content: str
    citations: List[Citation] = []
    run_id: Optional[str] = None
    mentioned_agents: List[str] = []
    indexed: bool = False
    created_at: datetime

class MessagesListResponse(BaseModel):
    messages: List[MessageResponse]
    has_more: bool
