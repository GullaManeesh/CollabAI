from dataclasses import dataclass
from datetime import datetime
from bson import ObjectId
from typing import List, Optional
import math
import logging

import backend.database as db
from backend.config import settings
from backend.rag.embeddings import embed_query

logger = logging.getLogger(__name__)

@dataclass
class RetrievedChunk:
    text: str
    score: float
    source_type: str
    filename: Optional[str]
    page: Optional[int]
    sender_name: Optional[str]
    document_id: Optional[str]
    message_id: Optional[str]
    created_at: datetime

async def _retrieve_from_stored_vectors(
    workspace_id: ObjectId,
    query_embedding: List[float],
    k: int,
    source_types: List[str],
) -> List[RetrievedChunk]:
    """Rank this workspace's stored vectors when Atlas returns no candidates."""
    cursor = db.chunks_col.find({
        "workspace_id": workspace_id,
        "source_type": {"$in": list(source_types)},
    })
    documents = await cursor.to_list(length=1000)
    query_norm = math.sqrt(sum(value * value for value in query_embedding))
    if not query_norm:
        return []

    ranked = []
    for document in documents:
        vector = document.get("embedding") or []
        if len(vector) != len(query_embedding):
            continue
        vector_norm = math.sqrt(sum(value * value for value in vector))
        if not vector_norm:
            continue
        score = sum(left * right for left, right in zip(query_embedding, vector)) / (query_norm * vector_norm)
        ranked.append((score, document))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return [
        RetrievedChunk(
            text=document.get("text", ""),
            score=score,
            source_type=document.get("source_type", "document"),
            filename=document.get("filename"),
            page=document.get("page"),
            sender_name=document.get("sender_name"),
            document_id=str(document.get("document_id")) if document.get("document_id") else None,
            message_id=str(document.get("message_id")) if document.get("message_id") else None,
            created_at=document.get("created_at", datetime.utcnow()),
        )
        for score, document in ranked[:k]
    ]

async def retrieve(
    workspace_id: ObjectId,
    query: str,
    k: int = 6,
    source_types: List[str] = ("document", "message", "plan"),
) -> List[RetrievedChunk]:
    """
    Executes a vector search query against the MongoDB Atlas vector index 'chunks_vec_index'.
    Enforces workspace isolation using the workspace_id query filter.
    """
    # 1. Generate query embedding (using asymmetric query_embed)
    query_embedding = embed_query(query)
    
    # 2. Build MongoDB Atlas vector search aggregation pipeline
    # Note: filter parameters must match BSON types (ObjectId, str).
    pipeline = [
        {
            "$vectorSearch": {
                "index": settings.VECTOR_INDEX_NAME,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": k * 15,
                "limit": k,
                "filter": {
                    "workspace_id": {"$eq": workspace_id},
                    "source_type": {"$in": list(source_types)}
                }
            }
        },
        {
            "$project": {
                "text": 1,
                "source_type": 1,
                "filename": 1,
                "page": 1,
                "document_id": 1,
                "message_id": 1,
                "sender_name": 1,
                "created_at": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    
    logger.info(f"Issuing $vectorSearch for workspace {workspace_id} with query '{query}'")
    
    try:
        cursor = db.chunks_col.aggregate(pipeline)
        results = await cursor.to_list(length=k)
    except Exception as e:
        logger.error(f"Error during Atlas Vector Search aggregation: {e}")
        
        # Check if the error is due to missing filter index configurations in Atlas
        if "indexed as filter" in str(e):
            logger.warning("Atlas Index is missing filter fields. Re-running with post-search filtering fallback...")
            try:
                fallback_pipeline = [
                    {
                        "$vectorSearch": {
                            "index": settings.VECTOR_INDEX_NAME,
                            "path": "embedding",
                            "queryVector": query_embedding,
                            "numCandidates": k * 15,
                            "limit": k * 5
                        }
                    },
                    {
                        "$match": {
                            "workspace_id": workspace_id,
                            "source_type": {"$in": list(source_types)}
                        }
                    },
                    {
                        "$limit": k
                    },
                    {
                        "$project": {
                            "text": 1,
                            "source_type": 1,
                            "filename": 1,
                            "page": 1,
                            "document_id": 1,
                            "message_id": 1,
                            "sender_name": 1,
                            "created_at": 1,
                            "score": {"$meta": "vectorSearchScore"}
                        }
                    }
                ]
                cursor = db.chunks_col.aggregate(fallback_pipeline)
                results = await cursor.to_list(length=k)
                return [
                    RetrievedChunk(
                        text=doc.get("text", ""),
                        score=doc.get("score", 0.0),
                        source_type=doc.get("source_type", "document"),
                        filename=doc.get("filename"),
                        page=doc.get("page"),
                        sender_name=doc.get("sender_name"),
                        document_id=str(doc.get("document_id")) if doc.get("document_id") else None,
                        message_id=str(doc.get("message_id")) if doc.get("message_id") else None,
                        created_at=doc.get("created_at", datetime.utcnow())
                    )
                    for doc in results
                ]
            except Exception as fallback_err:
                logger.error(f"Fallback retrieval failed: {fallback_err}")
                return []
                
        if "vectorSearch" in str(e):
            logger.warning("Atlas Vector Search is not supported on this cluster (perhaps local MongoDB is used). Returning empty results.")
        return await _retrieve_from_stored_vectors(workspace_id, query_embedding, k, source_types)

    if not results:
        logger.warning("Atlas Vector Search returned no candidates; using stored-vector fallback")
        return await _retrieve_from_stored_vectors(workspace_id, query_embedding, k, source_types)
        
    retrieved_chunks = []
    for doc in results:
        retrieved_chunks.append(
            RetrievedChunk(
                text=doc.get("text", ""),
                score=doc.get("score", 0.0),
                source_type=doc.get("source_type", "document"),
                filename=doc.get("filename"),
                page=doc.get("page"),
                sender_name=doc.get("sender_name"),
                document_id=str(doc.get("document_id")) if doc.get("document_id") else None,
                message_id=str(doc.get("message_id")) if doc.get("message_id") else None,
                created_at=doc.get("created_at", datetime.utcnow())
            )
        )
        
    return retrieved_chunks

def format_context(chunks: List[RetrievedChunk]) -> str:
    """
    Formats chunks into a structured string context for injection into LLM prompts.
    """
    if not chunks:
        return "No relevant material found in this workspace."
        
    parts = []
    for i, c in enumerate(chunks, 1):
        if c.source_type == "document":
            src = f"{c.filename}, page {c.page}"
        elif c.source_type == "message":
            src = f"team chat, {c.created_at.strftime('%d %b')}"
        else:
            src = "previous plan"
        parts.append(f"[{i}] ({src})\n{c.text}")
    return "\n\n".join(parts)
