from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DocumentResponse(BaseModel):
    id: str
    workspace_id: str
    filename: str
    size_bytes: int
    uploader_name: str
    status: str  # "processing" | "indexed" | "failed"
    error: Optional[str] = None
    chunk_count: int
    page_count: int
    created_at: datetime

class DocumentDetailResponse(DocumentResponse):
    summary: Optional[str] = None
