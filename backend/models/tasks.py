from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = ""
    priority: str = Field(default="medium")  # "high" | "medium" | "low"
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # "todo" | "in_progress" | "done"
    priority: Optional[str] = None
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    description: str
    status: str
    priority: str
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    due_date: Optional[datetime] = None
    created_by: str
    run_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
