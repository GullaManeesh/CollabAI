from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime

class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default="")

class WorkspaceMemberResponse(BaseModel):
    user_id: str
    name: str
    role: str
    joined_at: datetime
    avatar_color: Optional[str] = None

class WorkspaceChannels(BaseModel):
    team_chat: str
    copilot: str

class WorkspaceStats(BaseModel):
    message_count: int
    document_count: int
    task_count: int
    indexed_chunks: int

class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: str
    owner_id: str
    members: List[WorkspaceMemberResponse]
    channels: WorkspaceChannels
    created_at: datetime

class WorkspaceDetailResponse(BaseModel):
    id: str
    name: str
    description: str
    owner_id: str
    members: List[WorkspaceMemberResponse]
    channels: WorkspaceChannels
    stats: WorkspaceStats
    created_at: datetime

class WorkspaceListResponse(BaseModel):
    id: str
    name: str
    member_count: int
    role: str
    last_activity_at: datetime

class AddMemberRequest(BaseModel):
    email: EmailStr

class WorkspaceMembersListResponse(BaseModel):
    members: List[WorkspaceMemberResponse]
