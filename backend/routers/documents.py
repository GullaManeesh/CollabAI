from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
import os
import uuid
import logging

from backend.models.documents import DocumentResponse, DocumentDetailResponse
from backend.dependencies import require_member, get_current_user
from backend.config import settings
import backend.database as db
from backend.services.ingest_service import ingest_document_background

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}

@router.post("/{workspace_id}", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    workspace_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    workspace: dict = Depends(require_member)
):
    # 1. Validate file extension
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
        
    # 2. Validate file size
    max_size_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    content = await file.read()
    file_size = len(content)
    await file.seek(0)  # Reset pointer
    
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_MB} MB"
        )
        
    # 3. Create target directory
    ws_dir = os.path.join(settings.STORAGE_PATH, workspace_id)
    os.makedirs(ws_dir, exist_ok=True)
    
    # Save file on disk with a UUID prefix
    file_uuid = str(uuid.uuid4())
    safe_filename = f"{file_uuid}_{filename}"
    file_path = os.path.join(ws_dir, safe_filename)
    
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to write file to storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file to local disk storage"
        )
        
    # 4. Insert document record
    now = datetime.utcnow()
    doc_doc = {
        "workspace_id": ObjectId(workspace_id),
        "filename": filename,
        "stored_path": file_path,
        "mime_type": file.content_type or "application/octet-stream",
        "size_bytes": file_size,
        "uploaded_by": ObjectId(current_user["id"]),
        "uploader_name": current_user["name"],
        "status": "processing",
        "error": None,
        "chunk_count": 0,
        "page_count": 0,
        "summary": None,
        "created_at": now
    }
    
    res = await db.documents_col.insert_one(doc_doc)
    doc_id = res.inserted_id
    
    # 5. Trigger background parser/embedder
    background_tasks.add_task(
        ingest_document_background,
        workspace_id=workspace_id,
        document_id=str(doc_id),
        file_path=file_path,
        mime_type=file.content_type
    )
    
    return DocumentResponse(
        id=str(doc_id),
        workspace_id=workspace_id,
        filename=filename,
        size_bytes=file_size,
        uploader_name=current_user["name"],
        status="processing",
        error=None,
        chunk_count=0,
        page_count=0,
        created_at=now
    )

@router.get("/{workspace_id}", response_model=list[DocumentResponse])
async def list_documents(
    workspace_id: str,
    workspace: dict = Depends(require_member)
):
    ws_oid = ObjectId(workspace_id)
    cursor = db.documents_col.find({"workspace_id": ws_oid}).sort([("created_at", -1)])
    docs = await cursor.to_list(length=100)
    
    result = []
    for doc in docs:
        result.append(
            DocumentResponse(
                id=str(doc["_id"]),
                workspace_id=workspace_id,
                filename=doc["filename"],
                size_bytes=doc["size_bytes"],
                uploader_name=doc.get("uploader_name", "Unknown"),
                status=doc["status"],
                error=doc.get("error"),
                chunk_count=doc.get("chunk_count", 0),
                page_count=doc.get("page_count", 0),
                created_at=doc["created_at"]
            )
        )
    return result

@router.get("/{workspace_id}/{document_id}", response_model=DocumentDetailResponse)
async def get_document_details(
    workspace_id: str,
    document_id: str,
    workspace: dict = Depends(require_member)
):
    try:
        doc_oid = ObjectId(document_id)
        ws_oid = ObjectId(workspace_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document or workspace ID"
        )
        
    doc = await db.documents_col.find_one({"_id": doc_oid, "workspace_id": ws_oid})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found in workspace"
        )
        
    summary = doc.get("summary")
    
    return DocumentDetailResponse(
        id=str(doc["_id"]),
        workspace_id=workspace_id,
        filename=doc["filename"],
        size_bytes=doc["size_bytes"],
        uploader_name=doc.get("uploader_name", "Unknown"),
        status=doc["status"],
        error=doc.get("error"),
        chunk_count=doc.get("chunk_count", 0),
        page_count=doc.get("page_count", 0),
        summary=summary,
        created_at=doc["created_at"]
    )

@router.delete("/{workspace_id}/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    workspace_id: str,
    document_id: str,
    workspace: dict = Depends(require_member)
):
    try:
        doc_oid = ObjectId(document_id)
        ws_oid = ObjectId(workspace_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid IDs"
        )
        
    doc = await db.documents_col.find_one({"_id": doc_oid, "workspace_id": ws_oid})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
        
    # 1. Delete chunks first
    await db.chunks_col.delete_many({"document_id": doc_oid})
    
    # 2. Delete file on disk
    stored_path = doc.get("stored_path")
    if stored_path and os.path.exists(stored_path):
        try:
            os.remove(stored_path)
        except Exception as e:
            logger.error(f"Failed to delete document file {stored_path}: {e}")
            
    # 3. Delete document database record
    await db.documents_col.delete_one({"_id": doc_oid})
    
    return status.HTTP_204_NO_CONTENT
