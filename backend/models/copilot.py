from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from backend.models.messages import Citation

class CopilotTurnRequest(BaseModel):
    content: str = Field(..., min_length=1)

class CopilotTurnResponse(BaseModel):
    run_id: str
    message_id: str

class TraceStepResponse(BaseModel):
    step: int
    agent: str
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    tokens_in: Optional[int] = 0
    tokens_out: Optional[int] = 0
    latency_ms: Optional[int] = 0
    started_at: datetime

class CopilotRunResponse(BaseModel):
    id: str
    workspace_id: str
    channel_id: str
    user_id: str
    query: str
    intent: Optional[str] = None
    status: str  # "running" | "done" | "failed"
    final_answer: Optional[str] = None
    citations: List[Citation] = []
    trace: List[TraceStepResponse] = []
    total_tokens: int = 0
    total_latency_ms: int = 0
    revision_count: int = 0
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
