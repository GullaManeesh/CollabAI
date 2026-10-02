from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from bson.errors import InvalidId
from typing import List

from backend.models.search import SearchRequest, SearchResponse, SearchChunkResponse
from backend.dependencies import require_member
from backend.services.retrieval_service import retrieve

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/{workspace_id}", response_model=SearchResponse)
async def search_workspace_memory(
    workspace_id: str,
    req: SearchRequest,
    workspace: dict = Depends(require_member)
):
    try:
        ws_oid = ObjectId(workspace_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workspace ID"
        )
        
    # Retrieve chunks
    chunks = await retrieve(workspace_id=ws_oid, query=req.query, k=req.k)
    
    formatted_chunks = []
    for chunk in chunks:
        formatted_chunks.append(
            SearchChunkResponse(
                text=chunk.text,
                score=chunk.score,
                source_type=chunk.source_type,
                filename=chunk.filename,
                page=chunk.page,
                sender_name=chunk.sender_name,
                created_at=chunk.created_at
            )
        )
        
    return SearchResponse(chunks=formatted_chunks)
