from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    k: int = Field(default=6, ge=1, le=20)

class SearchChunkResponse(BaseModel):
    text: str
    score: float
    source_type: str
    filename: Optional[str] = None
    page: Optional[int] = None
    sender_name: Optional[str] = None
    created_at: datetime

class SearchResponse(BaseModel):
    chunks: List[SearchChunkResponse]
